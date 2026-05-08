import telebot
from telebot.types import Message
import sqlite3
import os

from config import BOT_TOKEN, OWNER_ID
from database.db import get_connection

bot = telebot.TeleBot(BOT_TOKEN)

# Helper to check if user is owner
def is_owner(user_id):
    return user_id == OWNER_ID

# Command: /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to Vocabulary Quiz Bot.")

# Command: /add_admin [name]
@bot.message_handler(commands=['add_admin'])
def add_admin(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "❌ Only owner can use this command.")
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /add_admin CenterName")
        return
    
    admin_name = parts[1]
    admin_id = message.from_user.id  # For now, admin is the one typing
    username = message.from_user.username or "no_username"
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO admins (name, telegram_id, owner_id) VALUES (?, ?, ?)",
            (admin_name, admin_id, OWNER_ID)
        )
        conn.commit()
        bot.reply_to(message, f"✅ Admin '{admin_name}' added successfully.")
    except sqlite3.IntegrityError:
        bot.reply_to(message, "❌ This Telegram ID is already an admin.")
    finally:
        conn.close()

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()