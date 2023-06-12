# https://docs.pyrogram.org
# https://python.langchain.com/en/latest/
# https://platform.openai.com/docs/guides/chat/introduction

import uvloop
import logging
from scripts import gvars, handlers, filters as custom_filters
from scripts.initiate import initiate_bot
from pyrogram import Client, filters, idle

logging.basicConfig(
    format="[ %(levelname)s / %(asctime)s]: %(message)s", level=logging.INFO
)

# Telegram bot client
uvloop.install()  # Needs to be placed before creating a Client instance to take effect
client = Client("Aris", gvars.api_id, gvars.api_hash, bot_token=gvars.bot_token)


# Global access filter for messages
@client.on_message(custom_filters.global_access_filter)
async def global_access_filter_chat_handler(_, message):
    await handlers.global_access_filter_handler(message)


# Global access filter for callback queries
@client.on_callback_query(custom_filters.global_access_filter)
async def global_access_filter_query_handler(_, query):
    await handlers.global_access_filter_handler(query)


# Welcome/help message
@client.on_message(filters.command(["start", "help"]))
async def help_handler(_, message):
    await handlers.help_handler(message)


# Version info and update log
@client.on_message(filters.command("version"))
async def version_handler(_, message):
    await handlers.version_handler(message)


# Get current chat id
@client.on_message(filters.command("chatid"))
async def chatid_handler(_, message):
    await handlers.chatid_handler(message)


# Model selection
@client.on_message(filters.command("model"))
async def model_selection_handler(_, message):
    await handlers.model_selection_handler(message)


# Model selection callback
@client.on_callback_query(filters.regex(r"^model-"))
async def model_selection_callback_handler(_, query):
    await handlers.model_selection_callback_handler(query)


# GPT-3.5 preset selection callback
@client.on_callback_query(filters.regex(r"^gpt35preset-"))
async def gpt35_preset_selection_callback_handler(client, query):
    await handlers.gpt35_preset_selection_callback_handler(client, query)


# Set custom preset
@client.on_message(custom_filters.custom_preset_filter)
async def custom_preset_handler(client, message):
    await handlers.custom_preset_handler(client, message)


# Bing style selection callback
@client.on_callback_query(filters.regex(r"^bingstyle-"))
async def bing_style_selection_callback_handler(_, query):
    await handlers.bing_style_selection_callback_handler(query)


# Bard preset selection callback
@client.on_callback_query(filters.regex(r"^bardpreset-"))
async def bard_preset_selection_callback_handler(_, query):
    await handlers.bard_preset_selection_callback_handler(query)


# Set OpenAI API key
@client.on_message(filters.command("apikey") & filters.text)
async def api_key_handler(_, message):
    await handlers.api_key_handler(message)


# Conversation
@client.on_message(
    ~filters.forwarded
    & (
        filters.command("aris")
        | filters.regex(r"^爱丽丝")
        | (filters.private & ~filters.regex(r"^/"))
        | (filters.group & custom_filters.group_conv_trigger)
    )
)
async def conversation_handler(client, message):
    await handlers.conversation_handler(client, message)


# Reset conversation history
@client.on_message(filters.command("reset"))
async def reset_handler(_, message):
    await handlers.reset_handler(message)


# Manage mode
@client.on_message(filters.command("manage") & filters.user(gvars.manager))
async def manage_mode_handler(_, message):
    await handlers.manage_mode_handler(message)


# Manage mode callback
@client.on_callback_query(filters.regex(r"^manage-") & filters.user(gvars.manager))
async def manage_mode_callback_handler(client, query):
    await handlers.manage_mode_callback_handler(client, query)


async def main():
    await client.start()
    await initiate_bot(client)
    await idle()
    await client.stop()


if __name__ == "__main__":
    client.run(main())
