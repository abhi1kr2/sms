from datetime import date
import re
import os
from werkzeug.utils import secure_filename
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


#Code for Student Dashboard Route

@app.route("/stddashboard")
def stddashboard():

    if "student_id" not in session:
        return redirect("/student_login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # ---------------- STUDENT INFO ----------------

    cursor.execute("""
        SELECT
            s.*,
            c.class_name

        FROM students_rgd s

        LEFT JOIN classes c
            ON s.class_id = c.id

        WHERE s.std_id=%s
    """, (session["student_id"],))

    student = cursor.fetchone()

    # ---------------- SUBJECTS ----------------

    cursor.execute("""
        SELECT *
        FROM subjects
        WHERE class_id=%s
    """, (student["class_id"],))

    subjects = cursor.fetchall()

    # ---------------- TEACHERS ----------------

    cursor.execute("""
        SELECT *
        FROM teachers
        WHERE class_id=%s
    """, (student["class_id"],))

    teachers = cursor.fetchall()

    conn.close()

    return render_template(
        "stddashboard.html",

        student=student,
        subjects=subjects,
        teachers=teachers
    )




#Code for Student Dashboard Route-context_processor
@app.context_processor
def inject_student():

    if "student_id" in session:

        conn = get_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT first_name FROM students_rgd WHERE std_id=%s
        """, (session["student_id"],))

        student = cursor.fetchone()
        conn.close()

        return dict(current_student=student)

    return dict(current_student=None)

# Code for Student Logout

@app.route("/student_logout")
def student_logout():
    session.clear()
    return redirect("/student_login")



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



#Start Code for View Marks by student Dasboard---

@app.route("/std_view_marks")
def std_view_marks():

    if "student_id" not in session:
        return redirect("/student_login")

    std_id = session["student_id"]
    exam_id = request.args.get("exam_id")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Load exams for dropdown
    cursor.execute("SELECT id, name FROM exams WHERE status='Active'")
    exams = cursor.fetchall()

    # Default (no result yet)
    data = None
    message = None

    if exam_id:

        # student
        cursor.execute("""
            SELECT first_name, last_name, reg_id
            FROM students_rgd
            WHERE std_id=%s
        """, (std_id,))
        student = cursor.fetchone()

        # exam
        cursor.execute("SELECT id, name FROM exams WHERE id=%s", (exam_id,))
        exam = cursor.fetchone()

        # marks
        cursor.execute("""
            SELECT s.name AS subject,
                   s.passing_marks,
                   m.marks_obtained
            FROM marks m
            JOIN subjects s ON m.subject_id = s.id
            WHERE m.std_id=%s AND m.exam_id=%s
            ORDER BY s.name
        """, (std_id, exam_id))

        rows = cursor.fetchall()

        feedback = [] 
        data = None     

        if not rows:
            message = "No marks available for selected exam."
        else:
            total = sum(r["marks_obtained"] for r in rows)
            max_total = len(rows) * 100
            percent = (total / max_total * 100) if max_total else 0
            feedback = build_feedback(rows, percent)

            failed = any(r["marks_obtained"] < r["passing_marks"] for r in rows)
            status = "FAIL" if failed else "PASS"

            if percent >= 90: grade = "A+"
            elif percent >= 75: grade = "A"
            elif percent >= 60: grade = "B"
            elif percent >= 50: grade = "C"
            elif percent >= 33: grade = "D"
            else: grade = "F"

            data = {
                "student": student,
                "exam": exam,
                "rows": rows,
                "total": total,
                "percent": round(percent, 2),
                "status": status,
                "grade": grade,
                "feedback": feedback 
            }

    conn.close()

    return render_template(
        "std_view_marks.html",
        exams=exams,
        data=data,
        message=message,
        selected_exam=exam_id
    )



#End Code for View Marks by student Dasboard---



# Start Student Performace feedback builder


def build_feedback(rows, percent):
    messages = []

    # --- Overall feedback ---
    if percent >= 85:
        messages.append("Excellent performance. Keep it up.")
    elif percent >= 70:
        messages.append("Good performance. Aim for excellence.")
    elif percent >= 50:
        messages.append("Average performance. Needs improvement.")
    elif percent >= 33:
        messages.append("Below average. Focus required.")
    else:
        messages.append("Poor performance. Immediate attention needed.")

    # --- Subject feedback ---
    weak = []
    strong = []

    for r in rows:
        m = r["marks_obtained"]
        p = r["passing_marks"]
        name = r["subject"]

        if m < p:
            messages.append(f"Fail in {name} – urgent attention required.")
            weak.append(name)
        elif m >= 80:
            strong.append(name)
        elif m < 60:
            weak.append(name)

    if strong:
        messages.append("Strong subjects: " + ", ".join(strong))

    if weak:
        messages.append("Focus on: " + ", ".join(weak))

    return messages


# Start Student Performace feedback builder

#Code for View and Edit Student Profile self:
@app.route("/stdstudent_profile", methods=["GET", "POST"])
def stdstudent_profile():

    if "student_id" not in session:
        return redirect("/student_login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    std_id = session["student_id"]

    message = None

    if request.method == "POST":

        email = request.form.get("email")
        phone = request.form.get("sphno")
        address = request.form.get("address")
        state = request.form.get("state")
        pincode = request.form.get("pincode")

        # Validation
        if phone and (not phone.isdigit() or len(phone) != 10):
            message = "Phone must be 10 digits!"
        else:
            cursor.execute("""
                UPDATE students_rgd SET email=%s, phone=%s, address=%s, state=%s, pincode=%s WHERE std_id=%s """, (email, phone, address, state, pincode, std_id))

            conn.commit()
            message = "Profile updated successfully!"

    cursor.execute("SELECT * FROM students_rgd WHERE std_id=%s", (std_id,))
    student = cursor.fetchone()

    conn.close()

    return render_template(
        "stdstudent_profile.html",
        student=student,
        message=message
    )

#End View Edit Student Profile..


#Start Student Setting Dashboard--

@app.route("/student_settings", methods=["GET", "POST"])
def student_settings():

    if "student_id" not in session:
        return redirect("/student_login")

    conn = get_db()
    cursor = conn.cursor()

    pwd_changed = session.pop("pwd_changed", None)
    std_id = session["student_id"]
    message = None
    msg_type = None  # success / danger / warning

    if request.method == "POST":

        current_pwd = request.form.get("current_password")
        new_pwd = request.form.get("new_password")
        confirm_pwd = request.form.get("confirm_password")

        # Fetch existing password hash
        cursor.execute("SELECT std_password FROM students_rgd WHERE std_id=%s", (std_id,))
        row = cursor.fetchone()

        if not row:
            message = "User not found."
            msg_type = "danger"

        #elif not check_password_hash(row["std_password"], current_pwd): #for secure if used hash the need to update during new insertion of pass
        elif row["std_password"] != current_pwd:   #for plain password
            message = "Current password is incorrect."
            msg_type = "danger"

        elif new_pwd != confirm_pwd:
            message = "New password and confirm password do not match."
            msg_type = "warning"

        elif len(new_pwd) < 6:
            message = "Password must be at least 6 characters."
            msg_type = "warning"

        else:
            # new_hash = generate_password_hash(new_pwd)  #This is for Hash password insert in the DB
            # cursor.execute(
            #     "UPDATE students_rgd SET password=%s WHERE std_id=%s",
            #     (new_hash, std_id)

            # )
            # Plain password (temporary)
            cursor.execute(
                "UPDATE students_rgd SET std_password=%s WHERE std_id=%s",
                (new_pwd, std_id)
            )
            conn.commit()

            session["pwd_changed"] = True
            return redirect("/student_settings")

    conn.close()

    return render_template(
        "student_settings.html",
        message=message,
        msg_type=msg_type, pwd_changed=pwd_changed
    )

#End Stuent Setting Dashboard-


#Start Stduent view assignment-


@app.route("/student_assignments")
def student_assignments():

    if "student_id" not in session:
        return redirect("/student_login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # ---------------- STUDENT INFO ----------------

    cursor.execute("""
        SELECT *
        FROM students_rgd
        WHERE std_id=%s
    """, (session["student_id"],))

    student = cursor.fetchone()

    class_id = student["class_id"]

    # ---------------- FETCH ASSIGNMENTS ----------------

    cursor.execute("""
        SELECT *
        FROM assignments
        WHERE class_id=%s
        ORDER BY id DESC
    """, (class_id,))

    assignments = cursor.fetchall()

    conn.close()

    return render_template(
        "student_assignments.html",

        student=student,
        assignments=assignments
    )


#End Stduent view assignment-






# #start Student view class and assigned teacher-- #commented because rendering it from stddashboard route



# @app.route("/student_class_details")
# def student_class_details():

#     if "student_id" not in session:
#         return redirect("/student_login")

#     conn = get_db()
#     cursor = conn.cursor(pymysql.cursors.DictCursor)

#     # ---------------- STUDENT INFO ----------------

#     cursor.execute("""
#         SELECT
#             s.*,
#             c.class_name

#         FROM students_rgd s

#         LEFT JOIN classes c
#             ON s.class_id = c.id

#         WHERE s.std_id=%s
#     """, (session["student_id"],))

#     student = cursor.fetchone()

#     # ---------------- SUBJECTS OF CLASS ----------------

#     cursor.execute("""
#         SELECT *
#         FROM subjects
#         WHERE class_id=%s
#     """, (student["class_id"],))

#     subjects = cursor.fetchall()

#     # ---------------- TEACHERS OF CLASS ----------------

#     cursor.execute("""
#         SELECT *
#         FROM teachers
#         WHERE class_id=%s
#     """, (student["class_id"],))

#     teachers = cursor.fetchall()

#     conn.close()

#     return render_template(
#         "student_class_details.html",
#         student=student,
#         subjects=subjects,
#         teachers=teachers
#     )


#End Student view class and assigned teacher--





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




#Code Start for Teacher dashboard Route... After success login below route will call


@app.route("/teacher_dashboard")
def teacher_dashboard():

    if "teacher_id" not in session:
        return redirect("/teacher_login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM teachers
        WHERE tchr_id=%s
    """, (session["teacher_id"],))

    teacher = cursor.fetchone()

    conn.close()

    return render_template(
        "teacher_dashboard.html",
        teacher=teacher
    )



#Code End for Teacher dashboard Route... After success login below route will call


#Update Teacher Profile:

@app.route("/teacher_profile", methods=["GET", "POST"])
def teacher_profile():

    if "teacher_id" not in session:
        return redirect("/teacher_login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    message = None
    msg_type = None

    if request.method == "POST":

        email = request.form.get("email").strip()
        phone = request.form.get("phone").strip()

        # Validation
        if not phone.isdigit() or len(phone) != 10:

            message = "Phone number must be exactly 10 digits."
            msg_type = "danger"

        else:

            cursor.execute("""
                UPDATE teachers

                SET
                    email=%s,
                    phone=%s

                WHERE tchr_id=%s
            """, (
                email,
                phone,
                session["teacher_id"]
            ))

            conn.commit()

            message = "Profile updated successfully!"
            msg_type = "success"

    # FETCH TEACHER
    cursor.execute("""
        SELECT *
        FROM teachers
        WHERE tchr_id=%s
    """, (session["teacher_id"],))

    teacher = cursor.fetchone()

    conn.close()

    return render_template(
        "teacher_profile.html",

        teacher=teacher,

        message=message,
        msg_type=msg_type
    )





#start teacher view class and subject--

@app.route("/teacher_my_details")
def teacher_my_details():

    if "teacher_id" not in session:
        return redirect("/teacher_login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT *
        FROM teachers
        WHERE tchr_id=%s
    """, (session["teacher_id"],))

    teacher = cursor.fetchone()

    conn.close()

    return render_template(
        "teacher_my_details.html",
        teacher=teacher
    )



#end teacher view class and subject--




# Start code for Teacher Analytics Dashboard


@app.route("/teacher_analytics")
def teacher_analytics():

    if "teacher_id" not in session:
        return redirect("/teacher_login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    teacher_id = session["teacher_id"]

    # ---------------- TEACHER INFO ----------------

    cursor.execute("""
        SELECT *
        FROM teachers
        WHERE tchr_id=%s
    """, (teacher_id,))

    teacher = cursor.fetchone()

    class_id = teacher["class_id"]

    # Teacher subjects
    teacher_subjects = [
        s.strip()
        for s in teacher["subject"].split(",")
    ]

    # Dynamic placeholders
    placeholders = ",".join(["%s"] * len(teacher_subjects))

    # ---------------- TOTAL STUDENTS ----------------

    cursor.execute("""
        SELECT COUNT(*) AS total_students
        FROM students_rgd
        WHERE class_id=%s
    """, (class_id,))

    total_students = cursor.fetchone()["total_students"]

    # ---------------- PASS PERCENTAGE ----------------

    query = f"""
        SELECT
            COUNT(*) AS total,

            SUM(
                CASE
                    WHEN m.marks_obtained >= s.passing_marks
                    THEN 1
                    ELSE 0
                END
            ) AS passed

        FROM marks m

        JOIN subjects s
            ON m.subject_id = s.id

        JOIN students_rgd st
            ON m.std_id = st.std_id

        WHERE st.class_id=%s
        AND s.name IN ({placeholders})
    """

    params = [class_id] + teacher_subjects

    cursor.execute(query, params)

    pass_data = cursor.fetchone()

    total = pass_data["total"] or 0
    passed = pass_data["passed"] or 0

    pass_percent = round((passed / total) * 100, 2) if total else 0

    # ---------------- AVERAGE MARKS ----------------

    query = f"""
        SELECT AVG(m.marks_obtained) AS avg_marks

        FROM marks m

        JOIN subjects s
            ON m.subject_id = s.id

        JOIN students_rgd st
            ON m.std_id = st.std_id

        WHERE st.class_id=%s
        AND s.name IN ({placeholders})
    """

    cursor.execute(query, params)

    avg_marks = cursor.fetchone()["avg_marks"] or 0

    avg_marks = round(avg_marks, 2)

    # ---------------- TOP SCORE ----------------

    query = f"""
        SELECT MAX(m.marks_obtained) AS top_score

        FROM marks m

        JOIN subjects s
            ON m.subject_id = s.id

        JOIN students_rgd st
            ON m.std_id = st.std_id

        WHERE st.class_id=%s
        AND s.name IN ({placeholders})
    """

    cursor.execute(query, params)

    top_score = cursor.fetchone()["top_score"] or 0

    # ---------------- TOPPER ----------------

    query = f"""
        SELECT
            st.first_name,
            st.last_name,

            SUM(m.marks_obtained) AS total_marks

        FROM marks m

        JOIN subjects s
            ON m.subject_id = s.id

        JOIN students_rgd st
            ON m.std_id = st.std_id

        WHERE st.class_id=%s
        AND s.name IN ({placeholders})

        GROUP BY st.std_id

        ORDER BY total_marks DESC

        LIMIT 1
    """

    cursor.execute(query, params)

    topper = cursor.fetchone()

    # ---------------- WEAK STUDENTS ----------------

    query = f"""
        SELECT COUNT(DISTINCT st.std_id) AS weak_students

        FROM marks m

        JOIN subjects s
            ON m.subject_id = s.id

        JOIN students_rgd st
            ON m.std_id = st.std_id

        WHERE st.class_id=%s
        AND s.name IN ({placeholders})
        AND m.marks_obtained < s.passing_marks
    """

    cursor.execute(query, params)

    weak_students = cursor.fetchone()["weak_students"]

    # ---------------- SUBJECT AVG CHART ----------------

    query = f"""
        SELECT
            s.name,

            AVG(m.marks_obtained) AS avg_marks

        FROM marks m

        JOIN subjects s
            ON m.subject_id = s.id

        JOIN students_rgd st
            ON m.std_id = st.std_id

        WHERE st.class_id=%s
        AND s.name IN ({placeholders})

        GROUP BY s.id
    """

    cursor.execute(query, params)

    chart_data = cursor.fetchall()

    subject_labels = [
        row["name"]
        for row in chart_data
    ]

    subject_averages = [
        round(row["avg_marks"], 2)
        for row in chart_data
    ]

    conn.close()

    return render_template(
        "teacher_analytics.html",

        total_students=total_students,
        pass_percent=pass_percent,
        avg_marks=avg_marks,
        top_score=top_score,
        topper=topper,
        weak_students=weak_students,

        subject_labels=subject_labels,
        subject_averages=subject_averages
    )



# End code for Teacher Analytics Dashboard




#Start code for teacher assignment



import os
from werkzeug.utils import secure_filename


@app.route("/teacher_assignments", methods=["GET", "POST"])
def teacher_assignments():

    if "teacher_id" not in session:
        return redirect("/teacher_login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    teacher_id = session["teacher_id"]

    # ---------------- TEACHER INFO ----------------

    cursor.execute("""
        SELECT *
        FROM teachers
        WHERE tchr_id=%s
    """, (teacher_id,))

    teacher = cursor.fetchone()

    message = None
    msg_type = None

    if request.method == "POST":

        title = request.form.get("title")
        description = request.form.get("description")
        due_date = request.form.get("due_date")

        subject_name = request.form.get("subject_name")

        class_id = teacher["class_id"]

        # ---------------- FILE UPLOAD ----------------

        file = request.files.get("assignment_file")

        filename = ""

        if file and file.filename != "":

            filename = secure_filename(file.filename)

            os.makedirs(
                "static/uploads/assignments",
                exist_ok=True
            )

            file.save(
                os.path.join(
                    "static/uploads/assignments",
                    filename
                )
            )

        # ---------------- INSERT ----------------

        cursor.execute("""
            INSERT INTO assignments
            (
                teacher_id,
                class_id,
                subject_name,
                title,
                description,
                due_date,
                file_name
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            teacher_id,
            class_id,
            subject_name,
            title,
            description,
            due_date,
            filename
        ))

        conn.commit()

        message = "Assignment uploaded successfully!"
        msg_type = "success"

    # Teacher subjects
    subjects = [
        s.strip()
        for s in teacher["subject"].split(",")
    ]

    # ---------------- RECENT ASSIGNMENTS ----------------

    cursor.execute("""
        SELECT *
        FROM assignments
        WHERE teacher_id=%s
        ORDER BY id DESC
    """, (teacher_id,))

    assignments = cursor.fetchall()

    conn.close()

    return render_template(
        "teacher_assignments.html",

        teacher=teacher,
        subjects=subjects,

        assignments=assignments,

        message=message,
        msg_type=msg_type
    )







# ================= UPDATE ASSIGNMENT =================

@app.route("/teacher_update_assignment/<int:id>", methods=["POST"])
def teacher_update_assignment(id):

    if "teacher_id" not in session:
        return redirect("/teacher_login")

    conn = get_db()
    cursor = conn.cursor()

    title = request.form.get("title")
    description = request.form.get("description")
    due_date = request.form.get("due_date")
    subject_name = request.form.get("subject_name")

    cursor.execute("""
        UPDATE assignments

        SET
            title=%s,
            description=%s,
            due_date=%s,
            subject_name=%s

        WHERE id=%s
    """, (
        title,
        description,
        due_date,
        subject_name,
        id
    ))

    conn.commit()
    conn.close()

    return redirect("/teacher_assignments")


# ================= DELETE ASSIGNMENT =================

@app.route("/teacher_delete_assignment/<int:id>")
def teacher_delete_assignment(id):

    if "teacher_id" not in session:
        return redirect("/teacher_login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM assignments
        WHERE id=%s
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/teacher_assignments")







#End Code for teacher assignment


#Start Insert new marks only for student by teachers


@app.route("/teacher_add_marks", methods=["GET", "POST"])
def teacher_add_marks():

    if "teacher_id" not in session:
        return redirect("/teacher_login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    message = None
    msg_type = None

    # ---------------- DROPDOWNS ----------------

    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()

    cursor.execute("SELECT * FROM exams")
    exams = cursor.fetchall()

    students = []
    subjects = []
    existing_marks = {}

    # ---------------- GET VALUES ----------------

    selected_class = request.args.get("class_id")
    selected_student = request.args.get("std_id")
    selected_exam = request.args.get("exam_id")

    # ---------------- LOAD STUDENTS & SUBJECTS ----------------

    if selected_class:

        cursor.execute(
            "SELECT * FROM students_rgd WHERE class_id=%s",
            (selected_class,)
        )

        students = cursor.fetchall()

        cursor.execute(
            "SELECT * FROM subjects WHERE class_id=%s",
            (selected_class,)
        )

        subjects = cursor.fetchall()

    # ---------------- LOAD EXISTING MARKS ----------------

    if selected_student and selected_exam:

        cursor.execute("""
            SELECT subject_id, marks_obtained
            FROM marks
            WHERE std_id=%s
            AND exam_id=%s
        """, (
            selected_student,
            selected_exam
        ))

        rows = cursor.fetchall()

        # Convert to dictionary
        for row in rows:
            existing_marks[row["subject_id"]] = row["marks_obtained"]

    # ---------------- INSERT MARKS ----------------

    if request.method == "POST":

        std_id = request.form.get("std_id")
        exam_id = request.form.get("exam_id")

        subject_ids = request.form.getlist("subject_id")
        marks_list = request.form.getlist("marks")

        already_exists = False

        for subject_id, marks in zip(subject_ids, marks_list):

            # CHECK EXISTING
            cursor.execute("""
                SELECT id FROM marks
                WHERE std_id=%s
                AND exam_id=%s
                AND subject_id=%s
            """, (
                std_id,
                exam_id,
                subject_id
            ))

            existing = cursor.fetchone()

            # If exists → skip
            if existing:
                already_exists = True
                continue

            # Validation
            if marks.strip() == "":
                continue

            marks = int(marks)

            if marks < 0 or marks > 100:
                continue

            # INSERT
            cursor.execute("""
                INSERT INTO marks
                (
                    std_id,
                    exam_id,
                    subject_id,
                    marks_obtained
                )
                VALUES (%s,%s,%s,%s)
            """, (
                std_id,
                exam_id,
                subject_id,
                marks
            ))

        conn.commit()

        if already_exists:
            message = "Some marks already exist. Teacher cannot edit them."
            msg_type = "warning"
        else:
            message = "Marks uploaded successfully!"
            msg_type = "success"

    conn.close()

    return render_template(
        "teacher_add_marks.html",
        classes=classes,
        exams=exams,
        students=students,
        subjects=subjects,
        existing_marks=existing_marks,
        selected_class=selected_class,
        selected_student=selected_student,
        selected_exam=selected_exam,
        message=message,
        msg_type=msg_type
    )


#End Insert new marks only for student by teachers


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



# Start Admin view Students Marksheet

@app.route("/admin_marks_view", methods=["GET", "POST"])
def admin_marks_view():

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    if request.method == "POST":

        std_id = request.form.get("std_id")
        exam_id = request.form.get("exam_id")

        return redirect(f"/admin_marks_result/{std_id}/{exam_id}")

    # GET → load dropdowns
    cursor.execute("SELECT id, class_name FROM classes")
    classes = cursor.fetchall()

    cursor.execute("SELECT id, name FROM exams WHERE status='Active'")
    exams = cursor.fetchall()

    return render_template("admin_marks_view.html", classes=classes, exams=exams)





@app.route("/admin_marks_result/<int:std_id>/<int:exam_id>")
def admin_marks_result(std_id, exam_id):

    # 🔒 Admin authentication
    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # =====================
    # FETCH STUDENT
    # =====================
    cursor.execute("""
        SELECT first_name, last_name, reg_id
        FROM students_rgd
        WHERE std_id=%s
    """, (std_id,))
    student = cursor.fetchone()

    if not student:
        flash("No marks found. Please enter marks first.", "warning")
        return redirect("/admin_marks_view")

    # =====================
    # FETCH EXAM
    # =====================
    cursor.execute("""
        SELECT id, name
        FROM exams
        WHERE id=%s
    """, (exam_id,))
    exam = cursor.fetchone()

    if not exam:
        flash("Exam not found!", "danger")
        return redirect("/admin_marks_view")

    # =====================
    # FETCH MARKS
    # =====================
    cursor.execute("""
        SELECT s.name AS subject,
               s.passing_marks,
               m.marks_obtained
        FROM marks m
        JOIN subjects s ON m.subject_id = s.id
        WHERE m.std_id=%s AND m.exam_id=%s
        ORDER BY s.name
    """, (std_id, exam_id))

    rows = cursor.fetchall()

    # =====================
    # 🔴 VALIDATION (IMPORTANT)
    # =====================
    if not rows:
        flash("No marks found. Please enter marks first.", "warning")
        return redirect("/admin_marks_view")

    # =====================
    # CALCULATIONS
    # =====================
    total = sum(r["marks_obtained"] for r in rows)
    max_total = len(rows) * 100

    percent = (total / max_total * 100) if max_total else 0

    # Subject-wise fail check
    failed = any(r["marks_obtained"] < r["passing_marks"] for r in rows)
    status = "FAIL" if failed else "PASS"

    # Grade logic
    if percent >= 90:
        grade = "A+"
    elif percent >= 75:
        grade = "A"
    elif percent >= 60:
        grade = "B"
    elif percent >= 50:
        grade = "C"
    elif percent >= 33:
        grade = "D"
    else:
        grade = "F"

    conn.close()

    # =====================
    # RENDER RESULT PAGE
    # =====================
    return render_template(
        "admin_marks_result.html",
        student=student,
        exam=exam,
        rows=rows,
        total=total,
        percent=round(percent, 2),
        status=status,
        grade=grade
    )


# End Admin view Students Marksheet





# Start Admin Notice- Insert, Update, delete

# Route Nocice

@app.route("/admin_notices")
def admin_notices():

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT * FROM notices
        ORDER BY priority DESC, notice_date DESC
    """)

    notices = cursor.fetchall()
    conn.close()

    return render_template("admin_notices.html", notices=notices)



#Insert Notice-

@app.route("/add_notice", methods=["POST"])
def add_notice():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO notices
        (title, description, category, notice_date, expiry_date, priority, image_url)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        request.form.get("title"),
        request.form.get("description"),
        request.form.get("category"),
        request.form.get("notice_date"),
        request.form.get("expiry_date") or None,
        request.form.get("priority") or 0,
        request.form.get("image_url")
    ))

    conn.commit()
    conn.close()

    return redirect("/admin_notices")


#Delete Notice-

@app.route("/delete_notice/<int:id>")
def delete_notice(id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM notices WHERE id=%s", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin_notices")


#Update Notice-
@app.route("/edit_notice", methods=["POST"])
def edit_notice():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE notices
        SET title=%s,
            description=%s,
            category=%s,
            notice_date=%s,
            expiry_date=%s,
            priority=%s,
            image_url=%s
        WHERE id=%s
    """, (
        request.form.get("title"),
        request.form.get("description"),
        request.form.get("category"),
        request.form.get("notice_date"),
        request.form.get("expiry_date") or None,
        request.form.get("priority") or 0,
        request.form.get("image_url"),
        request.form.get("id")
    ))

    conn.commit()
    conn.close()

    return redirect("/admin_notices")



# End Admin Notice- Insert, Update, delete


# Start Public View Notice.html page #

@app.route("/notices")
def notices():

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT * FROM notices
        WHERE status='Active'
        AND (expiry_date IS NULL OR expiry_date >= CURDATE())
        ORDER BY priority DESC, notice_date DESC
    """)

    notices = cursor.fetchall()
    conn.close()

    return render_template("notices.html", notices=notices)

