import psycopg2

DATABASE_URL = "postgresql://vocab_quiz_bot_user:8l8V1ZGeAwpZMo8cW52UBzAAqfqa43mn@dpg-d7v295naqgkc73d3609g-a.oregon-postgres.render.com:5432/vocab_quiz_bot"

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("UPDATE users SET username = 'Hasan' WHERE role = 'owner'")
cursor.execute("UPDATE users SET password = 'Hasan123' WHERE role = 'owner'")

conn.commit()
conn.close()

print("✅ Owner credentials changed!")
print("Username: newowner")
print("Password: newpassword123")