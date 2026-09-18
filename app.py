import os
from flask import Flask, url_for, redirect, render_template, flash
from dotenv import load_dotenv
from models import get_all_users__db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")


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
    return render_template("users.html", users=all_users)


if __name__ == "__main__":
    app.run(debug=True)
