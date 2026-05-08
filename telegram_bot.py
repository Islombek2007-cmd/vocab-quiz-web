import os
import psycopg2
import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


from telegram import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    web_app_url = "https://vocabquiz-01jb.onrender.com"
    
    keyboard = [[KeyboardButton("🚀 Open Vocabulary Quiz", web_app=WebAppInfo(url=web_app_url))]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🎓 Welcome! Click the button below to start your vocabulary quiz inside Telegram.",
        reply_markup=reply_markup
    )

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://vocab_quiz_bot_user:8l8V1ZGeAwpZMo8cW52UBzAAqfqa43mn@dpg-d7v295naqgkc73d3609g-a/vocab_quiz_bot')

def get_connection():
    return psycopg2.connect(DATABASE_URL)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

student_sessions = {}

def get_student_by_code(login_code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, created_by FROM users WHERE login_code = %s AND role = 'student'", (login_code,))
    student = cursor.fetchone()
    conn.close()
    return student

def get_vocabulary_by_teacher(teacher_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, word, translation FROM vocabulary WHERE teacher_id = %s", (teacher_id,))
    vocab = cursor.fetchall()
    conn.close()
    return vocab

def save_quiz_result(student_id, word_id, is_correct):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quiz_results (student_id, word_id, correct) VALUES (%s, %s, %s)", (student_id, word_id, is_correct))
    conn.commit()
    conn.close()

def get_student_stats(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE student_id = %s AND correct = true", (student_id,))
    correct = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM quiz_results WHERE student_id = %s AND correct = false", (student_id,))
    wrong = cursor.fetchone()[0]
    conn.close()
    return correct, wrong

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    student_sessions[user_id] = {'step': 'waiting_for_code'}
    await update.message.reply_text("🎓 Welcome to VocabQuiz!\n\nPlease enter your login code from your teacher.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if user_id not in student_sessions:
        student_sessions[user_id] = {'step': 'waiting_for_code'}
    
    step = student_sessions[user_id].get('step')
    
    if step == 'waiting_for_code':
        student = get_student_by_code(text)
        if student:
            student_sessions[user_id]['student_id'] = student[0]
            student_sessions[user_id]['student_name'] = student[1]
            student_sessions[user_id]['teacher_id'] = student[2]
            student_sessions[user_id]['step'] = 'ready'
            correct, wrong = get_student_stats(student[0])
            await update.message.reply_text(f"✅ Welcome {student[1]}!\n\n📊 Correct: {correct} | Wrong: {wrong}\n\nType /quiz to start")
        else:
            await update.message.reply_text("❌ Invalid code. Type /start to try again.")
            student_sessions.pop(user_id, None)
    
    elif step == 'quiz_active':
        correct_answer = student_sessions[user_id].get('correct_answer')
        current_word_id = student_sessions[user_id].get('current_word_id')
        is_correct = (text.lower() == correct_answer.lower())
        save_quiz_result(student_sessions[user_id]['student_id'], current_word_id, is_correct)
        await update.message.reply_text("✅ Correct!" if is_correct else f"❌ Wrong! Answer: {correct_answer}")
        await send_quiz_question(update, context)

async def send_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    teacher_id = student_sessions[user_id]['teacher_id']
    vocabulary = get_vocabulary_by_teacher(teacher_id)
    
    if not vocabulary:
        await update.message.reply_text("No vocabulary available.")
        student_sessions[user_id]['step'] = 'ready'
        return
    
    random_word = random.choice(vocabulary)
    word_id, word, translation = random_word
    student_sessions[user_id]['current_word_id'] = word_id
    student_sessions[user_id]['correct_answer'] = translation
    student_sessions[user_id]['step'] = 'quiz_active'
    await update.message.reply_text(f"📖 Translate: {word}")

async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in student_sessions or student_sessions[user_id].get('step') == 'waiting_for_code':
        await update.message.reply_text("Login first: /start")
        return
    await send_quiz_question(update, context)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in student_sessions or student_sessions[user_id].get('step') == 'waiting_for_code':
        await update.message.reply_text("Login first: /start")
        return
    correct, wrong = get_student_stats(student_sessions[user_id]['student_id'])
    total = correct + wrong
    pct = (correct/total*100) if total > 0 else 0
    await update.message.reply_text(f"📊 Correct: {correct} | Wrong: {wrong}\nAccuracy: {pct:.1f}%")

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    student_sessions.pop(user_id, None)
    await update.message.reply_text("Logged out. /start to login again.")

def main():
    TOKEN = "8765382148:AAEMI5stbL1tXPhMb1yxFDs8G1vrQNPa4IY"
    
    if not TOKEN:
        print("ERROR: No token")
        return
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("logout", logout_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Telegram bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()