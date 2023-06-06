# https://docs.pyrogram.org
# https://python.langchain.com/en/latest/
# https://platform.openai.com/docs/guides/chat/introduction

import os
import uvloop
import logging
from scripts import handlers
from scripts.initiate import initiate_bot
from scripts.filters import group_conv_trigger
from pyrogram import Client, filters, idle

logging.basicConfig(
    format="[ %(levelname)s / %(asctime)s]: %(message)s", level=logging.INFO
)

# Load env variables
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
manager = [int(i) for i in os.getenv("MANAGER").split(",")]

# Telegram bot client
uvloop.install()  # Needs to be placed before creating a Client instance to take effect
app = Client("Aris", api_id, api_hash, bot_token=bot_token)


# Welcome/help message
@app.on_message(filters.command(["start", "help"]))
async def help_handler(_, message):
    await handlers.help_handler(message)


# Version info and update log
@app.on_message(filters.command("version"))
async def version_handler(_, message):
    await handlers.version_handler(message)


# Get current chat id
@app.on_message(filters.command("chatid"))
async def chatid_handler(_, message):
    await handlers.chatid_handler(message)


# Model selection
@app.on_message(filters.command("model"))
async def model_selection_handler(_, message):
    await handlers.model_selection_handler(message)


# Model selection callback
@app.on_callback_query(filters.regex(r"^model-"))
async def model_selection_callback_handler(_, query):
    await handlers.model_selection_callback_handler(query)


# Set OpenAI API key
@app.on_message(filters.command("apikey") & filters.text)
async def api_key_handler(_, message):
    await handlers.api_key_handler(message)


# Conversation
@app.on_message(
    ~filters.forwarded
    & (
        filters.command("aris")
        | filters.regex(r"^爱丽丝")
        | (filters.private & ~filters.regex(r"^/"))
        | (filters.group & group_conv_trigger)
    )
)
async def conversation_handler(_, message):
    await handlers.conversation_handler(message)


# Manage mode
@app.on_message(filters.command("manage") & filters.user(manager))
async def manage_mode_handler(_, message):
    await handlers.manage_mode_handler(message)


async def main():
    await app.start()
    await initiate_bot(app)
    await idle()
    await app.stop()


if __name__ == "__main__":
    app.run(main())
