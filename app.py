from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

#Calling the Student login form
@app.route("/student_login")
def student_login():
    return render_template("student_login.html")




if __name__ == "__main__":
    app.run(debug=True)