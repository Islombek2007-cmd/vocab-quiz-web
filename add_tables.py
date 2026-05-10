import psycopg2

DATABASE_URL = "postgresql://vocab_quiz_bot_user:8l8V1ZGeAwpZMo8cW52UBzAAqfqa43mn@dpg-d7v295naqgkc73d3609g-a.oregon-postgres.render.com:5432/vocab_quiz_bot"

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS final_tests (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS final_test_questions (
    id SERIAL PRIMARY KEY,
    test_id INTEGER,
    word_id INTEGER,
    word TEXT,
    translation TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS final_test_results (
    id SERIAL PRIMARY KEY,
    student_id INTEGER,
    test_id INTEGER,
    score INTEGER,
    total INTEGER,
    percentage INTEGER,
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, test_id)
)
""")

conn.commit()
conn.close()
print("✅ Tables created successfully!")