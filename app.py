from datetime import date
import re

from flask import Flask, flash, jsonify, render_template, request, redirect, session, url_for
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/programs")
def programs():
    return render_template("programs.html")

#For Enquiry- Insert into Table
@app.route('/save_enquiry', methods=['POST'])
def save_enquiry():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    course = request.form.get('course')
    message = request.form.get('message')

    if not name or not phone or not course:
        return jsonify({"status": "error", "message": "Required fields missing"})

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO enquiries (name, email, phone, course, message)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, phone, course, message))

        conn.commit()
        cursor.close()

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

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
            error = "Invalid Email or Password"
            return render_template("student_login.html", error=error)

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


#=====Admin Part=====
#Admin Login-

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
            error = "Invalid Email or Password"
            return render_template("admin_login.html", error=error) 

    return render_template("admin_login.html")


@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        return redirect("/admin_login")

    return render_template("admin_dashboard.html")



#Start code for student registration by admin---

@app.route("/admin_register_students", methods=["GET", "POST"])
def admin_register_students():

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor()

    #fetch classes (needed for both GET & POST re-render)
    cursor.execute("SELECT id, class_name FROM classes WHERE status='Active'")
    classes = cursor.fetchall()

    if request.method == "POST":
        try:
            # -------- FORM DATA --------
            fname = request.form["fname"].strip()
            lname = request.form["lname"].strip()
            dob = request.form.get("dob")

            email = request.form["email"].strip()
            sphone = request.form["sphno"].strip()
            class_id = request.form["class_id"].strip()  # From fronted take class_id

            father = request.form["ftname"].strip()
            mother = request.form.get("mtname")
            parent_phone = request.form["pphno"].strip()

            address = request.form.get("address")
            state = request.form.get("state")
            pincode = request.form.get("pincode")

            prev_school = request.form.get("prev_school")
            prev_address = request.form.get("prev_address")

            admission_date = request.form.get("admission_date")
            password_input = request.form["password"]

            # -------- VALIDATION --------
            if len(sphone) < 10:
                return render_template("admin_register_students.html", error="Invalid phone number")

            # -------- EMAIL CHECK --------
            cursor.execute("SELECT std_id FROM students_rgd WHERE email=%s", (email,))
            if cursor.fetchone():
                return render_template("admin_register_students.html", error="Email already exists")
            
            #Value for admission date
            if not admission_date:
                admission_date = date.today()
            
            #Creating default Password
            # sanitize first name (letters/numbers only)
            safe_fname = re.sub(r'[^a-zA-Z0-9]', '', fname).lower()

            if not password_input:
                default_password = f"{safe_fname}@{sphone}"
            else:
                default_password = password_input
            
            # -------- GENERATE REG ID --------
            cursor.execute("SELECT COUNT(*) AS c FROM students_rgd")
            count = cursor.fetchone()["c"] + 1
            reg_id = f"STD-{str(count).zfill(4)}"

            # -------- INSERT --------
            cursor.execute("""
                INSERT INTO students_rgd (
                    reg_id, first_name, last_name, std_dob,
                    email, phone, class_id,
                    father_name, mother_name, parent_phone,
                    address, state, pincode,
                    prev_school_name, prev_school_address,
                    admission_date, status, std_password
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Active',%s)
            """, (
                reg_id, fname, lname, dob,
                email, sphone, class_id,
                father, mother, parent_phone,
                address, state, pincode,
                prev_school, prev_address,
                admission_date, default_password
            ))

            conn.commit()
            return render_template(
                "admin_register_students.html",
                success=f"Student Registered Successfully! ID: {reg_id}",
                classes=classes
            )

        except Exception as e:
            return f"Error: {e}"

        finally:
            conn.close()

    return render_template(
        "admin_register_students.html",
        classes=classes   # REQUIRED for dropdown
    )


#End code for student registration by admin---


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




#Start Code for Save/Enter Marks of Students by admin--


@app.route("/admin_marks_entry")
def admin_marks_entry():

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, class_name FROM classes")
    classes = cursor.fetchall()

    cursor.execute("SELECT id, name FROM exams WHERE status='Active'")
    exams = cursor.fetchall()

    conn.close()

    return render_template("admin_marks_entry.html", classes=classes, exams=exams)


            #Loading Student Details


@app.route("/get_students/<int:class_id>")
def get_students(class_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT std_id, first_name, reg_id
        FROM students_rgd
        WHERE class_id=%s
    """, (class_id,))

    students = cursor.fetchall()
    conn.close()

    return jsonify(students)


            #Loading Subjects appear with input boxes

@app.route("/get_subjects/<int:class_id>")
def get_subjects(class_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name 
        FROM subjects 
        WHERE class_id=%s
    """, (class_id,))

    subjects = cursor.fetchall()
    conn.close()

    return jsonify(subjects)




        #Code for Marks Saving


@app.route("/save_marks", methods=["POST"])
def save_marks():

    std_id = request.form.get("std_id")
    exam_id = request.form.get("exam_id")

    conn = get_db()
    cursor = conn.cursor()

    # get subjects for student class
    cursor.execute("""
        SELECT id FROM subjects WHERE class_id = (
            SELECT class_id FROM students_rgd WHERE std_id=%s
        )
    """, (std_id,))

    subjects = cursor.fetchall()

    for s in subjects:
        subject_id = s["id"]
        marks = request.form.get(f"marks_{subject_id}")

        if not marks:
            continue

        cursor.execute("""
            INSERT INTO marks (std_id, subject_id, exam_id, marks_obtained)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE marks_obtained=%s
        """, (std_id, subject_id, exam_id, marks, marks))
    conn.commit()
    
    flash("Marks saved successfully!", "success")
    conn.close()
    
    return redirect("/admin_marks_entry")


    #code for autofilled(if marks inserted->fetch) and update Marks


@app.route("/get_marks/<int:std_id>/<int:exam_id>")
def get_marks(std_id, exam_id):

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT subject_id, marks_obtained
        FROM marks
        WHERE std_id=%s AND exam_id=%s
    """, (std_id, exam_id))

    data = cursor.fetchall()
    conn.close()

    return jsonify(data)





#End Code for Save/Enter Marks of Students by admin--


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

#====Start Gallery====

#====End Gallery====

#====Start Notice====

#====End Notice====

#====Start Enquiry====
@app.route("/adm_view_enquiries")
def adm_view_enquiries():

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor()

    # Get filter value
    course = request.args.get("course")

    if course:
        cursor.execute(
            "SELECT * FROM enquiries WHERE course=%s ORDER BY id DESC",
            (course,)
        )
    else:
        cursor.execute(
            "SELECT * FROM enquiries ORDER BY id DESC"
        )

    enquiries = cursor.fetchall()
    cursor.close()

    return render_template("adm_view_enquiries.html", enquiries=enquiries)

# UPDATE STATUS OF Enquiry
@app.route("/update_status/<int:id>")
def update_status(id):

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE enquiries SET status='Contacted' WHERE id=%s",
        (id,)
    )
    conn.commit()
    cursor.close()
    return redirect(url_for("adm_view_enquiries"))


# DELETE ENQUIRY 
@app.route("/delete_enquiry/<int:id>")
def delete_enquiry(id):

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM enquiries WHERE id=%s",
        (id,)
    )

    conn.commit()
    cursor.close()

    return redirect(url_for("adm_view_enquiries"))


#====End Enquiry====



if __name__ == "__main__":
    app.run(debug=True)