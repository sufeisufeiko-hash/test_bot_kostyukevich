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
SHEET_NAME = "Задача 2"
GOOGLE_CREDENTIALS_JSON = "{"type": "service_account", "project_id": "tidy-visitor-504517-b0", "private_key_id": "3721f53f0ebd142110edcb5cf9b67366ed2aa5f7", "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDZ7wIeRHcr4hNT\n8tLcKihkWsZTxjh7zsGH73FGa8aGqHKie6qk7oSGy12kqoYg0buY91dGdR+Z3XBL\n1qJAeteGMDW3s1d387pbdKcl4BPqYTIaLVpTx3mrtggxIJs+ni79kgTNvVh3eoFG\nKKRs6IbSnNJceJTqEC0QooMHdSEGDT4MajkscOF/x54BGRta3UfyuOVFf0sdPlBm\nsPK51LHUU6/3MVMP3hw/6IM3xNnMjN9rSp8h15ZbcDoRSNmmLXp+eTrXyToBAiG1\no4pKfyf23cIs5czlbD4mrsFC8MAd39XaFh7wJJ+C1422I6Wvq+CJQhqu8Ruivbiq\n5n1a1sQPAgMBAAECggEAZSg/v3TgLApgFlNb9L3MyegorrIPfchWpJZL6fgUymRd\n8XWdm7jq4vZ6nPhaEdnIThRg+l9bL7xNZ6ZU4cEjUTIHfSFNtGv5UIIxI6+DDwPW\nkbgDeWfZ3g48dzE/Xi1memTQvf7plWvTnZE34SV9jz0jl7CQzqR7hoEoeMmxbnDT\nwaXLB2XwpqbU+aJttcO8tX+rZD+iz4j9uq/1SljZmPN1UIZEboa35JPQIvDLlzTe\nC8UWwFEje5gN3STsXYMsr0r+77N3LtgU6wqY78OVvUoXLXmM8lZkTdtGtRADMC3y\naiIwgpfrekDuvVljALHFbcE+lHXWohHsvVxGoJ9kQQKBgQDzM29TS2qv/MHae9pp\nSVCVehArr8eQkzsBU0aDYxaHfw0zSeqLqT3EPhPyWimypFzubkwabmSlVeb/hemA\ncmRAcUiHVBstFloAVdNAh4m4kc0JPX884yeHWxHlcJNMOs1olpt5MI9LeF/UQfe2\n5Fkol+bUX49woFr6dNYLNROdxwKBgQDlZyfUxMYIeQd70P1UUW2SlTwoRDJEOVOd\nrfGwdJ3iR/hN/NtsK4XdcxJuRYNVI6w2DrUuYS4JdEElXGPyi9DzVyYC98KX/SS3\nNiThjr6WRGGB5r5Mla4fFA6ZGcXnaeEF0cN4TEmA/r/0cbaVeKR/3aRI6994hFmq\nDbqBublHeQKBgQCGV4FFd8GFWZAUCpqJ0m/rQjQwjbcli87qWn/3EANf8bTvAgPI\nBkMSZmBKXbfu8JBNPSxY5WY/VoZ13BkyVP5AAtPXvYQNke1Bhidd3AEdrZyfYBMr\nJSeuw4XNQjR7xXe2MIvNlB9zxxjYfWBC7Ty7Cb3+zpLD2jCnbWbXZghh/QKBgAux\n15D8OxBBg0UnoVKEGC7p1rhCycE6nu2h6XlSaJ4ZhyoKovD/wwJIFH90ob5cZDIZ\nS9lCcQNgXtXVwO6jfBJ7td9e3Be9evqwEu9AxKyKbeIebkMfOlIxRpE9hB5JAoS2\nbd2bHgAqfISsq18xWEmAdhiVlb3iGWQW8RQd8LkZAoGBAMcIMSL0xb0fyE0ZiXES\ncY0FRXac8Vbvh7NVlRFJ6MZsdOdrmcloIIksVbAA7yviEzZCFWUB2Lnsgk17kMR1\na5cI/Uc04ZwV8CnHwOZSESEMDhoKA+Zo8ufuqzEQ+HWj9V5DaCtUb8eSQWxNHPzO\nCxWelIG4Z0ZzWfPqMHGDbX7p\n-----END PRIVATE KEY-----\n", "client_email": "sufeisufeiko@tidy-visitor-504517-b0.iam.gserviceaccount.com", "client_id": "110736427458895537620", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sufeisufeiko%40tidy-visitor-504517-b0.iam.gserviceaccount.com", "universe_domain": "googleapis.com"}"
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
    except Exception:
        log.exception("Failed to write to sheet")
        await update.message.reply_text("Не получилось записать в таблицу. Проверьте настройки доступа.")
 
 
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("Bot started, polling...")
    app.run_polling()
 
 
if __name__ == "__main__":
    main()
