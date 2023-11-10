import os
import json
import base64
import logging
import importlib
from scripts import gvars, util
from pyrogram import Client, errors
from pyrogram.types import (
    ChatPrivileges,
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllChatAdministrators,
)


async def set_bot_commands(client: Client):
    commands_common = [
        BotCommand("aris", "パンパカパーン！"),
        BotCommand("draw", "图像生成"),
        BotCommand("reset", "重置对话历史"),
        BotCommand("apikey", "为当前会话添加API key"),
        BotCommand("help", "爱丽丝食用指南"),
        BotCommand("version", "查看版本及更新信息"),
    ]
    await client.set_bot_commands(commands_common)

    commands_private = [
        BotCommand("aris", "パンパカパーン！"),
        BotCommand("draw", "图像生成"),
        BotCommand("model", "选择语言模型"),
        BotCommand("reset", "重置对话历史"),
        BotCommand("apikey", "为当前会话添加API key"),
        BotCommand("chatid", "获取当前会话的chat ID"),
        BotCommand("help", "爱丽丝食用指南"),
        BotCommand("version", "查看版本及更新信息"),
    ]
    await client.set_bot_commands(
        commands_private, scope=BotCommandScopeAllPrivateChats()
    )

    commands_group_admin = [
        BotCommand("aris", "パンパカパーン！"),
        BotCommand("draw", "图像生成"),
        BotCommand("model", "选择语言模型"),
        BotCommand("reset", "重置对话历史"),
        BotCommand("apikey", "为当前会话添加API key"),
        BotCommand("chatid", "获取当前会话的chat ID"),
        BotCommand("help", "爱丽丝食用指南"),
        BotCommand("version", "查看版本及更新信息"),
        BotCommand("setting", "当前群聊设置 (不支持频道身份)"),
    ]
    await client.set_bot_commands(
        commands_group_admin, scope=BotCommandScopeAllChatAdministrators()
    )

    commands_manager = [
        BotCommand("aris", "パンパカパーン！"),
        BotCommand("draw", "图像生成"),
        BotCommand("model", "选择语言模型"),
        BotCommand("reset", "重置对话历史"),
        BotCommand("apikey", "为当前会话添加API key"),
        BotCommand("chatid", "获取当前会话的chat ID"),
        BotCommand("help", "爱丽丝食用指南"),
        BotCommand("version", "查看版本及更新信息"),
        BotCommand("manage", "进入全局管理模式"),
    ]
    for chat_id in gvars.manager:
        await client.set_bot_commands(
            commands_manager, scope=BotCommandScopeChat(chat_id)
        )


async def set_bot_default_privileges(client: Client):
    try:
        await client.set_bot_default_privileges(ChatPrivileges(can_manage_chat=True))
    except errors.exceptions.bad_request_400.BadRequest:
        # 400 Bad Request - RIGHTS_NOT_MODIFIED (target privilege is same as before)
        pass


async def initiate_bot(client: Client):
    await set_bot_commands(client)
    await set_bot_default_privileges(client)


# Load add-on presets
def load_preset_addons():
    for filename in os.listdir("presets"):
        if filename.endswith(".py"):
            module = importlib.import_module(f"presets.{filename[:-3]}")
            module_dict = {
                k: v for k, v in vars(module).items() if not k.startswith("_")
            }
            if module_dict.get("base64_encoded"):
                module_dict["prompt"] = base64.b64decode(module_dict["prompt"]).decode()
            if "gpt35" in module.compatible_models:
                gvars.gpt35_addons.update({module.id: module_dict})
            if "gpt4" in module.compatible_models:
                gvars.gpt4_addons.update({module.id: module_dict})


# Create profile for chats in whitelist
def setup_whitelist():
    for chat_id in gvars.whitelist:
        if not gvars.db_chatdata.exists(chat_id):
            # Append to db only, not using .save() here to avoid miscounting active chats
            chatdata = util.load_chat(chat_id, create_new=True, is_group=chat_id < 0)
            gvars.db_chatdata.set(chat_id, json.dumps(chatdata.persistent_data))


# Initialte chatbot clients
async def start_chatbot_clients():
    try:
        await gvars.bing_client.init()
    except Exception:
        logging.error(
            "Error happened when initiating Bing client. Is cookie file valid?"
        )

    try:
        await gvars.claude_client.init()
    except Exception:
        logging.error(
            "Error happened when initiating Claude client. Is cookie file valid?"
        )
