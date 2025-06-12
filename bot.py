import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from dotenv import load_dotenv
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API credentials from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_API_TOKEN = os.getenv("TRELLO_API_TOKEN")

# Trello API base
BASE_URL = "https://api.trello.com/1"

# Trello API Functions
def get_boards():
    url = f"{BASE_URL}/members/me/boards?key={TRELLO_API_KEY}&token={TRELLO_API_TOKEN}"
    return requests.get(url).json()

def get_lists(board_id):
    url = f"{BASE_URL}/boards/{board_id}/lists?key={TRELLO_API_KEY}&token={TRELLO_API_TOKEN}"
    return requests.get(url).json()

def get_cards(list_id):
    url = f"{BASE_URL}/lists/{list_id}/cards?key={TRELLO_API_KEY}&token={TRELLO_API_TOKEN}"
    return requests.get(url).json()

# Telegram Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your Trello bot 🤖")

# Telegram Command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show help\n"
        "/list_boards - Show your Trello boards (with buttons)\n"
    )
    await update.message.reply_text(help_text)

# /list_boards — show board buttons
async def list_boards_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    boards = get_boards()
    keyboard = [
        [InlineKeyboardButton(board['name'], callback_data=f"board:{board['id']}")]
        for board in boards
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a board:", reply_markup=reply_markup)

# Handle board selection → show lists
async def board_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    board_id = query.data.split(":")[1]
    await query.answer()

    lists = get_lists(board_id)
    keyboard = [
        [InlineKeyboardButton(lst['name'], callback_data=f"list:{lst['id']}")]
        for lst in lists
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Select a list:", reply_markup=reply_markup)

# Handle list selection → show cards
async def list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    list_id = query.data.split(":")[1]
    await query.answer()

    cards = get_cards(list_id)
    if not cards:
        await query.edit_message_text("No cards found.")
    else:
        card_texts = [f"- {card['name']}" for card in cards]
        await query.edit_message_text("Cards:\n" + "\n".join(card_texts))

# Run the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("list_boards", list_boards_button))
    app.add_handler(CallbackQueryHandler(board_callback, pattern=r"^board:"))
    app.add_handler(CallbackQueryHandler(list_callback, pattern=r"^list:"))

    print("Bot is running...")
    app.run_polling()
