import os
import re
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
    create_post__db,
    get_posts_by_user__db,
    delete_post__db,
    update_post__db,
    get_all_posts__db,
    add_tag_to_post__db,
    remove_tag_from_post__db,
    get_posts_by_tag__db,
    get_all_tags__db,
    delete_tag__db,
    seed_demo_users__db,
)
from dotenv import load_dotenv
from log_setup import get_logger
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")


# ----------------** LOG **---------------------------
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    logger = get_logger("app")
else:
    logger = logging.getLogger("app")
    logger.addHandler(logging.NullHandler())
    logger.propagate = False

# ---------------@ app: seed demo users @-------------
#        (Render free-tier disk resets on redeploy)
seed_demo_users__db()
# ----------------------------------------------------


# ---------------** DECORATOR **----------------------
# --------------- auth: req_login --------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            logger.warning("Unauthorized access to endpoint=%s", request.endpoint)
            flash("ابتدا وارد شوید", "warning")
            return redirect(url_for("auth_login"))
        return f(*args, **kwargs)

    return decorated_function


# --------------- auth: req_admin --------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("ابتدا وارد شوید", "warning")
            return redirect(url_for("auth_login"))

        success, message, user = get_user_by_id__db(session["user_id"])
        if not success or not user.is_admin:
            logger.warning(
                "Unauthorized admin access attempt (user_id=%s, endpoint=%s)",
                session["user_id"],
                request.endpoint,
            )
            flash("شما به این بخش دسترسی ندارید", "error")
            return redirect(url_for("home"))
        return f(*args, **kwargs)

    return decorated_function


# ---------------- tag -------------------------------
def parse_tag_input(raw_input):
    tags = re.split(r"[,\s]+", raw_input.strip())
    return [tag for tag in tags if tag]


# ----------------* HOME *----------------------------
@app.route("/home")
@app.route("/")
def home():
    is_authenticated = "user_id" in session

    tags_success, _, tags = get_all_tags__db()
    if not tags_success:
        tags = []

    return render_template(
        "home.html",
        is_authenticated=is_authenticated,
        tags=tags,
    )


# ----------------* USERS *---------------------------
# ---------------- users: database -------------------
@app.route("/users")
def users_list():
    success, message, all_users = get_all_users__db()
    logger.info("Listed users (success=%s)", success)
    flash(message, "success" if success else "error")
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
        if success:
            logger.info("User registered (username=%s)", username)
        else:
            logger.warning("User registration failed (username=%s)", username)
        flash(message, "success" if success else "error")
        if success:
            return redirect(url_for("users_list"))
        else:
            return redirect(url_for("auth_register"))

    return render_template("register.html")


# -------------- auth: database_login -----------
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
            logger.info("User logged in (user_id=%s)", user_id)
            flash(message, "success")

            return redirect(url_for("edit_account"))
        else:
            logger.warning("Login failed (username=%s)", username)
            flash(message, "error")
            return render_template("userslogin.html")

    return render_template("userslogin.html")


# -------------- auth: logout -------------------
@app.route("/users/logout", methods=["POST"])
def auth_logout():
    user_id = session.pop("user_id", None)
    logger.info("User logged out (user_id=%s)", user_id)
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
            logger.info("Account updated (user_id=%s)", user_id)
            flash(message, "success")
            return redirect(url_for("edit_account"))
        else:
            logger.warning("Account update failed (user_id=%s)", user_id)
            flash(f"{message} : خطا در بارگذاری اطلاعات", "error")
            return redirect(url_for("edit_account"))

    success, message, result = get_user_by_id__db(user_id)

    if success:
        # flash(message, "success")
        return render_template("edit_account.html", user_data=result)
    else:
        logger.error("Failed to load account (user_id=%s)", user_id)
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
        if success:
            logger.info(
                "Profile %s (user_id=%s)",
                "updated" if existing_profile else "created",
                user_id,
            )
        else:
            logger.warning("Profile operation failed (user_id=%s)", user_id)
        return redirect(url_for("profile_manage"))

    success, message, result = get_profile__db(user_id)
    if not success:
        logger.error("Failed to load profile (user_id=%s)", user_id)
        flash(message, "error")

    return render_template("profile.html", profile=result)


