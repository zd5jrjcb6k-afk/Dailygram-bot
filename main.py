import os
import logging
from flask import Flask, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application
import threading

# Logging setup
logging.basicConfig(level=logging.INFO)

# Flask Web Server setup
app = Flask(__name__, static_folder='.')

WEBAPP_URL = "https://dailygram-bot.onrender.com"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # Start Flask op de achtergrond
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Hou de container actief
    import time
    while True:
        time.sleep(3600)
