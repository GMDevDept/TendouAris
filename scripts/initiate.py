import os
from pyrogram import Client, errors
from pyrogram.types import (
    ChatPrivileges,
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllChatAdministrators,
)


async def set_bot_commands(app: Client):
    commands_common = [
        BotCommand("aris", "パンパカパーン！"),
        BotCommand("pop", "清除上次问答记忆，继续当前对话"),
        BotCommand("reset", "清除全部问答记忆，开始新的对话"),
        BotCommand("apikey", "为当前会话添加OpenAI API key"),
        BotCommand("chatid", "获取当前会话的chat ID"),
        BotCommand("help", "爱丽丝食用指南"),
        BotCommand("version", "查看版本信息"),
    ]
    await app.set_bot_commands(commands_common)

    commands_private = [
        BotCommand("aris", "パンパカパーン！"),
        BotCommand("pop", "清除上次问答记忆，继续当前对话"),
        BotCommand("reset", "清除全部问答记忆，开始新的对话"),
        BotCommand("model", "选择语言模型"),
        BotCommand("apikey", "为当前会话添加OpenAI API key"),
        BotCommand("chatid", "获取当前会话的chat ID"),
        BotCommand("help", "爱丽丝食用指南"),
        BotCommand("version", "查看版本信息"),
    ]
    await app.set_bot_commands(commands_private, scope=BotCommandScopeAllPrivateChats())

    commands_group_admin = [
        BotCommand("aris", "パンパカパーン！"),
        BotCommand("pop", "清除上次问答记忆，继续当前对话"),
        BotCommand("reset", "清除全部问答记忆，开始新的对话"),
        BotCommand("model", "选择语言模型"),
        BotCommand("apikey", "为当前会话添加OpenAI API key"),
        BotCommand("chatid", "获取当前会话的chat ID"),
        BotCommand("help", "爱丽丝食用指南"),
        BotCommand("version", "查看版本信息"),
    ]
    await app.set_bot_commands(
        commands_group_admin, scope=BotCommandScopeAllChatAdministrators()
    )

    commands_manager = [
        BotCommand("aris", "パンパカパーン！"),
        BotCommand("pop", "清除上次问答记忆，继续当前对话"),
        BotCommand("reset", "清除全部问答记忆，开始新的对话"),
        BotCommand("model", "选择语言模型"),
        BotCommand("apikey", "为当前会话添加OpenAI API key"),
        BotCommand("chatid", "获取当前会话的chat ID"),
        BotCommand("help", "爱丽丝食用指南"),
        BotCommand("version", "查看版本信息"),
        BotCommand("manage", "进入管理模式"),
    ]
    manager = [int(i) for i in os.getenv("MANAGER").split(",")]
    for chat_id in manager:
        await app.set_bot_commands(commands_manager, scope=BotCommandScopeChat(chat_id))


async def set_bot_default_privileges(app: Client):
    try:
        await app.set_bot_default_privileges(ChatPrivileges(can_manage_chat=True))
    except errors.exceptions.bad_request_400.BadRequest:
        # 400 Bad Request - RIGHTS_NOT_MODIFIED (target privilege is same as before)
        pass


async def initiate_bot(app: Client):
    await set_bot_commands(app)
    await set_bot_default_privileges(app)
