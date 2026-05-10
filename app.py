from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random
import secrets
import string
import os

app = Flask(__name__)
app.secret_key = "vocabquiz_secret_key_2025"

from database.db import get_connection

# ============ Helper Functions ============

def generate_login_code():
    import secrets
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(25))

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, full_name, role, created_by, center_name, login_code FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    total_words = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
    total_students = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM quiz_results")
    total_quizzes = cursor.fetchone()[0]
    conn.close()
    return {"total_words": total_words, "total_students": total_students, "total_quizzes": total_quizzes}

# ============ Routes ============

@app.route("/", methods=["GET"])
def index():
    return render_template("login.html", error=None)

@app.route("/login_code", methods=["POST"])
def login_code():
    login_code = request.form["login_code"].strip()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, role, created_by FROM users WHERE login_code = %s AND role = 'student'", (login_code,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session["user_id"] = user[0]
        session["username"] = user[1]
        session["role"] = user[3]
        session["full_name"] = user[2]
        session["teacher_id"] = user[4]
        return redirect(url_for("home"))
    else:
        return render_template("login.html", error="Invalid login code. Please check with your teacher.")

@app.route("/login_staff", methods=["POST"])
def login_staff():
    username = request.form["username"].strip()
    password = request.form["password"].strip()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, full_name, role FROM users WHERE username = %s AND role IN ('owner', 'admin', 'teacher')", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user[2] == password:
        session["user_id"] = user[0]
        session["username"] = user[1]
        session["role"] = user[4]
        session["full_name"] = user[3]
        session["teacher_id"] = None
        return redirect(url_for("home"))
    else:
        return render_template("login.html", error="Invalid username or password")

@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    user = get_user_by_id(session["user_id"])
    if not user:
        return redirect(url_for("logout"))
    
    user_dict = {
        "id": user[0],
        "username": user[1],
        "full_name": user[3],
        "role": user[4],
        "center_name": user[6],
        "teacher_id": user[5]
    }
    
    stats = get_user_stats()
    
    return render_template("home.html", user=user_dict, stats=stats)

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    user = get_user_by_id(session["user_id"])
    user_dict = {
        "id": user[0],
        "username": user[1],
        "full_name": user[3],
        "role": user[4],
        "center_name": user[6],
        "join_date": "2025"
    }
    
    return render_template("profile.html", user=user_dict)

@app.route("/change_password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    old_password = request.form["old_password"]
    new_password = request.form["new_password"]
    
    user = get_user_by_id(session["user_id"])
    
    if user[2] != old_password:
        return "Old password incorrect"
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_password, session["user_id"]))
    conn.commit()
    conn.close()
    
    return redirect(url_for("profile"))

# ============ Owner Routes ============

@app.route("/manage_admins")
def manage_admins():
    if "user_id" not in session or session.get("role") != "owner":
        return redirect(url_for("home"))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, center_name FROM users WHERE role = 'admin'")
    admins = cursor.fetchall()
    conn.close()
    
    return render_template("manage_admins.html", admins=admins)

@app.route("/add_admin", methods=["POST"])
def add_admin():
    if "user_id" not in session or session.get("role") != "owner":
        return redirect(url_for("home"))
    
    username = request.form["username"]
    password = request.form["password"]
    full_name = request.form["full_name"]
    center_name = request.form.get("center_name", "")
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, full_name, role, center_name, created_by) VALUES (%s, %s, %s, 'admin', %s, %s)",
            (username, password, full_name, center_name, session["user_id"])
        )
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
    
    return redirect(url_for("manage_admins"))

@app.route("/delete_admin/<int:admin_id>")
def delete_admin(admin_id):
    if "user_id" not in session or session.get("role") != "owner":
        return redirect(url_for("home"))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s AND role = 'admin'", (admin_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for("manage_admins"))

@app.route("/all_stats")
def all_stats():
    if "user_id" not in session or session.get("role") != "owner":
        return redirect(url_for("home"))
    return render_template("all_stats.html")

@app.route("/api/stats")
def api_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admins = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'teacher'")
    teachers = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
    students = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM vocabulary")
    words = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM quiz_results")
    quizzes = cursor.fetchone()[0]
    conn.close()
    
    return {"admins": admins, "teachers": teachers, "students": students, "words": words, "quizzes": quizzes}

# ============ Admin Routes ============

