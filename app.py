from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

@app.route("/")
def home():
    return render_template("index.html")

#Calling the Student login form
@app.route("/student_login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form["semail"]
        password = request.form["spassword"]
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students_rgd WHERE email=%s", (email,))
        student = cursor.fetchone()
        conn.close()
        #if student and check_password_hash(student[5], password): #Encrypt then Match password
        if student and student[5] == password:   #Match with direct entered plain password
            session["student_id"] = student[0]
            session["student_name"] = student[1]
            return redirect("/stddashboard")
        else:
            return "Invalid Email or Password"

    return render_template("student_login.html")



@app.route("/stddashboard")
def stddashboard():
    if "student_id" not in session:
        return redirect("/student_login")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students_rgd WHERE std_id=%s", (session["student_id"],))
    student = cursor.fetchone()
    conn.close()

    return render_template("stddashboard.html", student=student)



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/student_login")


if __name__ == "__main__":
    app.run(debug=True)