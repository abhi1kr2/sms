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


#Admin Part:

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["admusername"]
        password = request.form["admpassword"]

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE adm_email=%s", (username,))
        admin = cursor.fetchone()
        conn.close()

        if admin and admin[5] == password:
            session["admin_id"] = admin[0]
            session["admin_name"] = admin[1]
            return redirect("/admin_dashboard")
        else:
            return "Invalid Admin Credentials"

    return render_template("admin_login.html")


@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        return redirect("/admin_login")

    return render_template("admin_dashboard.html")

#From Admin Register Students
@app.route("/admin_register_students", methods=["GET", "POST"])
def admin_register_students():
    if "admin_id" not in session:
        return redirect("/admin_login")

    if request.method == "POST":

        fname = request.form["fname"]
        lname = request.form["lname"]
        # ft_name = request.form["ftname"]
        # mt_name = request.form["mtname"]
        email = request.form["email"]
        sphone = request.form["sphno"]
        # stdcls = request.form["stdclass"]
        # cls_sec = request.form["classsec"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO students_rgd (first_name, last_name, email, phone, std_password) VALUES (%s, %s, %s, %s, %s)",
            (fname, lname, email, sphone, password)
        )
        conn.commit()
        conn.close()

        return "Student Registered Successfully!"

    return render_template("admin_register_students.html")



if __name__ == "__main__":
    app.run(debug=True)