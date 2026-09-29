import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- ALLES IS AL VOOR JE INGEVULD ---
BOT_TOKEN = "8817058021:AAGUsAVqwHV_dDUtccdvmAUz8oWgFW3M4gM"
MY_WALLET_ADDRESS = "UQAfwLNsBO1WJbzc2bQtBIEtPv9ErGvEpKRn-g2XSz_vRdWH"

COST_GRAM = 10.0
DAILY_REWARD_GRAM = 0.05  # 0.05 GRAM per dag (0.5% dagelijks)

# --- DATABASE INSTELLINGEN ---
def init_db():
    conn = sqlite3.connect("farming_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            is_active INTEGER DEFAULT 0,
            balance REAL DEFAULT 0.0,
            last_payout TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_or_create_user(user_id, username):
    conn = sqlite3.connect("farming_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, username, is_active, balance) VALUES (?, ?, 0, 0.0)",
            (user_id, username)
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
    conn.close()
    return user

def activate_farming(user_id):
    conn = sqlite3.connect("farming_bot.db")
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    cursor.execute(
        "UPDATE users SET is_active = 1, last_payout = ? WHERE user_id = ?",
        (now, user_id)
    )
    conn.commit()
    conn.close()

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = get_or_create_user(user.id, user.username)
    
    is_active = db_user[2]
    balance = db_user[3]
    
    status_text = "Actief 🟢" if is_active else "Inactief 🔴"
    
    msg = (
        f"👋 Welkom **{user.first_name}** bij **Dailygram Miner**!\n\n"
        f"📊 **Jouw Status:** {status_text}\n"
        f"💰 **Jouw Saldo:** {balance} GRAM\n\n"
        f"⚡ *Hoe werkt het?*\n"
        f"Stort eenmalig **{COST_GRAM} GRAM** om te starten en ontvang elke dag **{DAILY_REWARD_GRAM} GRAM** beloning!"
    )
    
    keyboard = []
    if not is_active:
        keyboard.append([InlineKeyboardButton("📥 10 GRAM Storten & Starten", callback_data="deposit")])
    else:
        keyboard.append([InlineKeyboardButton("🔄 Saldo Vernieuwen", callback_data="refresh")])
        keyboard.append([InlineKeyboardButton("💸 Saldo Opnemen", callback_data="withdraw")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == "deposit":
        deposit_text = (
            f"📥 **Instructies voor storten:**\n\n"
            f"1. Maak exact **{COST_GRAM} GRAM** over naar het onderstaande adres:\n"
            f"`{MY_WALLET_ADDRESS}`\n\n"
            f"2. **BELANGRIJK:** Voeg deze code toe als Memo/Comment bij je transactie:\n"
            f"`ID-{user_id}`\n\n"
            f"⚠️ *Na het storten duurt het 1-3 minuten voordat het netwerk je transactie verwerkt.*"
        )
        keyboard = [
            [InlineKeyboardButton("✅ Ik heb betaald (Check Transactie)", callback_data="check_payment")],
            [InlineKeyboardButton("⬅️ Terug", callback_data="start")]
        ]
        await query.edit_message_text(deposit_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "check_payment":
        activate_farming(user_id)
        
        success_text = (
            "🎉 **Betaling Ontvangen & Gefilterd!**\n\n"
            f"Je Mining status staat nu op **Actief**. Je ontvangt vanaf nu elke 24 uur automatisch je **{DAILY_REWARD_GRAM} GRAM** beloning!"
        )
        keyboard = [[InlineKeyboardButton("📊 Naar Dashboard", callback_data="start")]]
        await query.edit_message_text(success_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "start":
        await start(update, context)

# --- MAIN RUNNER ---
def main():
    init_db()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Dailygram Miner Bot is online en luistert...")
    app.run_polling()

if __name__ == "__main__":
    main()
