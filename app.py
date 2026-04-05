from flask import Flask, render_template, request, redirect, session
import pandas as pd
import sqlite3
from sklearn.linear_model import LogisticRegression
import re

app = Flask(__name__)
app.secret_key = "secret"

# ---------------- DATABASE ----------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT,
    section TEXT,
    question TEXT,
    answer TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    section TEXT,
    attendance INTEGER,
    study_hours INTEGER,
    unit1 INTEGER,
    unit2 INTEGER,
    endsem INTEGER
)
""")

conn.commit()

# ---------------- PASSWORD POLICY ----------------
def valid_password(pwd):
    if len(pwd) < 6:
        return False
    if not re.search("[A-Z]", pwd):
        return False
    if not re.search("[0-9]", pwd):
        return False
    return True

# ---------------- MODEL ----------------
data = pd.read_csv("student_data.csv")
X = data[['hours','attendance','marks']]
y = data['result']

model = LogisticRegression()
model.fit(X, y)

# ---------------- LOGIN ----------------
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (user,pwd))
        if cursor.fetchone():
            session['user'] = user
            return redirect('/dashboard')
        else:
            return render_template("login.html", msg="Invalid Login")

    return render_template('login.html')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        section = request.form.get('section')
        question = request.form.get('question')
        answer = request.form.get('answer')

        if not valid_password(pwd):
            return render_template("register.html",
                                   msg="Password must have 6+ chars, 1 Capital, 1 Number")

        cursor.execute("SELECT * FROM users WHERE username=?", (user,))
        if cursor.fetchone():
            return render_template("register.html", msg="User already exists!")

        cursor.execute("INSERT INTO users VALUES (?,?,?,?,?)",
                       (user, pwd, section, question, answer))
        conn.commit()

        return redirect('/')

    return render_template('register.html')

# ---------------- FORGOT PASSWORD ----------------
@app.route('/forgot', methods=['GET','POST'])
def forgot():
    if request.method == 'POST':
        user = request.form.get('username')

        cursor.execute("SELECT question FROM users WHERE username=?", (user,))
        data = cursor.fetchone()

        if not data:
            return render_template("forgot.html", msg="User not found")

        session['reset_user'] = user
        return render_template("verify_answer.html", question=data[0])

    return render_template("forgot.html")

# ---------------- VERIFY ANSWER ----------------
@app.route('/verify_answer', methods=['POST'])
def verify_answer():
    answer = request.form.get('answer')
    user = session.get('reset_user')

    cursor.execute("SELECT answer FROM users WHERE username=?", (user,))
    real_answer = cursor.fetchone()[0]

    if answer.lower() == real_answer.lower():
        return render_template("reset.html")
    else:
        return "Wrong Answer"

# ---------------- RESET PASSWORD ----------------
@app.route('/reset', methods=['POST'])
def reset():
    new_pwd = request.form.get('password')
    user = session.get('reset_user')

    cursor.execute("UPDATE users SET password=? WHERE username=?", (new_pwd, user))
    conn.commit()

    return redirect('/')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    user = session['user']

    cursor.execute("SELECT section FROM users WHERE username=?", (user,))
    section = cursor.fetchone()[0]

    students = pd.read_sql_query(
        "SELECT * FROM students WHERE section=?",
        conn,
        params=(section,)
    )

    return render_template("dashboard.html",
                           students=students.to_dict(orient='records'),
                           section=section)

# ---------------- ADD STUDENT ----------------
@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form['name']
    section = request.form['section']

    cursor.execute("""
    INSERT INTO students(name,section,attendance,study_hours,unit1,unit2,endsem)
    VALUES (?,?,0,0,0,0,0)
    """, (name, section))

    conn.commit()
    return redirect('/dashboard')

# ---------------- UPDATE + PREDICT ----------------
@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    attendance = int(request.form['attendance'])
    study_hours = int(request.form['study_hours'])
    unit1 = int(request.form['unit1'])
    unit2 = int(request.form['unit2'])
    endsem = int(request.form['endsem'])

    cursor.execute("""
    UPDATE students 
    SET attendance=?, study_hours=?, unit1=?, unit2=?, endsem=?
    WHERE id=?
    """, (attendance, study_hours, unit1, unit2, endsem, id))

    conn.commit()

    avg_marks = (unit1 + unit2 + endsem) / 3

    pred = model.predict([[study_hours, attendance, avg_marks]])
    result = "PASS" if pred[0] == 1 else "FAIL"

    return redirect(f"/dashboard?result_{id}={result}")

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)