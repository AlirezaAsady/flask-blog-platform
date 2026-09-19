import os
import logging
from flask import Flask, request, url_for, redirect, render_template, flash, session
from models import (
    get_all_users__db,
    create_user__db,
    login_user__db,
    get_user_by_id__db,
    update_user__db,
    delete_user__db,
    create_profile__db,
    get_profile__db,
    update_profile__db,
)
from dotenv import load_dotenv
from log_setup import get_logger
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")


# ----------------** log **-----------------
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    logger = get_logger("app")
else:
    logger = logging.getLogger("app")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False


# ---------------- auth: access_control ----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("ابتدا وارد شوید", "warning")
            return redirect(url_for("auth_login"))
        return f(*args, **kwargs)

    return decorated_function


# -------------------* HOME *--------------------------
@app.route("/home")
@app.route("/")
def home():
    return render_template("home.html")


# ----------------* USERS *---------------------------
# ---------------- users: database -------------------
@app.route("/users")
def users_list():
    success, message, all_users = get_all_users__db()
    # print(success, message)
    flash(message, "success" if success else "error")
    # logger.info(f"info in users_list(message={message}")
    return render_template("users.html", users=all_users)


# ---------------- auth: registration -----------------
@app.route("/users/register", methods=["GET", "POST"])
def auth_register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        firstname = request.form.get("firstname") or None
        lastname = request.form.get("lastname") or None
        age_raw = request.form.get("age")

        if not username or not password:
            flash("نام کاربری و رمز عبور را وارد کنید", "warning")
            return render_template("register.html")
        elif len(username) < 3 or len(password) < 4:
            flash("نام کاربری یا رمز عبور نامعتبر است", "error")
            return render_template("register.html")

        age = None
        if age_raw:
            try:
                age = int(age_raw)
            except ValueError:
                flash("سن باید عدد باشد", "error")
                return render_template("register.html")

        success, message = create_user__db(username, password, firstname, lastname, age)
        flash(message, "success" if success else "error")
        if success:
            return redirect(url_for("users_list"))
        else:
            return redirect(url_for("auth_register"))

    return render_template("register.html")


# ---------------- auth: database_login ----------------
@app.route("/users/login", methods=["GET", "POST"])
def auth_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("نام کاربری و رمز عبور را وارد کنید", "warning")
            return render_template("userslogin.html")

        success, message, user_id = login_user__db(username, password)

        if success:
            session["user_id"] = user_id
            flash(message, "success")

            return redirect(url_for("edit_account"))
        else:
            flash(message, "error")
            return render_template("userslogin.html")

    return render_template("userslogin.html")


# ---------------- auth: logout -----------------------
@app.route("/users/logout", methods=["POST"])
def auth_logout():
    session.pop("user_id", None)
    flash("exit!", "success")
    return redirect(url_for("users_list"))


# -------------- users: edit account ------------
@app.route("/users/account/edit", methods=["GET", "POST"])
@login_required
def edit_account():
    user_id = session["user_id"]

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        age_raw = request.form.get("age")

        if not username:
            flash("نام کاربری را وارد کنید", "warning")
            return redirect(url_for("edit_account"))

        age = None
        if age_raw:
            try:
                age = int(age_raw)
            except ValueError:
                flash("سن باید عدد باشد", "error")
                return redirect(url_for("edit_account"))

        success, message, result = update_user__db(
            user_id, username, password, firstname, lastname, age
        )
        if success:
            flash(message, "success")
            return redirect(url_for("edit_account"))
        else:
            flash(f"{message} : خطا در بارگذاری اطلاعات", "error")
            return redirect(url_for("edit_account"))

    success, message, result = get_user_by_id__db(user_id)

    if success:
        # flash(message, "success")
        return render_template("edit_account.html", user_data=result)
    else:
        flash(message, "error")
        return render_template("edit_account.html", user_data=None)


# ---------------- profile: management ----------------
@app.route("/users/profile", methods=["GET", "POST"])
@login_required
def profile_manage():
    user_id = session["user_id"]

    if request.method == "POST":
        bio = request.form.get("bio")
        avatar_url = request.form.get("avatar_url")

        success, message, existing_profile = get_profile__db(user_id)

        if not success:
            flash(message, "error")
            return redirect(url_for("profile_manage"))

        if existing_profile:
            success, message = update_profile__db(
                uid=user_id, bio=bio, avatar_url=avatar_url
            )
        else:
            success, message = create_profile__db(
                uid=user_id, bio=bio, avatar_url=avatar_url
            )

        flash(message, "success" if success else "error")
        return redirect(url_for("profile_manage"))

    success, message, result = get_profile__db(user_id)
    if not success:
        flash(message, "error")

    return render_template("profile.html", profile=result)


# -------------------# avatar #------------------------
def get_avatar_list():
    avatar_folder = os.path.join(app.static_folder, "avatars")
    files = os.listdir(avatar_folder)
    valid_extensions = (".jpg", ".jpeg", ".png", ".webp")
    images = [f for f in files if f.lower().endswith(valid_extensions)]
    return images


# ---------------- profile: avatar ----------------
@app.route("/users/profile/avatars", methods=["GET", "POST"])
@login_required
def choose_avatar():
    if request.method == "POST":
        avatar_filename = request.form.get("avatar_url")
        valid_avatars = get_avatar_list()

        if avatar_filename not in valid_avatars:
            flash("آواتار انتخابی معتبر نیست", "error")
            return redirect(url_for("choose_avatar"))

        avatar_path = f"avatars/{avatar_filename}"

        success, message, existing_profile = get_profile__db(session["user_id"])
        if not success:
            flash(message, "error")
            return redirect(url_for("choose_avatar"))

        if existing_profile:
            success, message = update_profile__db(
                uid=session["user_id"], avatar_url=avatar_path
            )
        else:
            success, message = create_profile__db(
                uid=session["user_id"], avatar_url=avatar_path
            )

        flash(message, "success" if success else "error")
        return redirect(url_for("profile_manage"))

    avatars = get_avatar_list()
    return render_template("choose_avatar.html", avatars=avatars)


# ---------------- profile: delete_account ----------------------
@app.route("/users/profile/delete", methods=["POST"])
@login_required
def delete_account():
    success, message = delete_user__db(session["user_id"])

    if success:
        session.clear()
        flash(message, "success")
        return redirect(url_for("auth_login"))
    else:
        flash(message, "error")
        return redirect(url_for("profile_manage"))


# -------------------------------------------------------


# ---------------*** Error Handler ***------------------
# --------------- app: error_handling -----------------
@app.errorhandler(404)
def errors_page_not_found(e):
    return "این صفحه پیدا نشد. به آدرس‌ /home سر بزنید.", 404


# -----------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