@app.route("/manage_teachers")
def manage_teachers():
    if "user_id" not in session or session.get("role") not in ["owner", "admin"]:
        return redirect(url_for("home"))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name FROM users WHERE role = 'teacher'")
    teachers = cursor.fetchall()
    conn.close()
    
    return render_template("manage_teachers.html", teachers=teachers)

@app.route("/add_teacher", methods=["POST"])
def add_teacher():
    if "user_id" not in session or session.get("role") not in ["owner", "admin"]:
        return redirect(url_for("home"))
    
    username = request.form["username"]
    password = request.form["password"]
    full_name = request.form["full_name"]
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, full_name, role, created_by) VALUES (%s, %s, %s, 'teacher', %s)",
            (username, password, full_name, session["user_id"])
        )
        conn.commit()
    except:
        pass
    conn.close()
    
    return redirect(url_for("manage_teachers"))

@app.route("/delete_teacher/<int:teacher_id>")
def delete_teacher(teacher_id):
    if "user_id" not in session or session.get("role") not in ["owner", "admin"]:
        return redirect(url_for("home"))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s AND role = 'teacher'", (teacher_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for("manage_teachers"))

@app.route("/manage_students/<int:teacher_id>")
def manage_students(teacher_id):
    if "user_id" not in session or session.get("role") not in ["owner", "admin"]:
        return redirect(url_for("home"))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE id = %s", (teacher_id,))
    teacher = cursor.fetchone()
    cursor.execute("SELECT id, username, full_name, login_code FROM users WHERE created_by = %s AND role = 'student'", (teacher_id,))
    students = cursor.fetchall()
    conn.close()
    
    return render_template("manage_students.html", 
                          students=students, 
                          teacher_id=teacher_id,
                          teacher_name=teacher[0] if teacher else "Unknown")

@app.route("/add_student/<int:teacher_id>", methods=["POST"])
def add_student(teacher_id):
    if "user_id" not in session or session.get("role") not in ["owner", "admin"]:
        return redirect(url_for("home"))
    
    student_name = request.form["student_name"].strip()
    login_code = generate_login_code()
    username = f"student_{login_code[:8]}"
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, full_name, role, created_by, login_code) VALUES (%s, %s, 'student', %s, %s)",
            (username, student_name, teacher_id, login_code)
        )
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
    
    return redirect(url_for("manage_students", teacher_id=teacher_id))

@app.route("/delete_student/<int:student_id>")
def delete_student(student_id):
    if "user_id" not in session or session.get("role") not in ["owner", "admin"]:
        return redirect(url_for("home"))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT created_by FROM users WHERE id = %s", (student_id,))
    student = cursor.fetchone()
    teacher_id = student[0] if student else None
    
    cursor.execute("DELETE FROM users WHERE id = %s AND role = 'student'", (student_id,))
    conn.commit()
    conn.close()
    
    if teacher_id:
        return redirect(url_for("manage_students", teacher_id=teacher_id))
    return redirect(url_for("manage_teachers"))

# ============ Teacher Routes ============

@app.route("/manage_vocabulary")
def manage_vocabulary():
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("home"))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, word, translation FROM vocabulary WHERE teacher_id = %s", (session["user_id"],))
    vocabulary = cursor.fetchall()
    conn.close()
    
    return render_template("manage_vocabulary.html", vocabulary=vocabulary)

@app.route("/add_vocab", methods=["POST"])
def add_vocab():
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("home"))
    
    word = request.form["word"].strip()
    translation = request.form["translation"].strip()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO vocabulary (word, translation, teacher_id) VALUES (%s, %s, %s)",
        (word, translation, session["user_id"])
    )
    conn.commit()
    conn.close()
    
    return redirect(url_for("manage_vocabulary"))

@app.route("/delete_vocab/<int:vocab_id>")
def delete_vocab(vocab_id):
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("home"))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vocabulary WHERE id = %s AND teacher_id = %s", (vocab_id, session["user_id"]))
    conn.commit()
    conn.close()
    
    return redirect(url_for("manage_vocabulary"))

