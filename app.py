from flask import Flask, flash, render_template, request, redirect, session
import pymysql
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

        if student and student["std_password"] == password:   #Match with direct entered plain password
            session["student_id"] = student["std_id"]
            session["student_name"] = student["first_name"]
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


# #Student View Profile

# @app.route("/stdstudent_profile")
# def stdstudent_profile():

#     if "student_id" not in session:
#         return redirect("/student_login")

#     conn = get_db()
#     cursor = conn.cursor()

#     cursor.execute(
#         "SELECT * FROM students_rgd WHERE std_id=%s",
#         (session["student_id"],)
#     )

#     student = cursor.fetchone()

#     conn.close()

#     return render_template("stdstudent_profile.html", student=student)

#Code for View and Edit Student Profile self:
@app.route("/stdstudent_profile", methods=["GET","POST"])
def stdstudent_profile():

    if "student_id" not in session:
        return redirect("/student_login")

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":

        email = request.form["email"]
        phone = request.form["phone"]

        cursor.execute(
            "UPDATE students_rgd SET email=%s, phone=%s WHERE std_id=%s",
            (email, phone, session["student_id"])
        )

        conn.commit()

    cursor.execute(
        "SELECT * FROM students_rgd WHERE std_id=%s",
        (session["student_id"],)
    )

    student = cursor.fetchone()

    conn.close()

    return render_template("stdstudent_profile.html", student=student)

#Student Forgot Password Route

@app.route("/std_forgot_password", methods=["GET","POST"])
def std_forgot_password():

    error = None

    if request.method == "POST":

        # STEP 1 → verify email
        if "email" in request.form:

            email = request.form["email"]

            conn = get_db()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT std_id FROM students_rgd WHERE email=%s",
                (email,)
            )

            student = cursor.fetchone()
            conn.close()

            if student:
                session["reset_student"] = student["std_id"]
            else:
                error = "Email not found"

        # STEP 2 → update password
        elif "new_password" in request.form:

            new_password = request.form["new_password"]
            confirm_password = request.form["confirm_password"]

            if new_password != confirm_password:
                error = "Passwords do not match"

            else:

                conn = get_db()
                cursor = conn.cursor()

                cursor.execute(
                    "UPDATE students_rgd SET std_password=%s WHERE std_id=%s",
                    (new_password, session["reset_student"])
                    
                )
                
                conn.commit()

                return render_template( "std_forgot_password.html",
                success="Password updated Successfully!"
                )

                conn.close()

                session.pop("reset_student")

                return redirect("/student_login")

    return render_template(
        "std_forgot_password.html",
        show_reset="reset_student" in session,
        error=error
    )


#Teacher part: #teacher login--

@app.route("/teacher_login", methods=["GET","POST"])
def teacher_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM teachers WHERE email=%s",
            (email,)
        )

        teacher = cursor.fetchone()

        conn.close()

        if teacher and teacher["teacher_password"] == password:

            session["teacher_id"] = teacher["tchr_id"]
            session["teacher_name"] = teacher["first_name"]

            return redirect("/teacher_dashboard")

        else:
            return render_template("teacher_login.html", error="Invalid Creadential")
    
    return render_template("teacher_login.html")

# Teacher dashboard Route... After success login below route will call
@app.route("/teacher_dashboard")
def teacher_dashboard():

    if "teacher_id" not in session:
        return redirect("/teacher_login")

    return render_template("teacher_dashboard.html")


#Update Teacher Profile:

@app.route("/teacher_profile", methods=["GET","POST"])
def teacher_profile():

    if "teacher_id" not in session:
        return redirect("/teacher_login")

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":

        email = request.form["email"]
        phone = request.form["phone"]

        cursor.execute(
            "UPDATE teachers SET email=%s, phone=%s WHERE tchr_id=%s",
            (email, phone, session["teacher_id"])
        )

        conn.commit()

    cursor.execute(
        "SELECT * FROM teachers WHERE tchr_id=%s",
        (session["teacher_id"],)
    )

    teacher = cursor.fetchone()

    conn.close()

    return render_template("teacher_profile.html", teacher=teacher)


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
        print(admin)
        conn.close()

        if admin and admin["adm_password"] == password:
            session["admin_id"] = admin["adm_id"]
            session["admin_name"] = admin["adm_fname"]
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

        try:
            # Check if email already exists
            cursor.execute(
                "SELECT std_id FROM students_rgd WHERE email=%s",
                (email,)
            )
            if cursor.fetchone():
                return render_template(
                    "admin_register_students.html",
                    error="Email already registered!"
                )

            #Insert
            cursor.execute(
                "INSERT INTO students_rgd (first_name, last_name, email, phone, std_password) VALUES (%s, %s, %s, %s, %s)",
                (fname, lname, email, sphone, password)
            )
            conn.commit()

            return render_template(
                "admin_register_students.html",
                success="Student Registered Successfully!"
            )

        except pymysql.err.IntegrityError:
            # fallback safety (race condition protection)
            return render_template(
                "admin_register_students.html",
                error="Email already exists (DB constraint)."
            )

        finally:
            conn.close()

    return render_template("admin_register_students.html")

