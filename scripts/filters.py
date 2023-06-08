# https://docs.pyrogram.org/topics/create-filters

import logging
from typing import Union
from scripts import gvars
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
    try:
        match scope:
            case "all":
                return False
            case "whitelist":
                if isinstance(update, Message):
                    return update.chat.id not in gvars.whitelist
                elif isinstance(update, CallbackQuery):
                    return update.message.chat.id not in gvars.whitelist
            case "manager":
                if isinstance(update, Message):
                    return update.chat.id not in gvars.manager
                elif isinstance(update, CallbackQuery):
                    return update.message.chat.id not in gvars.manager
    except Exception as e:
        logging.error(f"Error in global_access_filter_func: {e}")
        pass

    return True


group_conv_trigger = filters.create(group_conv_trigger_func)
global_access_filter = filters.create(global_access_filter_func)
