import os
import psycopg2
import traceback

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set!")

def get_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"Database connection error: {e}")
        print(traceback.format_exc())
        raise

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
try:
    setup_database()
except Exception as e:
    print(f"Setup failed: {e}")
    import traceback
    traceback.print_exc()