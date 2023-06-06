from typing import Optional
from scripts import globals
from scripts.chatdata import ChatData, GroupChatData
from pyrogram import enums
from pyrogram.types import Chat, Message


def load_chat(
    chat_id: int, create_new: bool = False, is_group: bool = False
) -> Optional[ChatData]:
    if chat_id in globals.allchats:
        return globals.allchats[chat_id]
    elif globals.db_chatdata.exists(chat_id):
        data = globals.db_chatdata.get(chat_id)
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
