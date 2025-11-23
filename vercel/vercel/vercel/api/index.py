import os
import re
import io
import time
import json
import asyncio
from PIL import Image
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mysecret")
ASK_ADDR = 1

def _norm(txt: str) -> str:
    txt = (txt or "").strip()
    m = re.search(r'(0x[a-fA-F0-9]{40})', txt)
    if m:
        return f"https://hyperdash.info/trader/{m.group(1)}"
    return txt if txt.startswith("http") else txt

def _shot_url(url: str) -> str:
    return f"https://image.thum.io/get/fullpage/{url}"

def _fetch_and_crop_bottom(url: str, bottom_ratio: float = 0.40):
    for _ in range(3):
        r = requests.get(_shot_url(url), timeout=60)
        if r.ok and r.headers.get("Content-Type", "").startswith("image"):
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            w, h = img.size
            top = int(h * (1.0 - bottom_ratio))
            crop = img.crop((0, top, w, h))
            buf = io.BytesIO()
            crop.save(buf, format="JPEG", quality=90)
            buf.seek(0)
            return buf.read()
        time.sleep(2)
    return None

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("Tracking whale", callback_data="track")]]
    await update.message.reply_text("Bot is alive. انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

async def on_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("آدرس 0x یا لینک hyperdash را بفرست.")
    return ASK_ADDR

async def on_addr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = _norm(update.message.text)

    if not url.startswith("http"):
        await update.message.reply_text("ورودی نامعتبر است.")
        return ConversationHandler.END

    await update.message.reply_text("در حال گرفتن اسکرین‌شات از بخش پایینی صفحه…")

    img = _fetch_and_crop_bottom(url)
    if img:
        await update.message.reply_photo(img, caption="Asset Positions (screenshot)")
    else:
        await update.message.reply_text("اسکرین‌شات نشد. دوباره تلاش کن.")

    return ConversationHandler.END

application = ApplicationBuilder().token(BOT_TOKEN).build()

conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(on_menu, pattern="^track$")],
    states={ASK_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_addr)]},
    fallbacks=[CommandHandler("start", cmd_start)],
    allow_reentry=True
)

application.add_handler(CommandHandler("start", cmd_start))
application.add_handler(conv)

async def handler(request):
    if request.method != "POST":
        return {"statusCode": 200, "body": "OK"}

    body = await request.json()

    if body.get("secret") != WEBHOOK_SECRET:
        return {"statusCode": 401, "body": "Unauthorized"}

    update = Update.de_json(body["update"], application.bot)
    await application.process_update(update)

    return {"statusCode": 200, "body": "done"}
