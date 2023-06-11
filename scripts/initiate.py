from scripts import gvars
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
        BotCommand("reset", "重置对话历史"),
        BotCommand("apikey", "为当前会话添加OpenAI API key"),
        BotCommand("chatid", "获取当前会话的chat ID"),
        BotCommand("help", "爱丽丝食用指南"),
        BotCommand("version", "查看版本及更新信息"),
    ]
    await client.set_bot_commands(commands_common)

    commands_private = [
        BotCommand("aris", "パンパカパーン！"),
        BotCommand("model", "选择语言模型"),
        BotCommand("reset", "重置对话历史"),
        BotCommand("apikey", "为当前会话添加OpenAI API key"),
        BotCommand("chatid", "获取当前会话的chat ID"),
        BotCommand("help", "爱丽丝食用指南"),
        BotCommand("version", "查看版本及更新信息"),
    ]
    await client.set_bot_commands(
        commands_private, scope=BotCommandScopeAllPrivateChats()
    )

    commands_group_admin = [
        BotCommand("aris", "パンパカパーン！"),
        BotCommand("model", "选择语言模型"),
        BotCommand("reset", "重置对话历史"),
        BotCommand("apikey", "为当前会话添加OpenAI API key"),
        BotCommand("chatid", "获取当前会话的chat ID"),
        BotCommand("help", "爱丽丝食用指南"),
        BotCommand("version", "查看版本及更新信息"),
    ]
    await client.set_bot_commands(
        commands_group_admin, scope=BotCommandScopeAllChatAdministrators()
    )

    commands_manager = [
        BotCommand("aris", "パンパカパーン！"),
        BotCommand("model", "选择语言模型"),
        BotCommand("reset", "重置对话历史"),
        BotCommand("apikey", "为当前会话添加OpenAI API key"),
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
