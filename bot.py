from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from kaspi import KaspiParser
from intertop import IntertopParser
from wildberries import WildberriesParser
import asyncio

BOT_TOKEN = "7765941206:AAHEEqWZU1JIh0ZypRG5RZBQMbCQPrCzF88"

# Store user choices
user_choices = {}

kaspi_parser = KaspiParser()
intertop_parser = IntertopParser()
wildberries_parser = WildberriesParser()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_choices.pop(user_id, None)

    await update.message.reply_text(
        "🛒 Where do you want to parse a product from?\n"
        "1 - Kaspi\n"
        "2 - Intertop\n"
        "3 - Wildberries"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Step 1: Choose source
    if user_id not in user_choices:
        if text not in ["1", "2", "3"]:
            await update.message.reply_text("❗ Please choose 1, 2, or 3.")
            return

        user_choices[user_id] = {
            "source": text,
            "step": "awaiting_url"
        }

        await update.message.reply_text("⏳ Great! Now wait 5 seconds...")
        await asyncio.sleep(5)
        await update.message.reply_text("🔗 Please send the product link now.")
        return

    # Step 2: Parse the link
    elif user_choices[user_id]["step"] == "awaiting_url":
        url = text
        source = user_choices[user_id]["source"]

        await update.message.reply_text("🔍 Parsing, please wait...")

        if source == "1":
            price, title = kaspi_parser.parse_product(url)
        elif source == "2":
            price, title = intertop_parser.parse_product(url)
        elif source == "3":
            price, title = wildberries_parser.parse_product(url)
        else:
            await update.message.reply_text("⚠️ Invalid source.")
            return

        if price and title:
            await update.message.reply_text(f"🛍️ Product: {title}\n💰 Price: {price} ₸")
        else:
            await update.message.reply_text("❌ Failed to parse product details. Check the link.")

        # Reset user state
        user_choices.pop(user_id, None)
        return

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()
