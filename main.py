import pandas as pd
import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import matplotlib.pyplot as plt

# ---------------- DATABASE ----------------
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password TEXT
)
""")
conn.commit()

# ---------------- LOAD DATA ----------------
data = pd.read_csv("student_data.csv")

def train_model():
    global model, data
    X = data[['hours', 'attendance', 'marks']]
    y = data['result']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = LogisticRegression()
    model.fit(X_train, y_train)

train_model()

# ---------------- GUI ----------------
root = tk.Tk()
root.title("AI Student System")
root.geometry("450x450")
root.config(bg="#1e293b")

def clear():
    for widget in root.winfo_children():
        widget.destroy()

# ---------------- REGISTER ----------------
def register():
    clear()

    tk.Label(root, text="Register", font=("Arial", 18, "bold"), fg="white", bg="#1e293b").pack(pady=20)

    user = tk.Entry(root)
    user.pack(pady=5)

    pwd = tk.Entry(root, show="*")
    pwd.pack(pady=5)

    def save():
        try:
            cursor.execute("INSERT INTO users VALUES (?,?)", (user.get(), pwd.get()))
            conn.commit()
            messagebox.showinfo("Success", "Registered!")
            login()
        except:
            messagebox.showerror("Error", "User already exists")

    tk.Button(root, text="Register", command=save, bg="#22c55e", fg="white").pack(pady=10)
    tk.Button(root, text="Login", command=login).pack()

# ---------------- LOGIN ----------------
def login():
    clear()

    tk.Label(root, text="Login", font=("Arial", 18, "bold"), fg="white", bg="#1e293b").pack(pady=20)

    user = tk.Entry(root)
    user.pack(pady=5)

    pwd = tk.Entry(root, show="*")
    pwd.pack(pady=5)

    def check():
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (user.get(), pwd.get()))
        if cursor.fetchone():
            dashboard()
        else:
            messagebox.showerror("Error", "Invalid Login")

    tk.Button(root, text="Login", command=check, bg="#3b82f6", fg="white").pack(pady=10)
    tk.Button(root, text="Register", command=register).pack()

# ---------------- DASHBOARD ----------------
def dashboard():
    clear()

    tk.Label(root, text="Dashboard", font=("Arial", 18, "bold"), fg="white", bg="#1e293b").pack(pady=20)

    tk.Label(root, text=f"Total Students: {len(data)}",
             fg="white", bg="#1e293b", font=("Arial", 14)).pack(pady=10)

    tk.Button(root, text="Predict", command=predict_screen,
              bg="#22c55e", fg="white").pack(pady=5)

    tk.Button(root, text="Show Chart", command=show_chart,
              bg="#f59e0b", fg="white").pack(pady=5)

    tk.Button(root, text="Upload CSV", command=upload_file,
              bg="#06b6d4", fg="white").pack(pady=5)

    tk.Button(root, text="Logout", command=login).pack(pady=10)

# ---------------- CHART ----------------
def show_chart():
    pass_count = data['result'].value_counts().get(1, 0)
    fail_count = data['result'].value_counts().get(0, 0)

    plt.bar(['Pass', 'Fail'], [pass_count, fail_count])
    plt.title("Student Result Distribution")
    plt.show()

# ---------------- UPLOAD CSV ----------------
def upload_file():
    global data
    file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if file:
        data = pd.read_csv(file)
        train_model()
        messagebox.showinfo("Success", "New Data Loaded!")

# ---------------- PREDICTION ----------------
def predict_screen():
    clear()

    tk.Label(root, text="Prediction", font=("Arial", 18, "bold"), fg="white", bg="#1e293b").pack(pady=20)

    h = tk.Entry(root); h.pack(pady=5)
    a = tk.Entry(root); a.pack(pady=5)
    m = tk.Entry(root); m.pack(pady=5)

    result = tk.Label(root, text="", fg="white", bg="#1e293b", font=("Arial", 14))
    result.pack(pady=10)

    def predict():
        try:
            new = pd.DataFrame([[float(h.get()), float(a.get()), float(m.get())]],
                               columns=['hours','attendance','marks'])
            pred = model.predict(new)

            if pred[0] == 1:
                result.config(text="PASS ✅", fg="green")
            else:
                result.config(text="FAIL ❌", fg="red")
        except:
            messagebox.showerror("Error", "Invalid Input")

    tk.Button(root, text="Predict", command=predict,
              bg="#22c55e", fg="white").pack(pady=10)

    tk.Button(root, text="Back", command=dashboard).pack()

# ---------------- START ----------------
login()
root.mainloop()