# ----------------# avatar #---------------------
def get_avatar_list():
    avatar_folder = os.path.join(app.static_folder, "avatars")
    files = os.listdir(avatar_folder)
    valid_extensions = (".jpg", ".jpeg", ".png", ".webp")
    images = [f for f in files if f.lower().endswith(valid_extensions)]
    return images


# -------------- profile: avatar ----------------
@app.route("/users/profile/avatars", methods=["GET", "POST"])
@login_required
def choose_avatar():
    if request.method == "POST":
        avatar_filename = request.form.get("avatar_url")
        valid_avatars = get_avatar_list()

        if avatar_filename not in valid_avatars:
            logger.warning("Invalid avatar selection (filename=%s)", avatar_filename)
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
        if success:
            logger.info(
                "Avatar updated (user_id=%s, filename=%s)",
                session["user_id"],
                avatar_filename,
            )
        else:
            logger.warning("Avatar update failed (user_id=%s)", session["user_id"])
        return redirect(url_for("profile_manage"))

    avatars = get_avatar_list()
    return render_template("choose_avatar.html", avatars=avatars)


# ------------- profile: delete_account ---------
@app.route("/users/profile/delete", methods=["POST"])
@login_required
def delete_account():
    success, message = delete_user__db(session["user_id"])

    if success:
        logger.info("Account deleted (user_id=%s)", session["user_id"])
        session.clear()
        flash(message, "success")
        return redirect(url_for("auth_login"))
    else:
        logger.warning("Account deletion failed (user_id=%s)", session["user_id"])
        flash(message, "error")
        return redirect(url_for("profile_manage"))


# ----------------------------------------------------


# -------------- posts: owner_actions ----------------
@app.route("/users/posts/new", methods=["GET", "POST"])
@login_required
def posts_create():
    user_id = session["user_id"]
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        tags_raw = request.form.get("tags", "")
        success, message, result = create_post__db(user_id, title, content)
        if success:
            tags = parse_tag_input(tags_raw)
            for tag_name in tags:
                add_tag_to_post__db(result.post_id, tag_name, user_id)

            logger.info(
                "Post created (post_id=%s, user_id=%s)", result.post_id, user_id
            )
            flash(message, "success")
            flash(
                f"title: {result.title}\ncontent: {result.content}\ncreated_at:{result.created_at}",
                "post",
            )
            return redirect(url_for("posts_create"))
        else:
            logger.warning("Post creation failed (user_id=%s)", user_id)
            flash(f"{message} : خطا در بارگذاری اطلاعات", "error")
            return redirect(url_for("posts_create"))

    return render_template("posts_create.html")


# -------------- posts: owner_list_and_update --------
@app.route("/users/posts/show", methods=["GET", "POST"])
@login_required
def posts_list_owned_update():
    user_id = session["user_id"]
    if request.method == "POST":
        post_id = request.form.get("post_id")
        try:
            post_id = int(post_id)
        except (ValueError, TypeError):
            flash("شناسه‌ی نامعتبر است", "error")
            return redirect(url_for("posts_list_owned_update"))

        title = request.form.get("title")
        content = request.form.get("content")

        success, message = update_post__db(post_id, user_id, title, content)
        if success:
            logger.info("Post updated (post_id=%s, user_id=%s)", post_id, user_id)
            flash(message, "success")
            return redirect(url_for("posts_list_owned_update"))
        else:
            logger.warning(
                "Post update failed (post_id=%s, user_id=%s)", post_id, user_id
            )
            flash(f"{message} : خطا در بارگذاری اطلاعات", "error")
            return redirect(url_for("posts_list_owned_update"))

    success, message, result = get_posts_by_user__db(user_id)
    title_filter = request.args.get("title", "")
    if result:
        result = [p for p in result if title_filter.lower() in p.title.lower()]
    return render_template(
        "posts_list_owned_update.html", posts=result, title_filter=title_filter
    )


# --------------- posts: owner_delete -----------------
@app.route("/users/posts/delete", methods=["POST"])
@login_required
def posts_delete():
    user_id = session["user_id"]
    post_id = request.form.get("post_id")

    try:
        post_id = int(post_id)
    except (ValueError, TypeError):
        flash("شناسه‌ی نامعتبر است", "error")
        return redirect(url_for("posts_list_owned_update"))

    success, message = delete_post__db(post_id, user_id)

    if success:
        logger.info("Post deleted (post_id=%s, user_id=%s)", post_id, user_id)
        flash(message, "success")
    else:
        logger.warning(
            "Post deletion failed (post_id=%s, user_id=%s)", post_id, user_id
        )
        flash(message, "error")
    return redirect(url_for("posts_list_owned_update"))


