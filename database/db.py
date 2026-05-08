import os
import psycopg2

# Get database URL from environment variable
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://vocab_quiz_bot_user:8l8V1ZGeAwpZMo8cW52UBzAAqfqa43mn@dpg-d7v295naqgkc73d3609g-a/vocab_quiz_bot')

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            full_name TEXT,
            role TEXT CHECK(role IN ('owner', 'admin', 'teacher', 'student')),
            created_by INTEGER,
            center_name TEXT,
            login_code TEXT UNIQUE
        )
    ''')
    
    # Vocabulary table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id SERIAL PRIMARY KEY,
            word TEXT,
            translation TEXT,
            teacher_id INTEGER
        )
    ''')
    
    # Quiz results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id SERIAL PRIMARY KEY,
            student_id INTEGER,
            word_id INTEGER,
            correct BOOLEAN,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add default owner if none exists
    cursor.execute("SELECT * FROM users WHERE role = 'owner'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (%s, %s, %s, %s)",
            ("owner", "owner123", "System Owner", "owner")
        )
    
    conn.commit()
    conn.close()
    print("PostgreSQL database ready")

# Run setup when imported
setup_database()