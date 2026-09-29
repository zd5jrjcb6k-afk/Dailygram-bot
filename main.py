import os
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging instellen
logging.basicConfig(level=logging.INFO)

# Telegram Bot Token & WebApp URL
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "JOUW_TELEGRAM_BOT_TOKEN_HIER")
WEBAPP_URL = "https://dailygram-bot.onrender.com"

# /start Commando
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🦁 Open Lion Miner", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welkom bij Lion Miner! 🦁\n\nKlik op de knop hieronder om de Mini App te openen en te beginnen met minen!",
        reply_markup=reply_markup
    )

def run_bot():
    # Telegram Bot Applicatie bouwen
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    # Eenvoudige HTTP Webserver voor Render (serveert index.html, style.css, script.js)
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    
    logging.info(f"Server gestart op poort {port}")
    
    # Start bot polling en HTTP server
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    run_bot()
