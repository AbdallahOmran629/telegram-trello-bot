import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load secrets
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")

BASE_URL = "https://api.trello.com/1"
logging.basicConfig(level=logging.INFO)

# --- Trello API helpers ---
def get_boards():
    url = f"{BASE_URL}/members/me/boards"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    return requests.get(url, params=params).json()

def get_board_id(board_name):
    boards = get_boards()
    board = next((b for b in boards if b["name"] == board_name), None)
    return board["id"] if board else None

def get_lists(board_id):
    url = f"{BASE_URL}/boards/{board_id}/lists"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    return requests.get(url, params=params).json()

def get_list_id(board_id, list_name):
    lists = get_lists(board_id)
    for lst in lists:
        if lst["name"] == list_name:
            return lst["id"]
    return None

def get_cards(list_id):
    url = f"{BASE_URL}/lists/{list_id}/cards"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    return requests.get(url, params=params).json()

def create_card(list_id, card_name):
    url = f"{BASE_URL}/cards"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "idList": list_id,
        "name": card_name
    }
    return requests.post(url, params=params)

def move_card(card_name, src_list_id, dest_list_id):
    cards = get_cards(src_list_id)
    card = next((c for c in cards if c["name"] == card_name), None)
    if not card:
        return None
    url = f"{BASE_URL}/cards/{card['id']}"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN, "idList": dest_list_id}
    return requests.put(url, params=params)

def comment_card(card_id, comment):
    url = f"{BASE_URL}/cards/{card_id}/actions/comments"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN, "text": comment}
    return requests.post(url, params=params)

def delete_card(card_name, list_id):
    cards = get_cards(list_id)
    card = next((c for c in cards if c["name"] == card_name), None)
    if not card:
        return None
    url = f"{BASE_URL}/cards/{card['id']}"
    params = {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}
    return requests.delete(url, params=params)

# --- Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! I'm your Trello Bot. Use /help to see what I can do.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
Available Commands:
/start - Welcome message
/help - This help message
/list_boards - Show Trello boards
/list_cards <board> <list> - Show cards in a list
/add_card <board> <list> <name> - Create card
/move_card <board> <from_list> <to_list> <card_name>
/comment_card <board> <list> <card_name> <comment>
/delete_card <board> <list> <card_name>
"""
    await update.message.reply_text(help_text)

async def list_boards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    boards = get_boards()
    msg = "📋 Trello Boards:\n" + "\n".join([f"- {b['name']}" for b in boards])
    await update.message.reply_text(msg)

async def list_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /list_cards <board> <list>")
    board_name, list_name = context.args[0], context.args[1]
    board_id = get_board_id(board_name)
    if not board_id:
        return await update.message.reply_text("Board not found.")
    list_id = get_list_id(board_id, list_name)
    if not list_id:
        return await update.message.reply_text("List not found.")
    cards = get_cards(list_id)
    msg = "📝 Cards:\n" + "\n".join([f"- {c['name']}" for c in cards])
    await update.message.reply_text(msg or "No cards.")

async def add_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        return await update.message.reply_text("Usage: /add_card <board> <list> <card name>")
    board_name, list_name = context.args[0], context.args[1]
    card_name = " ".join(context.args[2:])
    board_id = get_board_id(board_name)
    if not board_id:
        return await update.message.reply_text("Board not found.")
    list_id = get_list_id(board_id, list_name)
    if not list_id:
        return await update.message.reply_text("List not found.")
    res = create_card(list_id, card_name)
    await update.message.reply_text("✅ Card created." if res.status_code == 200 else "❌ Failed to create card.")

async def move_card_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 4:
        return await update.message.reply_text("Usage: /move_card <board> <from_list> <to_list> <card_name>")
    board_name, from_list, to_list = context.args[0], context.args[1], context.args[2]
    card_name = " ".join(context.args[3:])
    board_id = get_board_id(board_name)
    if not board_id:
        return await update.message.reply_text("Board not found.")
    src_list_id = get_list_id(board_id, from_list)
    dest_list_id = get_list_id(board_id, to_list)
    if not src_list_id or not dest_list_id:
        return await update.message.reply_text("List(s) not found.")
    res = move_card(card_name, src_list_id, dest_list_id)
    await update.message.reply_text("✅ Card moved." if res and res.status_code == 200 else "❌ Failed to move card.")

async def comment_card_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 4:
        return await update.message.reply_text("Usage: /comment_card <board> <list> <card_name> <comment>")
    board_name, list_name = context.args[0], context.args[1]
    card_name = context.args[2]
    comment = " ".join(context.args[3:])
    board_id = get_board_id(board_name)
    list_id = get_list_id(board_id, list_name)
    cards = get_cards(list_id)
    card = next((c for c in cards if c['name'] == card_name), None)
    if not card:
        return await update.message.reply_text("Card not found.")
    res = comment_card(card['id'], comment)
    await update.message.reply_text("💬 Comment added." if res.status_code == 200 else "❌ Failed to comment.")

async def delete_card_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        return await update.message.reply_text("Usage: /delete_card <board> <list> <card_name>")
    board_name, list_name = context.args[0], context.args[1]
    card_name = " ".join(context.args[2:])
    board_id = get_board_id(board_name)
    list_id = get_list_id(board_id, list_name)
    res = delete_card(card_name, list_id)
    await update.message.reply_text("🗑️ Card deleted." if res and res.status_code == 200 else "❌ Failed to delete card.")

# --- Main Bot Setup ---
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("list_boards", list_boards))
app.add_handler(CommandHandler("list_cards", list_cards))
app.add_handler(CommandHandler("add_card", add_card))
app.add_handler(CommandHandler("move_card", move_card_cmd))
app.add_handler(CommandHandler("comment_card", comment_card_cmd))
app.add_handler(CommandHandler("delete_card", delete_card_cmd))

if __name__ == "__main__":
    app.run_polling()