# --------------- posts: public_list -----------------
@app.route("/users/posts/showall")
def posts_list_all():

    title_filter = request.args.get("title", "")
    user_filter = request.args.get("user", "")
    success, message, result = get_all_posts__db(
        title_filter=title_filter, user_filter=user_filter
    )

    if not success:
        logger.error("Failed to load public posts")
        flash(message, "error")
        result = []

    return render_template(
        "posts_list_all.html",
        posts=result,
        title_filter=title_filter,
        user_filter=user_filter,
    )


# ----------------------------------------------------


# ----------------* TAG *-----------------------------
# ---------------- tag: posts_by_tag -----------------
@app.route("/users/posts/tag/<tag_name>")
def posts_by_tag(tag_name):
    success, message, posts = get_posts_by_tag__db(tag_name)

    if not success:
        logger.error("Failed to load posts by tag (tag=%s)", tag_name)
        flash(message, "error")
        posts = []

    return render_template("posts_by_tag.html", posts=posts, tag_name=tag_name)


# ---------------- tag: add --------------------------
@app.route("/users/posts/tag/add", methods=["POST"])
@login_required
def posts_add_tag():
    user_id = session["user_id"]
    post_id = request.form.get("post_id")
    tag_name = request.form.get("tag_name")

    try:
        post_id = int(post_id)
    except (ValueError, TypeError):
        flash("شناسه‌ی نامعتبر است", "error")
        return redirect(url_for("posts_list_owned_update"))

    success, message = add_tag_to_post__db(post_id, tag_name, user_id)

    if success:
        logger.info(
            "Tag added (post_id=%s, tag_name=%s, user_id=%s)",
            post_id,
            tag_name,
            user_id,
        )
        flash(message, "success")
    else:
        logger.warning(
            "Tag addition failed (post_id=%s, tag_name=%s, user_id=%s)",
            post_id,
            tag_name,
            user_id,
        )
        flash(message, "error")
    return redirect(url_for("posts_list_owned_update"))


# ---------------- tag: remove -----------------------
@app.route("/users/posts/tag/remove", methods=["POST"])
@login_required
def posts_remove_tag():
    user_id = session["user_id"]
    post_id = request.form.get("post_id")
    tag_name = request.form.get("tag_name")

    try:
        post_id = int(post_id)
    except (ValueError, TypeError):
        flash("شناسه‌ی نامعتبر است", "error")
        return redirect(url_for("posts_list_owned_update"))

    success, message = remove_tag_from_post__db(post_id, tag_name, user_id)

    if success:
        logger.info(
            "Tag deleted (post_id=%s, tag_name=%s, user_id=%s)",
            post_id,
            tag_name,
            user_id,
        )
        flash(message, "success")
    else:
        logger.warning(
            "Tag deletion failed (post_id=%s, tag_name=%s, user_id=%s)",
            post_id,
            tag_name,
            user_id,
        )
        flash(message, "error")
    return redirect(url_for("posts_list_owned_update"))


# ----------------* admin *------------------------------
# ---------------- admin: tags list --------------------
@app.route("/admin/tags")
@admin_required
def admin_tags():
    success, message, tags = get_all_tags__db()
    if not success:
        flash(message, "error")
        tags = []
    return render_template("admin_tags.html", tags=tags)


# ---------------- admin: tags remove --------------------
@app.route("/admin/tags/remove", methods=["POST"])
@admin_required
def admin_remove_tag():
    user_id = session["user_id"]
    tag_name = request.form.get("tag_name")

    success, message = delete_tag__db(tag_name)

    if success:
        logger.info(
            "Tag deleted by admin (tag_name=%s, admin_id=%s)", tag_name, user_id
        )
        flash(message, "success")
    else:
        logger.warning(
            "Tag deletion failed (tag_name=%s, admin_id=%s)", tag_name, user_id
        )
        flash(message, "error")
    return redirect(url_for("admin_tags"))


# ---------------*** ERROR HANDLER ***----------------
# --------------- app: error_handling ----------------
@app.errorhandler(404)
def errors_page_not_found(e):
    logger.warning("Page not found (path=%s)", request.path)
    return "این صفحه پیدا نشد. به آدرس‌ /home سر بزنید.", 404


# -----------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
