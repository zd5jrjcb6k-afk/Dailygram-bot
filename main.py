import os
import sqlite3
import datetime
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- FLASK KEEP ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURATION ---
BOT_TOKEN = "8817058021:AAGUsAVqwHV_dDUtccdvmAUz8oWgFW3M4gM"
MY_WALLET_ADDRESS = "UQAfwLNsBO1WJbzc2bQtBIEtPv9ErGvEpKRn-g2XSz_vRdWH"
REFERRAL_REWARD = 0.1  # Reward in GRAM per invited friend

# --- DATABASE SETTINGS ---
def init_db():
    conn = sqlite3.connect("farming_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            is_active INTEGER DEFAULT 0,
            deposit_amount REAL DEFAULT 0.0,
            daily_reward REAL DEFAULT 0.0,
            balance REAL DEFAULT 0.0,
            referred_by INTEGER,
            referrals_count INTEGER DEFAULT 0,
            last_payout TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_or_create_user(user_id, username, referrer_id=None):
    conn = sqlite3.connect("farming_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        # Save new user with referrer
        cursor.execute(
            "INSERT INTO users (user_id, username, is_active, deposit_amount, daily_reward, balance, referred_by, referrals_count) VALUES (?, ?, 0, 0.0, 0.0, 0.0, ?, 0)",
            (user_id, username, referrer_id)
        )
        conn.commit()
        
        # Reward the referrer if applicable
        if referrer_id and referrer_id != user_id:
            cursor.execute("UPDATE users SET referrals_count = referrals_count + 1, balance = balance + ? WHERE user_id = ?", (REFERRAL_REWARD, referrer_id))
            conn.commit()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
    conn.close()
    return user

def activate_farming(user_id, deposit_amount):
    daily_reward = deposit_amount * 0.005  # 0.5% daily yield
    conn = sqlite3.connect("farming_bot.db")
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    cursor.execute(
        "UPDATE users SET is_active = 1, deposit_amount = ?, daily_reward = ?, last_payout = ? WHERE user_id = ?",
        (deposit_amount, daily_reward, now, user_id)
    )
    conn.commit()
    conn.close()

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Check if user came via a referral link (/start 123456)
    referrer_id = None
    if context.args and context.args[0].isdigit():
        referrer_id = int(context.args[0])
        
    db_user = get_or_create_user(user.id, user.username, referrer_id)
    
    is_active = db_user[2]
    deposit_amount = db_user[3]
    daily_reward = db_user[4]
    balance = db_user[5]
    referrals_count = db_user[7]
    
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user.id}"
    status_text = "Active 🟢" if is_active else "Inactive 🔴"
    
    if not is_active:
        msg = (
            f"👋 **Welcome {user.first_name} to Dailygram Miner!**\n\n"
            f"📊 **Status:** {status_text}\n"
            f"💰 **Balance:** {balance:.3f} GRAM\n"
            f"👥 **Referrals:** {referrals_count} friends invited\n"
            f"📈 **Daily Yield:** 0.5% per day\n\n"
            f"⚡ *How it works?*\n"
            f"Choose a deposit plan to start earning daily GRAM rewards:\n\n"
            f"• Deposit **1 GRAM** → Earn **0.005 GRAM**/day\n"
            f"• Deposit **5 GRAM** → Earn **0.025 GRAM**/day\n"
            f"• Deposit **10 GRAM** → Earn **0.050 GRAM**/day\n"
            f"• Deposit **20 GRAM** → Earn **0.100 GRAM**/day\n"
            f"• Deposit **50 GRAM** → Earn **0.250 GRAM**/day\n"
            f"• Deposit **100 GRAM** → Earn **0.500 GRAM**/day"
        )
        keyboard = [
            [InlineKeyboardButton("📥 Deposit 1 GRAM", callback_data="dep_1"),
             InlineKeyboardButton("📥 Deposit 5 GRAM", callback_data="dep_5")],
            [InlineKeyboardButton("📥 Deposit 10 GRAM", callback_data="dep_10"),
             InlineKeyboardButton("📥 Deposit 20 GRAM", callback_data="dep_20")],
            [InlineKeyboardButton("📥 Deposit 50 GRAM", callback_data="dep_50"),
             InlineKeyboardButton("📥 Deposit 100 GRAM", callback_data="dep_100")],
            [InlineKeyboardButton("👥 Invite Friends (Get Free GRAM)", callback_data="referral")]
        ]
    else:
        msg = (
            f"👋 **Welcome back {user.first_name}!**\n\n"
            f"📊 **Status:** {status_text}\n"
            f"💎 **Active Deposit:** {deposit_amount:.1f} GRAM\n"
            f"🎁 **Daily Reward:** {daily_reward:.3f} GRAM/day\n"
            f"👥 **Referrals:** {referrals_count} friends invited\n"
            f"💰 **Balance:** {balance:.3f} GRAM"
        )
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh Balance", callback_data="refresh")],
            [InlineKeyboardButton("👥 Invite Friends", callback_data="referral")],
            [InlineKeyboardButton("💸 Withdraw Rewards", callback_data="withdraw")]
        ]
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    
    if data == "referral":
        ref_text = (
            f"👥 **Invite Friends & Earn Free GRAM!**\n\n"
            f"Share your referral link with friends and earned **{REFERRAL_REWARD} GRAM** for every user who joins!\n\n"
            f"🔗 **Your Personal Referral Link:**\n"
            f"`{ref_link}`"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="start")]]
        await query.edit_message_text(ref_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("dep_"):
        amount = float(data.split("_")[1])
        daily_reward = amount * 0.005
        context.user_data['pending_amount'] = amount
        
        deposit_text = (
            f"📥 **Deposit Instructions ({amount:.0f} GRAM):**\n\n"
            f"1. Send exactly **{amount:.1f} GRAM** to the wallet address below:\n"
            f"`{MY_WALLET_ADDRESS}`\n\n"
            f"2. **IMPORTANT:** Include this code as Memo/Comment in your transaction:\n"
            f"`ID-{user_id}`\n\n"
            f"🎁 **Daily Yield:** {daily_reward:.3f} GRAM per day (0.5%)\n\n"
            f"⚠️ *It usually takes 1-3 minutes for the network to confirm your payment.*"
        )
        keyboard = [
            [InlineKeyboardButton("✅ I Have Paid (Verify Payment)", callback_data="check_payment")],
            [InlineKeyboardButton("⬅️ Back", callback_data="start")]
        ]
        await query.edit_message_text(deposit_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "check_payment":
        amount = context.user_data.get('pending_amount', 10.0)
        activate_farming(user_id, amount)
        daily_reward = amount * 0.005
        
        success_text = (
            "🎉 **Payment Received & Verified!**\n\n"
            f"Your Mining Status is now **Active**. You will receive **{daily_reward:.3f} GRAM** every 24 hours!"
        )
        keyboard = [[InlineKeyboardButton("📊 Go to Dashboard", callback_data="start")]]
        await query.edit_message_text(success_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "start" or data == "refresh":
        await start(update, context)

    elif data == "withdraw":
        withdraw_text = (
            "💸 **Withdrawal Request:**\n\n"
            "Minimum withdrawal amount is **1.0 GRAM**.\n"
            "Please accumulate more rewards before withdrawing."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="start")]]
        await query.edit_message_text(withdraw_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# --- MAIN RUNNER ---
def main():
    init_db()
    keep_alive()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Dailygram Miner Bot is online and listening...")
    app.run_polling()

if __name__ == "__main__":
    main()
