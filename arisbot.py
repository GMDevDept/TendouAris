# https://docs.pyrogram.org
# https://python.langchain.com/en/latest/
# https://platform.openai.com/docs/guides/chat/introduction

import uvloop
import logging
from scripts import gvars, handlers, filters as custom_filters
from scripts.initiate import (
    initiate_bot,
    load_preset_addons,
    setup_whitelist,
    start_chatbot_clients,
)
from pyrogram import Client, filters, idle

logging.basicConfig(
    format="[ %(levelname)s / %(asctime)s]: %(message)s", level=logging.ERROR
)

# Telegram bot client
uvloop.install()  # Needs to be placed before creating a Client instance to take effect
client = Client("Aris", gvars.api_id, gvars.api_hash, bot_token=gvars.bot_token)


# Global access filter for messages
@client.on_message(custom_filters.global_access_filter)
async def global_access_filter_chat_handler(client, message):
    await handlers.global_access_filter_handler(client, message)


# Global access filter for callback queries
@client.on_callback_query(custom_filters.global_access_filter)
async def global_access_filter_query_handler(client, query):
    await handlers.global_access_filter_handler(client, query)


# Welcome/help message
@client.on_message(filters.command(["start", "help"]))
async def help_handler(client, message):
    await handlers.help_handler(client, message)


# Version info and update log
@client.on_message(filters.command("version"))
async def version_handler(client, message):
    await handlers.version_handler(client, message)


# Get current chat id
@client.on_message(filters.command("chatid"))
async def chatid_handler(client, message):
    await handlers.chatid_handler(client, message)


# Model selection
@client.on_message(filters.command("model"))
async def model_selection_handler(client, message):
    await handlers.model_selection_handler(client, message)


# Model selection callback
@client.on_callback_query(filters.regex(r"^model-"))
async def model_selection_callback_handler(client, query):
    await handlers.model_selection_callback_handler(client, query)


# Gemini Pro preset selection callback
@client.on_callback_query(filters.regex(r"^geminipreset-"))
async def gemini_preset_selection_callback_handler(client, query):
    await handlers.gemini_preset_selection_callback_handler(client, query)


# GPT-3.5 preset selection callback
@client.on_callback_query(filters.regex(r"^gpt35preset-"))
async def gpt35_preset_selection_callback_handler(client, query):
    await handlers.gpt35_preset_selection_callback_handler(client, query)


# GPT-4 preset selection callback
@client.on_callback_query(filters.regex(r"^gpt4preset-"))
async def gpt4_preset_selection_callback_handler(client, query):
    await handlers.gpt4_preset_selection_callback_handler(client, query)


# Set custom preset
@client.on_message(custom_filters.custom_preset_filter)
async def custom_preset_handler(client, message):
    await handlers.custom_preset_handler(client, message)


# Bing style selection callback
@client.on_callback_query(filters.regex(r"^bingstyle-"))
async def bing_style_selection_callback_handler(client, query):
    await handlers.bing_style_selection_callback_handler(client, query)


# Bard preset selection callback
@client.on_callback_query(filters.regex(r"^bardpreset-"))
async def bard_preset_selection_callback_handler(client, query):
    await handlers.bard_preset_selection_callback_handler(client, query)


# Claude preset selection callback
@client.on_callback_query(filters.regex(r"^claudepreset-"))
async def claude_preset_selection_callback_handler(client, query):
    await handlers.claude_preset_selection_callback_handler(client, query)


# Set OpenAI API key
@client.on_message(filters.command("apikey") & filters.text)
async def api_key_handler(client, message):
    await handlers.api_key_handler(client, message)


# Reset conversation history
@client.on_message(filters.command("reset"))
async def reset_handler(client, message):
    await handlers.reset_handler(client, message)


# Chat settings
@client.on_message(
    filters.command("setting") & filters.group & custom_filters.group_admin_filter
)
async def chat_setting_handler(client, message):
    await handlers.chat_setting_handler(client, message)


# Chat settings callback
@client.on_callback_query(
    filters.regex(r"^chat_setting-") & custom_filters.group_admin_filter
)
async def chat_setting_callback_handler(client, query):
    await handlers.chat_setting_callback_handler(client, query)


# Manage mode
@client.on_message(filters.command("manage") & filters.user(gvars.manager))
async def manage_mode_handler(client, message):
    await handlers.manage_mode_handler(client, message)


# Manage mode callback
@client.on_callback_query(filters.regex(r"^manage-") & filters.user(gvars.manager))
async def manage_mode_callback_handler(client, query):
    await handlers.manage_mode_callback_handler(client, query)


# Conversation
@client.on_message(
    ~filters.forwarded
    & (
        filters.command("aris")
        | filters.regex(r"^爱丽丝")
        | (filters.private & ~filters.regex(r"^/"))
        | (filters.group & ~filters.regex(r"^/") & custom_filters.group_conv_trigger)
    )
)
async def conversation_handler(client, message):
    await handlers.conversation_handler(client, message)


# Generate image
@client.on_message(filters.command("draw") & filters.text)
async def draw_handler(client, message):
    await handlers.draw_handler(client, message)


async def main():
    setup_whitelist()
    load_preset_addons()
    await client.start()
    await initiate_bot(client)
    await start_chatbot_clients()
    await idle()
    await client.stop()


if __name__ == "__main__":
    client.run(main())
