# https://docs.pyrogram.org/topics/create-filters

from typing import Union
from scripts import gvars, util
from pyrogram import filters
from pyrogram.types import Message, CallbackQuery


async def group_conv_trigger_func(_, __, m: Message) -> bool:
    if m.reply_to_message and m.from_user and not m.from_user.is_self:
        rm = m.reply_to_message
        if rm.from_user and rm.from_user.is_self:
            return True
    return False


async def global_access_filter_func(
    _, __, update: Union[Message, CallbackQuery]
) -> bool:
    scope = gvars.scope_global
    chat_id = (
        isinstance(update, Message)
        and update.chat.id
        or isinstance(update, CallbackQuery)
        and update.message.chat.id
    )
    access_check = util.access_scope_filter(scope, chat_id)
    return not access_check


group_conv_trigger = filters.create(group_conv_trigger_func)
global_access_filter = filters.create(global_access_filter_func)