#Admin View Registered Students:
@app.route("/adm_students_list")
def adm_students_list():

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students_rgd")
    adm_view_students = cursor.fetchall()

    conn.close()

    return render_template("adm_students_list.html", adm_view_students=adm_view_students)

#Admin can Edit Registered Students details:

@app.route("/adm_edit_student/<int:std_id>", methods=["GET","POST"])
def adm_edit_student(std_id):

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":

        fname = request.form["fname"]
        lname = request.form["lname"]
        email = request.form["email"]
        phone = request.form["phone"]

        cursor.execute(
            "UPDATE students_rgd SET first_name=%s, last_name=%s, email=%s, phone=%s WHERE std_id=%s",
            (fname, lname, email, phone, std_id)
        )

        conn.commit()
        conn.close()

        return redirect("/adm_students_list")

    cursor.execute("SELECT * FROM students_rgd WHERE std_id=%s",(std_id,))
    student = cursor.fetchone()

    conn.close()

    return render_template("adm_edit_student.html", student=student)

#Admin can Delete Registered Students:
@app.route("/delete_student/<int:std_id>")
def delete_student(std_id):

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students_rgd WHERE std_id=%s", (std_id,))

    conn.commit()
    conn.close()

    return redirect("/adm_students_list")

#Admin can add teacher

@app.route("/admadd_teacher", methods=["GET","POST"])
def admadd_teacher():

    if "admin_id" not in session:
        return redirect("/admin_login")

    if request.method == "POST":

        fname = request.form["fname"]
        lname = request.form["lname"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        try:
            # Check duplicate
            cursor.execute("SELECT * FROM teachers WHERE email=%s", (email,))
            if cursor.fetchone():
                flash("Email already exists!", "danger")
                return redirect("/admadd_teacher")

            # Insert
            cursor.execute(
                "INSERT INTO teachers (first_name,last_name,email,phone,teacher_password) VALUES (%s,%s,%s,%s,%s)",
                (fname,lname,email,phone,password)
            )

            conn.commit()

            return render_template("/admadd_teacher", success="Teacher Added Successfully!")

        except pymysql.err.IntegrityError:

            return render_template("/admadd_teacher", error="Duplicate email not allowed!")

        finally:
            conn.close()

    return render_template("admadd_teacher.html")


#Admin View Registered Teachers:
@app.route("/adm_teachers_list")
def adm_teachers_list():

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM teachers")
    adm_view_teacher = cursor.fetchall()

    conn.close()

    return render_template("adm_teachers_list.html", adm_view_teacher=adm_view_teacher)





#Admin can Edit Registered Teachers details:
@app.route("/adm_edit_teacher/<int:tchr_id>", methods=["GET","POST"])
def adm_edit_teacher(tchr_id):

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor()

    try:
        if request.method == "POST":

            fname = request.form["fname"]
            lname = request.form["lname"]
            email = request.form["email"].strip()
            phone = request.form["phone"]

            #duplicate check
            cursor.execute(
                "SELECT * FROM teachers WHERE email=%s AND tchr_id!=%s",
                (email, tchr_id)
            )
            if cursor.fetchone():
                # re-render with same data
                return render_template(
                    "adm_edit_teacher.html",
                    teacher={
                        "tchr_id": tchr_id,
                        "first_name": fname,
                        "last_name": lname,
                        "email": email,
                        "phone": phone
                    },
                    error="Email already exists!"
                )

            # update
            cursor.execute(
                "UPDATE teachers SET first_name=%s, last_name=%s, email=%s, phone=%s WHERE tchr_id=%s",
                (fname, lname, email, phone, tchr_id)
            )
            conn.commit()

            flash("Teacher updated successfully!", "success")
            return redirect(f"/adm_edit_teacher/{tchr_id}")

        # GET request
        cursor.execute("SELECT * FROM teachers WHERE tchr_id=%s", (tchr_id,))
        teacher = cursor.fetchone()

        return render_template("adm_edit_teacher.html", teacher=teacher)

    finally:
        conn.close()


#Admin can Delete Registered Teachers:
@app.route("/delete_teacher/<int:tchr_id>")
def delete_teacher(tchr_id):

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM teachers WHERE tchr_id=%s", (tchr_id,))

    conn.commit()
    conn.close()

    return redirect("/adm_teachers_list")





if __name__ == "__main__":
    app.run(debug=True)