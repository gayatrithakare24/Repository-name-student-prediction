import sqlite3
from flask import Flask, render_template, request, redirect, session, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from model import predict_result   # 🔥 ML IMPORT

app = Flask(__name__)
app.secret_key = "secret"

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

# USERS
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT,
question TEXT,
answer TEXT
)
""")

# STUDENTS
cursor.execute("""
CREATE TABLE IF NOT EXISTS students(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
teacher TEXT,
study REAL,
attendance REAL,
m1 REAL,
m2 REAL,
m3 REAL,
result TEXT,
score REAL
)
""")

conn.commit()

# LOGIN
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        if cursor.fetchone():
            session['user'] = u
            return redirect('/dashboard')
    return render_template('login.html')

# REGISTER
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        cursor.execute("INSERT INTO users VALUES (?,?,?,?)",
                       (request.form['username'],request.form['password'],
                        request.form['question'],request.form['answer']))
        conn.commit()
        return redirect('/')
    return render_template('register.html')

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    user = session['user']
    cursor.execute("SELECT * FROM students WHERE teacher=? ORDER BY score DESC", (user,))
    students = cursor.fetchall()
    return render_template('dashboard.html', students=students, tips={})

# ADD
@app.route('/add_student', methods=['POST'])
def add():
    cursor.execute("""
    INSERT INTO students(name, teacher, study, attendance, m1, m2, m3, result, score)
    VALUES (?, ?,0,0,0,0,0,'',0)
    """, (request.form['name'], session['user']))
    conn.commit()
    return redirect('/dashboard')

# DELETE
@app.route('/delete/<int:id>')
def delete(id):
    cursor.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    return redirect('/dashboard')

# CSV UPLOAD
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    data = file.read().decode("utf-8").splitlines()

    for line in data:
        name = line.strip()
        if name:
            cursor.execute("""
            INSERT INTO students(name, teacher, study, attendance, m1, m2, m3, result, score)
            VALUES (?, ?,0,0,0,0,0,'',0)
            """, (name, session['user']))

    conn.commit()
    return redirect('/dashboard')

# 🔥 PREDICT USING ML
@app.route('/predict', methods=['POST'])
def predict():
    study = float(request.form['study'])
    att = float(request.form['att'])
    m1 = float(request.form['m1'])
    m2 = float(request.form['m2'])
    m3 = float(request.form['m3'])
    sid = int(request.form['id'])

    ut_avg = (m1 + m2) / 2

    # 🔥 ML prediction integration with flask
    result_ml = predict_result(study, att, ut_avg, m3)

    status = "PASS" if result_ml == 1 else "FAIL"

    # Level (for graph)
    if m3 >= 50:
        level = "EXCELLENT"
    elif m3 >= 30:
        level = "AVERAGE"
    else:
        level = "WEAK"

    final_result = f"{level} ({status})"

    # Score (for ranking)
    score = (ut_avg/20)*30 + (m3/60)*50 + (att/100)*10 + (study/5)*10

    cursor.execute("""
    UPDATE students SET study=?,attendance=?,m1=?,m2=?,m3=?,result=?,score=?
    WHERE id=?
    """,(study,att,m1,m2,m3,final_result,score,sid))

    conn.commit()

    cursor.execute("SELECT * FROM students WHERE teacher=? ORDER BY score DESC", (session['user'],))
    students = cursor.fetchall()

    return render_template('dashboard.html', students=students, tips={})

# PDF
@app.route('/pdf/<int:id>')
def pdf(id):
    cursor.execute("SELECT * FROM students WHERE id=?", (id,))
    s = cursor.fetchone()

    file = "report.pdf"
    doc = SimpleDocTemplate(file)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph(f"Name: {s[1]}", styles['Normal']))
    content.append(Paragraph(f"Result: {s[8]}", styles['Normal']))
    content.append(Paragraph(f"Score: {s[9]:.2f}", styles['Normal']))
    content.append(Spacer(1,20))

    doc.build(content)
    return send_file(file, as_attachment=True)

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

app.run(debug=True)