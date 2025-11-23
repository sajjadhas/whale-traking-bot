import os
import re
import io
import time
from PIL import Image
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)
from telegram.ext import ApplicationBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN")
ASK_ADDR = 1

# ---------- Utility Functions ----------

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

# ---------- Bot Handlers ----------

async def cmd_start(u: Update, c: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("Tracking whale", callback_data="track")]]
    await u.message.reply_text("Bot is alive. انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

async def on_menu(u: Update, c: ContextTypes.DEFAULT_TYPE):
    q = u.callback_query
    await q.answer()
    await q.message.reply_text("آدرس 0x یا لینک hyperdash را ارسال کنید.")
    return ASK_ADDR

async def on_addr(u: Update, c: ContextTypes.DEFAULT_TYPE):
    url = _norm(u.message.text)
    if not url.startswith("http"):
        await u.message.reply_text("ورودی نامعتبر است.")
        return ConversationHandler.END

    await u.message.reply_text("در حال گرفتن اسکرین‌شات از بخش پایینی صفحه…")

    img = _fetch_and_crop_bottom(url)
    if img:
        await u.message.reply_photo(img, caption="Asset Positions (screenshot)")
    else:
        await u.message.reply_text("اسکرین‌شات انجام نشد. دوباره تلاش کن.")

    return ConversationHandler.END

# ---------- Vercel HTTP handler ----------

async def handler(request):
    if request.method != "POST":
        return {"status": "ok"}

    body = await request.json()
    update = Update.de_json(body, app.bot)
    await app.process_update(update)
    return {"status": "processed"}

# ---------- Initialize App ----------

def build_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(on_menu, pattern="^track$")],
        states={ASK_ADDR: [MessageHandler(filters.TEXT & ~filters.COMMAND, on_addr)]},
        fallbacks=[CommandHandler("start", cmd_start)],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(conv)
    return app

app = build_app()