@app.route("/my_students")
def my_students():
    if "user_id" not in session or session.get("role") != "teacher":
        return redirect(url_for("home"))
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, full_name, login_code FROM users WHERE created_by = %s AND role = 'student'", (session["user_id"],))
    students = cursor.fetchall()
    
    student_data = []
    for student in students:
        student_id = student[0]
        student_name = student[2]
        student_code = student[3]
        
        cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE student_id = %s", (student_id,))
        total_quizzes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE student_id = %s AND correct = true", (student_id,))
        correct_count = cursor.fetchone()[0]
        
        accuracy = 0
        if total_quizzes > 0:
            accuracy = round((correct_count / total_quizzes) * 100, 1)
        
        student_data.append({
            "id": student_id,
            "name": student_name,
            "code": student_code,
            "total_quizzes": total_quizzes,
            "correct": correct_count,
            "accuracy": accuracy
        })
    
    conn.close()
    
    return render_template("my_students.html", students=student_data)


@app.route("/bulk_add_vocab", methods=["POST"])
def bulk_add_vocab():
    if session.get("role") != "teacher":
        return "Unauthorized", 401
    
    data = request.get_json()
    lines = data.get('words', '').strip().split('\n')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for line in lines:
        if '=' in line:
            word, translation = line.split('=', 1)
            cursor.execute(
                "INSERT INTO vocabulary (word, translation, level, teacher_id) VALUES (%s, %s, 'easy', %s)",
                (word.strip(), translation.strip(), session["user_id"])
            )
    
    conn.commit()
    conn.close()
    return "OK", 200



@app.route("/telegram_auth")
def telegram_auth():
    # Get user data from Telegram Web App
    user_data = request.args.get('user')
    if user_data:
        import json
        user = json.loads(user_data)
        # Auto-login as student using Telegram ID
        session["telegram_id"] = user['id']
        session["username"] = user.get('username', 'telegram_user')
        session["full_name"] = user.get('first_name', '')
        session["role"] = "student"
        return redirect(url_for("quiz"))
    return redirect(url_for("index"))

    
# ============ Student Routes ============

@app.route("/take_quiz", methods=["GET", "POST"])
def take_quiz():
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("home"))
    
    student = get_user_by_id(session["user_id"])
    teacher_id = student[5] if student else None
    
    if not teacher_id:
        return render_template("quiz.html", question=None, result="No teacher assigned to you.", selected_level='easy')
    
    # Get level from URL parameter
    selected_level = request.args.get('level', 'easy')
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, word, translation FROM vocabulary WHERE teacher_id = %s AND level = %s", (teacher_id, selected_level))
    vocabulary = cursor.fetchall()
    conn.close()
    
    result = None
    question_word = None
    current_word_id = None
    correct_answer = None
    
    if request.method == "POST":
        user_answer = request.form["answer"].strip().lower()
        word_id = int(request.form["word_id"])
        correct = request.form["correct_answer"]
        
        is_correct = (user_answer == correct.lower())
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO quiz_results (student_id, word_id, correct) VALUES (%s, %s, %s)",
            (session["user_id"], word_id, is_correct)
        )
        conn.commit()
        conn.close()
        
        if is_correct:
            result = "✅ Correct!"
        else:
            result = f"❌ Wrong. Correct answer: {correct}"
    
    if vocabulary:
        random_word = random.choice(vocabulary)
        question_word = random_word[1]
        current_word_id = random_word[0]
        correct_answer = random_word[2]
    
    return render_template("quiz.html", 
                          question=question_word, 
                          word_id=current_word_id,
                          correct_answer=correct_answer,
                          result=result,
                          selected_level=selected_level)

@app.route("/my_progress")
def my_progress():
    if "user_id" not in session or session.get("role") != "student":
        return redirect(url_for("home"))
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE student_id = %s AND correct = true", (session["user_id"],))
    correct = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE student_id = %s AND correct = false", (session["user_id"],))
    wrong = cursor.fetchone()[0]
    total = correct + wrong
    percentage = (correct / total * 100) if total > 0 else 0
    
    cursor.execute('''
        SELECT v.word, v.translation, qr.correct, qr.date 
        FROM quiz_results qr 
        JOIN vocabulary v ON qr.word_id = v.id 
        WHERE qr.student_id = %s 
        ORDER BY qr.date DESC LIMIT 20
    ''', (session["user_id"],))
    recent = cursor.fetchall()
    conn.close()
    
    return render_template("my_progress.html", 
                          correct=correct, 
                          wrong=wrong, 
                          total=total, 
                          percentage=round(percentage, 1),
                          recent=recent)

# ============ Logout ============

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)