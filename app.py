import os
import logging
from flask import Flask, request, url_for, redirect, render_template, flash, session
from models import get_all_users__db, create_user__db, login_user__db
from dotenv import load_dotenv
from log_setup import get_logger

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


# -------------------* HOME *--------------------------
@app.route("/home")
@app.route("/")
def home():
    return render_template("home.html")


# ----------------* users *---------------------------
# ---------------- users: database -------------------
@app.route("/users")
def users_list():
    success, message, all_users = get_all_users__db()
    # print(success, message)
    flash(message, "success")
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

            # TODO: redirect to edit_profile once
            return redirect(url_for("auth_login"))
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


if __name__ == "__main__":
    app.run(debug=True)
