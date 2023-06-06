# https://docs.pyrogram.org/topics/create-filters

from pyrogram import filters
from pyrogram.types import Message


async def func(_, __, m: Message) -> bool:
    if m.reply_to_message and m.from_user and not m.from_user.is_self:
        rm = m.reply_to_message
        if rm.from_user and rm.from_user.is_self:
            return True
    return False


group_conv_trigger = filters.create(func)
