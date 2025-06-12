import requests
import os

# Replace with your actual API credentials or set them as environment variables

API_KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_API_TOKEN")

# Replace with your actual board short ID (from Trello URL)
BOARD_SHORT_ID = "ncRrPl0C"

# Get full board ID
board_info = requests.get(
    f"https://api.trello.com/1/boards/{BOARD_SHORT_ID}",
    params={
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }
)

if board_info.status_code != 200:
    print("❌ Failed to get board info:", board_info.text)
    exit()

board_id = board_info.json()["id"]
print(f"✅ Full board ID: {board_id}")

# Replace with your Railway domain
CALLBACK_URL = "https://railway.com/project/ff41b3d4-cb0f-42fe-945f-6044f13e8fd9?environmentId=9281e559-7930-417d-bbd2-03cc1446e706"

# Create webhook
webhook_response = requests.post(
    "https://api.trello.com/1/webhooks",
    params={
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN,
        "callbackURL": CALLBACK_URL,
        "idModel": board_id,
        "description": "Telegram Bot Trello Webhook"
    }
)

if webhook_response.status_code == 200:
    print("✅ Webhook successfully created!")
else:
    print("❌ Failed to create webhook:", webhook_response.status_code, webhook_response.text)
