import os
import re
import json
import logging
import threading
from datetime import datetime
 
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
 
# ---------------- секреты из переменных окружения ----------------
TELEGRAM_TOKEN = "8968331217:AAHNqa30L8iykEVZH3NiHwRIjFuxi_l2dU0"
SPREADSHEET_ID = "1MY4lsVeCW0_v8rFWMobqxf8Ud0A6AisG0inlrAp_peo"
SHEET_NAME = "Task2"
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
# -------------------------------------------------------------------
 
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
 
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("email_bot")
 
 
 
# ---------- 2) доступ к Google Sheets ----------
def get_worksheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    info = json.loads(GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    return sh.worksheet(SHEET_NAME)
 
 
# ---------- 3) логика бота ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    match = EMAIL_RE.search(text)
 
    if not match:
        await update.message.reply_text(
            "Не нашёл email в сообщении. Пришлите текст, содержащий email-адрес."
        )
        return
 
    email = match.group(0)
    username = f"@{update.effective_user.username}" if update.effective_user.username else str(update.effective_user.id)
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
 
    try:
        ws = get_worksheet()
        ws.append_row([email, timestamp, username], value_input_option="USER_ENTERED")
        await update.message.reply_text(f"Готово! {email} добавлен в таблицу (лист «{SHEET_NAME}»).")
        log.info("Added row: %s | %s | %s", email, timestamp, username)
    except Exception as e:
        log.exception("Failed to write to sheet")
        await update.message.reply_text(f"Ошибка: {e}")
 
 
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("Bot started, polling...")
    app.run_polling()
 
 
if __name__ == "__main__":
    main()
