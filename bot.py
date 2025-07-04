# bot.py
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from api.kaspi import KaspiParser
from api.intertop import IntertopParser
from api.wildberries import WildberriesParser
from api.db import init_db, add_product, get_all_products, update_product_price
import asyncio
import nest_asyncio

BOT_TOKEN = "7765941206:AAHEEqWZU1JIh0ZypRG5RZBQMbCQPrCzF88"

user_choices = {}
kaspi_parser = KaspiParser()
intertop_parser = IntertopParser()
wildberries_parser = WildberriesParser()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_choices.pop(user_id, None)
    await update.message.reply_text(
        "Where do you want to parse a product from?\n"
        "1 - Kaspi\n"
        "2 - Intertop\n"
        "3 - Wildberries"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in user_choices:
        if text not in ["1", "2", "3"]:
            await update.message.reply_text("Please choose 1, 2, or 3.")
            return

        user_choices[user_id] = {
            "source": text,
            "step": "awaiting_url"
        }

        await update.message.reply_text("Great! Now wait 5 seconds...")
        await asyncio.sleep(5)
        await update.message.reply_text("Please send the product link now.")
        return

    elif user_choices[user_id]["step"] == "awaiting_url":
        url = text
        source = user_choices[user_id]["source"]

        await update.message.reply_text("Please wait...")

        if source == "1":
            price, title = kaspi_parser.parse_product(url)
        elif source == "2":
            price, title = intertop_parser.parse_product(url)
        elif source == "3":
            price, title = wildberries_parser.parse_product(url)
        else:
            await update.message.reply_text("Invalid source.")
            return

        if price and title:
            await update.message.reply_text(f"Product: {title}\nPrice: {price} ₸")
            add_product(user_id, source, url, price)
        else:
            await update.message.reply_text("Failed to parse product. Check the link.")

        user_choices.pop(user_id, None)

async def send_price_updates(app):
    products = get_all_products()

    for user_id, source, url, old_price in products:
        if source == "1":
            new_price, title = kaspi_parser.parse_product(url)
        elif source == "2":
            new_price, title = intertop_parser.parse_product(url)
        elif source == "3":
            new_price, title = wildberries_parser.parse_product(url)
        else:
            continue

        if new_price is None or title is None:
            continue

        if new_price != old_price:
            message = (
                "<b>Price Changed!</b>\n"
                f"<b>Product:</b> {title}\n"
                f"<b>Old Price:</b> {old_price} ₸\n"
                f"<b>New Price:</b> {new_price} ₸"
            )
            await app.bot.send_message(chat_id=user_id, text=message, parse_mode="HTML")
            update_product_price(url, new_price)
        else:
            # If price hasn't changed
            await app.bot.send_message(
                chat_id=user_id,
                text=f"No change: {title}"
            )

async def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_price_updates, 'interval', hours = 1 , args=[app])
    scheduler.start()

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        nest_asyncio.apply()
        asyncio.get_event_loop().run_until_complete(main())
