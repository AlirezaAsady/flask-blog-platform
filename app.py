import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")


@app.route("/")
def home():
    return "Flask app is running."


if __name__ == "__main__":
    app.run(debug=True)