# End Public View Notice




# Start Admin Analytics Dashboard#

@app.route("/admin_analytics")
def admin_analytics():

    if "admin_id" not in session:
        return redirect("/admin_login")

    class_id = request.args.get("class_id")
    exam_id = request.args.get("exam_id")

    conn = get_db()
    cursor = conn.cursor()

    # -----------------------
    # LOAD FILTER DATA
    # -----------------------
    cursor.execute("SELECT id, class_name FROM classes")
    classes = cursor.fetchall()

    cursor.execute("SELECT id, name FROM exams WHERE status='Active'")
    exams = cursor.fetchall()

    # Default outputs
    total_students = pass_count = fail_count = 0
    pass_percent = 0
    subject_data = []
    weak_subject = top_subject = None
    performance = "N/A"
    top_students = []
    topper = None

    # -----------------------
    # APPLY FILTER
    # -----------------------
    if class_id:

        # Total students in class
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM students_rgd
            WHERE class_id=%s
        """, (class_id,))
        total_students = cursor.fetchone()["total"]

        # Pass / Fail (exam-wise if selected)
        query = """
            SELECT m.std_id,
                   SUM(CASE WHEN m.marks_obtained < s.passing_marks THEN 1 ELSE 0 END) AS fails
            FROM marks m
            JOIN subjects s ON m.subject_id = s.id
            JOIN students_rgd st ON st.std_id = m.std_id
            WHERE st.class_id=%s
        """
        params = [class_id]

        if exam_id:
            query += " AND m.exam_id=%s"
            params.append(exam_id)

        query += " GROUP BY m.std_id"

        cursor.execute(query, params)
        results = cursor.fetchall()

        pass_count = sum(1 for r in results if r["fails"] == 0)
        fail_count = sum(1 for r in results if r["fails"] > 0)

        pass_percent = round((pass_count / total_students) * 100, 2) if total_students else 0

        # -----------------------
        # SUBJECT AVERAGE
        # -----------------------
        query = """
            SELECT s.name, AVG(m.marks_obtained) AS avg_marks
            FROM marks m
            JOIN subjects s ON m.subject_id = s.id
            JOIN students_rgd st ON st.std_id = m.std_id
            WHERE st.class_id=%s
        """
        params = [class_id]

        if exam_id:
            query += " AND m.exam_id=%s"
            params.append(exam_id)

        query += " GROUP BY s.name"

        cursor.execute(query, params)
        subject_data = cursor.fetchall()

        # Weak & Top subject
        if subject_data:
            weak_subject = min(subject_data, key=lambda x: x["avg_marks"])
            top_subject = max(subject_data, key=lambda x: x["avg_marks"])

        # -----------------------
        # PERFORMANCE TAG
        # -----------------------
        if pass_percent >= 75:
            performance = "Excellent"
        elif pass_percent >= 50:
            performance = "Average"
        else:
            performance = "Needs Improvement"

        # -----------------------
        # RANK SYSTEM (EXAM-WISE)
        # -----------------------
        if exam_id:
            cursor.execute("""
                SELECT st.first_name,
                       SUM(m.marks_obtained) AS total_marks
                FROM marks m
                JOIN students_rgd st ON m.std_id = st.std_id
                WHERE st.class_id=%s AND m.exam_id=%s
                GROUP BY m.std_id
                ORDER BY total_marks DESC
                LIMIT 5
            """, (class_id, exam_id))

            top_students = cursor.fetchall()

            for i, s in enumerate(top_students, start=1):
                s["rank"] = i

            topper = top_students[0] if top_students else None

    conn.close()

    return render_template(
        "admin_analytics.html",
        classes=classes,
        exams=exams,
        selected_class=class_id,
        selected_exam=exam_id,
        total_students=total_students,
        pass_percent=pass_percent,
        pass_count=pass_count,
        fail_count=fail_count,
        subject_data=subject_data,
        weak_subject=weak_subject,
        top_subject=top_subject,
        performance=performance,
        top_students=top_students,
        topper=topper
    )

# end Admin Analytics Dashboard#


#Start Admin can add teacher

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_IMAGE_SIZE = 2 * 1024 * 1024   # 2MB


@app.route("/admadd_teacher", methods=["GET", "POST"])
def admadd_teacher():

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # ---------------- FETCH CLASSES ----------------
    cursor.execute("SELECT * FROM classes")
    classes = cursor.fetchall()

    # ---------------- FETCH SUBJECTS ----------------
    cursor.execute("SELECT * FROM subjects")
    subjects = cursor.fetchall()

    message = None
    msg_type = None

    if request.method == "POST":

        first_name = request.form.get("first_name").strip()
        last_name = request.form.get("last_name").strip()
        dob = request.form.get("tchr_dob")
        email = request.form.get("email").strip()
        phone = request.form.get("phone").strip()

        class_id = request.form.get("class_id")

        # Get class name from DB
        cursor.execute(
            "SELECT class_name FROM classes WHERE id=%s",
            (class_id,)
        )

        class_row = cursor.fetchone()
        class_name = class_row["class_name"] if class_row else ""

        # ---------------- MULTIPLE SUBJECTS ----------------
        subjects_list = request.form.getlist("subjects")

        # Convert list → comma string
        subject_string = ",".join(subjects_list)

        # ---------------- PASSWORD ----------------
        password = request.form.get("teacher_password")

        # Auto password if blank
        if not password:
            password = f"{first_name}@{phone[-4:]}"

        # ---------------- VALIDATION ----------------

        # Duplicate Email Check
        cursor.execute(
            "SELECT tchr_id FROM teachers WHERE email=%s",
            (email,)
        )

        existing = cursor.fetchone()

        if existing:
            message = "Email already exists!"
            msg_type = "danger"

        elif not phone.isdigit() or len(phone) != 10:
            message = "Phone must be exactly 10 digits!"
            msg_type = "warning"

        elif len(subjects_list) == 0:
            message = "Please select at least one subject!"
            msg_type = "warning"

        else:

            # ---------------- IMAGE UPLOAD ----------------
            image = request.files.get("tchr_img")
            filename = ""

            if image and image.filename != "":

                # IMAGE SIZE VALIDATION
                image.seek(0, os.SEEK_END)
                size = image.tell()
                image.seek(0)

                if size > MAX_IMAGE_SIZE:

                    conn.close()

                    return render_template(
                        "admadd_teacher.html",
                        classes=classes,
                        subjects=subjects,
                        message="Image size must be less than 2MB!",
                        msg_type="danger"
                    )

                # FILE TYPE VALIDATION
                ext = image.filename.rsplit('.', 1)[-1].lower()

                if ext not in ALLOWED_EXTENSIONS:

                    conn.close()

                    return render_template(
                        "admadd_teacher.html",
                        classes=classes,
                        subjects=subjects,
                        message="Only JPG, JPEG, PNG files allowed!",
                        msg_type="danger"
                    )

                # SECURE FILE NAME
                filename = secure_filename(image.filename)

                # CREATE FOLDER IF NOT EXISTS
                os.makedirs("static/uploads/teachers", exist_ok=True)

                # SAVE IMAGE
                image.save(
                    os.path.join(
                        "static/uploads/teachers",
                        filename
                    )
                )

            # ---------------- INSERT TEACHER ----------------

            cursor.execute("""
                INSERT INTO teachers
                (
                    first_name,
                    last_name,
                    tchr_dob,
                    email,
                    phone,
                    class_id,
                    class,
                    subject,
                    teacher_password,
                    tchr_img
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                first_name,
                last_name,
                dob,
                email,
                phone,
                class_id,
                class_name,
                subject_string,
                password,
                filename
            ))

            conn.commit()

            message = f"Teacher registered successfully! Default Password: {password}"
            msg_type = "success"

    conn.close()

    return render_template(
        "admadd_teacher.html",
        classes=classes,
        subjects=subjects,
        message=message,
        msg_type=msg_type
    )

