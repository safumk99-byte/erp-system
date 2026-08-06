from flask import Flask, render_template
from config import SECRET_KEY
from routes.auth import auth
from routes.dashboard import dashboard

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.register_blueprint(auth)
app.register_blueprint(dashboard)


@app.route("/")
def home():
    return "ERP Backend Running Successfully 🚀"

@app.route("/login")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)