from typing import Optional, Union
from scripts import gvars
from scripts.chatdata import ChatData, GroupChatData
from pyrogram import enums, Client
from pyrogram.types import Chat, Message, CallbackQuery
from pyrogram.errors import UserNotParticipant


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


async def is_group_update_from_admin(
    client: Client, update: Union[Message, CallbackQuery]
) -> bool:
    chat = (
        isinstance(update, Message)
        and update.chat
        or isinstance(update, CallbackQuery)
        and update.message.chat
    )

    if update.from_user:
        try:
            sender = await client.get_chat_member(
                chat_id=chat.id, user_id=update.from_user.id
            )
            if sender.privileges:
                return True
        except (
            UserNotParticipant
        ):  # Anonymous admin will send callback query as user, but their id cannot be get using get_chat_member
            if isinstance(update, CallbackQuery):
                return True
    elif update.sender_chat and update.sender_chat.id == chat.id:
        return True

    return False


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
