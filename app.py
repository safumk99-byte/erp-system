from flask import Flask, render_template
from config import SECRET_KEY
from routes.auth import auth
from routes.dashboard import dashboard_bp
from routes.institutions import institution
from routes.staff import staff
from routes.portal import portal
from routes.students import students
from routes.classes import classes
from routes.subjects import subjects
from routes.parents import parents

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.register_blueprint(auth)
app.register_blueprint(dashboard_bp)
app.register_blueprint(institution)
app.register_blueprint(staff)
app.register_blueprint(portal)
app.register_blueprint(students)
app.register_blueprint(classes)
app.register_blueprint(subjects)
app.register_blueprint(parents)



@app.route("/login")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)