#End Admin can add teacher


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

# ================= EDIT TEACHER =================

@app.route("/adm_edit_teacher/<int:tchr_id>", methods=["GET", "POST"])
def adm_edit_teacher(tchr_id):

    if "admin_id" not in session:
        return redirect("/admin_login")

    conn = get_db()

    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:

        # ---------------- FETCH CLASSES ----------------

        cursor.execute("SELECT * FROM classes")

        classes = cursor.fetchall()

        if request.method == "POST":

            fname = request.form.get("fname").strip()

            lname = request.form.get("lname").strip()

            email = request.form.get("email").strip()

            phone = request.form.get("phone").strip()

            class_id = request.form.get("class_id")

            class_name = request.form.get("class_name")

            subjects = request.form.getlist("subject")

            subject_string = ",".join(subjects)

            # ---------------- VALIDATION ----------------

            if not phone.isdigit() or len(phone) != 10:

                flash(
                    "Phone number must be exactly 10 digits.",
                    "danger"
                )

                return redirect(
                    f"/adm_edit_teacher/{tchr_id}"
                )

            # ---------------- DUPLICATE EMAIL ----------------

            cursor.execute("""
                SELECT *
                FROM teachers
                WHERE email=%s
                AND tchr_id!=%s
            """, (
                email,
                tchr_id
            ))

            if cursor.fetchone():

                flash(
                    "Email already exists!",
                    "danger"
                )

                return redirect(
                    f"/adm_edit_teacher/{tchr_id}"
                )

            # ---------------- IMAGE UPDATE ----------------

            cursor.execute("""
                SELECT tchr_img
                FROM teachers
                WHERE tchr_id=%s
            """, (tchr_id,))

            old_teacher = cursor.fetchone()

            teacher_img = old_teacher["tchr_img"]

            file = request.files.get("tchr_img")

            if file and file.filename != "":

                filename = secure_filename(file.filename)

                os.makedirs(
                    "static/uploads/teachers",
                    exist_ok=True
                )

                file.save(
                    os.path.join(
                        "static/uploads/teachers",
                        filename
                    )
                )

                teacher_img = filename

            # ---------------- UPDATE ----------------

            cursor.execute("""
                UPDATE teachers

                SET
                    first_name=%s,
                    last_name=%s,
                    email=%s,
                    phone=%s,
                    class_id=%s,
                    class=%s,
                    subject=%s,
                    tchr_img=%s

                WHERE tchr_id=%s
            """, (
                fname,
                lname,
                email,
                phone,
                class_id,
                class_name,
                subject_string,
                teacher_img,
                tchr_id
            ))

            conn.commit()

            flash(
                "Teacher updated successfully!",
                "success"
            )

            return redirect(
                f"/adm_edit_teacher/{tchr_id}"
            )

        # ---------------- FETCH TEACHER ----------------

        cursor.execute("""
            SELECT *
            FROM teachers
            WHERE tchr_id=%s
        """, (tchr_id,))

        teacher = cursor.fetchone()

        return render_template(
            "adm_edit_teacher.html",

            teacher=teacher,
            classes=classes
        )

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