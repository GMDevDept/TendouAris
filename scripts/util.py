from typing import Optional
from scripts import gvars
from scripts.chatdata import ChatData, GroupChatData
from pyrogram import enums
from pyrogram.types import Chat, Message


def load_chat(
    chat_id: int, create_new: bool = False, is_group: bool = False
) -> Optional[ChatData]:
    if chat_id in gvars.all_chats:
        return gvars.all_chats[chat_id]
    elif gvars.db_chatdata.exists(chat_id):
        data = gvars.db_chatdata.get(chat_id)
        return ChatData.load(data)
    elif create_new:
        if is_group:
            return GroupChatData(chat_id)
        else:
            return ChatData(chat_id)
    else:
        return None


async def is_group(chat: Chat) -> bool:
    return bool(chat.type in {enums.ChatType.GROUP, enums.ChatType.SUPERGROUP})


async def get_raw_text(message: Message) -> str:
    return (
        message.text
        or message.caption
        or message.sticker
        and message.sticker.emoji
        or ""
    )


def access_scope_filter(scope: str, chat_id: int) -> bool:
    match scope:
        case "all":
            return True
        case "whitelist":
            return chat_id in gvars.whitelist
        case "manager":
            return chat_id in gvars.manager
        case _:
            raise ValueError(f"Invalid access scope: {scope}")
