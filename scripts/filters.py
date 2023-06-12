# https://docs.pyrogram.org/topics/create-filters

import re
from typing import Union
from scripts import gvars, util
from pyrogram import filters
from pyrogram.types import Message, CallbackQuery, ForceReply


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


global_access_filter = filters.create(global_access_filter_func)


async def group_conv_trigger_func(_, __, message: Message) -> bool:
    if message.reply_to_message and message.from_user and not message.from_user.is_self:
        rm = message.reply_to_message
        if rm.from_user and rm.from_user.is_self:
            return True
    return False


group_conv_trigger = filters.create(group_conv_trigger_func)


async def custom_preset_filter_func(_, __, message: Message) -> bool:
    rm = message.reply_to_message
    if (
        rm
        and (rm.reply_markup and isinstance(rm.reply_markup, ForceReply))
        and (rm.from_user and rm.from_user.is_self)
        and (rm.text and re.match(r"^\s*\[(\S*)\sModel Custom Preset\]", rm.text))
    ):
        return True
    else:
        return False


custom_preset_filter = filters.create(custom_preset_filter_func)
