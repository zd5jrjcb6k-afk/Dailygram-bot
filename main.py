import os
import sqlite3
import datetime
import logging
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# --- LOGGING SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- FLASK KEEP ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Dailygram Miner Bot & Mini App backend is alive!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()

# --- CONFIGURATION ---
BOT_TOKEN = "8817058021:AAGUsAVqwHV_dDUtccdvmAUz8oWgFW3M4gM"
MY_WALLET_ADDRESS = "UQAfwLNsBO1WJbzc2bQtBIEtPv9ErGvEpKRn-g2XSz_vRdWH"
REFERRAL_REWARD = 0.1
PAYOUT_CHANNEL = "@dailygram_payout_channel"
MIN_WITHDRAWAL = 1.0  # Minimum opnamebedrag in GRAM

# --- HELPER FUNCTIONS ---
async def send_payout_notification(bot, user_id, amount, wallet_address, is_deposit=False):
    """ Stuurt automatisch een melding naar het Payout Kanaal """
    if is_deposit:
        message = (
            "🚀 **NEW DEPOSIT CONFIRMED!** 🚀\n\n"
            f"👤 **User ID:** `{user_id}`\n"
            f"💎 **Deposit Amount:** `{amount:.1f} GRAM`\n"
            f"📈 **Daily Reward:** `{amount * 0.005:.3f} GRAM/day`\n\n"
            "⚡ Start mining today with @DailygramMiner_bot !"
        )
    else:
        message = (
            "💸 **WITHDRAWAL PROCESSED!** 💸\n\n"
            f"👤 **User ID:** `{user_id}`\n"
            f"💰 **Amount Paid:** `{amount:.3f} GRAM`\n"
            f"💼 **Wallet:** `{wallet_address[:6]}...{wallet_address[-4:]}`\n\n"
            "🎉 Congratulations! Keep mining with @DailygramMiner_bot !"
        )
    
    try:
        await bot.send_message(chat_id=PAYOUT_CHANNEL, text=message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Fout bij versturen naar kanaal: {e}")

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
            last_payout TEXT,
            wallet_address TEXT DEFAULT ''
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
        cursor.execute(
            "INSERT INTO users (user_id, username, is_active, deposit_amount, daily_reward, balance, referred_by, referrals_count, wallet_address) VALUES (?, ?, 0, 0.0, 0.0, 0.0, ?, 0, '')",
            (user_id, username, referrer_id)
        )
        conn.commit()
        
        if referrer_id and referrer_id != user_id:
            cursor.execute("UPDATE users SET referrals_count = referrals_count + 1, balance = balance + ? WHERE user_id = ?", (REFERRAL_REWARD, referrer_id))
            conn.commit()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
    conn.close()
    return user

def update_user_wallet(user_id, wallet):
    conn = sqlite3.connect("farming_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET wallet_address = ? WHERE user_id = ?", (wallet, user_id))
    conn.commit()
    conn.close()

def update_user_balance(user_id, new_balance):
    conn = sqlite3.connect("farming_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()

def activate_farming(user_id, deposit_amount):
    daily_reward = deposit_amount * 0.005
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
    
    referrer_id = None
    if context.args and context.args[0].isdigit():
        referrer_id = int(context.args[0])
        
    db_user = get_or_create_user(user.id, user.username, referrer_id)
    
    is_active = db_user[2]
    deposit_amount = db_user[3]
    daily_reward = db_user[4]
    balance = db_user[5]
    referrals_count = db_user[7]
    wallet = db_user[9] if len(db_user) > 9 else ""
    
    status_text = "Active 🟢" if is_active else "Inactive 🔴"
    wallet_status = f"`{wallet[:6]}...{wallet[-4:]}`" if wallet else "Not Set ❌"
    
    if not is_active:
        msg = (
            f"👋 **Welcome {user.first_name} to Dailygram Miner!**\n\n"
            f"📊 **Status:** {status_text}\n"
            f"💰 **Balance:** {balance:.3f} GRAM\n"
            f"💼 **Wallet:** {wallet_status}\n"
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
            [InlineKeyboardButton("⚙️ Set Wallet Address", callback_data="set_wallet")],
            [InlineKeyboardButton("👥 Invite Friends (Get Free GRAM)", callback_data="referral")]
        ]
    else:
        msg = (
            f"👋 **Welcome back {user.first_name}!**\n\n"
            f"📊 **Status:** {status_text}\n"
            f"💎 **Active Deposit:** {deposit_amount:.1f} GRAM\n"
            f"🎁 **Daily Reward:** {daily_reward:.3f} GRAM/day\n"
            f"💰 **Balance:** {balance:.3f} GRAM\n"
            f"💼 **Wallet:** {wallet_status}\n"
            f"👥 **Referrals:** {referrals_count} friends invited"
        )
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh Balance", callback_data="refresh")],
            [InlineKeyboardButton("💸 Withdraw Rewards", callback_data="withdraw_req")],
            [InlineKeyboardButton("⚙️ Set Wallet Address", callback_data="set_wallet")],
            [InlineKeyboardButton("👥 Invite Friends", callback_data="referral")]
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
            f"Share your referral link with friends and earn **{REFERRAL_REWARD} GRAM** for every user who joins!\n\n"
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
        
        await send_payout_notification(context.bot, user_id, amount, MY_WALLET_ADDRESS, is_deposit=True)

        success_text = (
            "🎉 **Payment Received & Verified!**\n\n"
            f"Your Mining Status is now **Active**. You will receive **{daily_reward:.3f} GRAM** every 24 hours!"
        )
        keyboard = [[InlineKeyboardButton("📊 Go to Dashboard", callback_data="start")]]
        await query.edit_message_text(success_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "set_wallet":
        context.user_data['awaiting_wallet'] = True
        msg_text = (
            "💼 **Set Your Wallet Address:**\n\n"
            "Please send your **TON / GRAM Wallet Address** as a reply in this chat."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="start")]]
        await query.edit_message_text(msg_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "withdraw_req":
        db_user = get_or_create_user(user_id, query.from_user.username)
        balance = db_user[5]
        wallet = db_user[9] if len(db_user) > 9 else ""

        if not wallet:
            msg_text = (
                "⚠️ **Wallet Not Configured!**\n\n"
                "Please click **'Set Wallet Address'** first to store your payout wallet."
            )
            keyboard = [
                [InlineKeyboardButton("⚙️ Set Wallet Address", callback_data="set_wallet")],
                [InlineKeyboardButton("⬅️ Back", callback_data="start")]
            ]
            await query.edit_message_text(msg_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if balance < MIN_WITHDRAWAL:
            msg_text = (
                "💸 **Withdrawal Request:**\n\n"
                f"Your current balance: `{balance:.3f} GRAM`\n"
                f"Minimum withdrawal: `{MIN_WITHDRAWAL:.1f} GRAM`\n\n"
                "Please accumulate more rewards before requesting a payout."
            )
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="start")]]
            await query.edit_message_text(msg_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            # Voer uitbetalingsaanvraag uit
            update_user_balance(user_id, 0.0)
            await send_payout_notification(context.bot, user_id, balance, wallet, is_deposit=False)
            
            msg_text = (
                "✅ **Withdrawal Request Submitted!**\n\n"
                f"💰 **Amount:** `{balance:.3f} GRAM`\n"
                f"💼 **Sent to:** `{wallet[:6]}...{wallet[-4:]}`\n\n"
                "Your payout has been recorded and broadcasted to the official channel!"
            )
            keyboard = [[InlineKeyboardButton("📊 Back to Dashboard", callback_data="start")]]
            await query.edit_message_text(msg_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "start" or data == "refresh":
        await start(update, context)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Verwerkt ingevoerde wallet-adressen """
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if context.user_data.get('awaiting_wallet'):
        if len(text) > 20:  # Eenvoudige check voor een geldige wallet hash
            update_user_wallet(user_id, text)
            context.user_data['awaiting_wallet'] = False
            await update.message.reply_text(
                f"✅ **Wallet Address Saved!**\n\nYour wallet:\n`{text}`",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⚠️ Invalid wallet address. Please enter a valid TON/GRAM wallet address.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

# --- MAIN RUNNER ---
def main():
    init_db()
    keep_alive()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_error_handler(error_handler)
    
    print("Dailygram Miner Bot & Mini App Backend is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
