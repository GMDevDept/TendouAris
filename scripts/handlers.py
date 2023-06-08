import re
import openai
import random
import logging
import traceback
from typing import Union
from scripts import gvars, strings
from scripts.util import load_chat, is_group, get_raw_text
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
)
from pyrogram.errors import RPCError


# Global access filter
async def global_access_filter_handler(update: Union[Message, CallbackQuery]):
    message = (
        isinstance(update, Message)
        and update
        or isinstance(update, CallbackQuery)
        and update.message
    )
    if message:
        await message.reply(strings.no_auth)


# Welcome/help message
async def help_handler(message):
    try:
        sender = message.from_user
        name = f"{sender.first_name and sender.first_name or ''} {sender.last_name and sender.last_name or ''}".strip()
    except AttributeError:
        name = ""
    await message.reply(strings.manual.format(name))


# Version info and update log
async def version_handler(message):
    await message.reply(strings.version)


# Get current chat id
async def chatid_handler(message):
    await message.reply(f"Chat ID: `{message.chat.id}`")


# Model selection
async def model_selection_handler(message):
    await message.reply(
        strings.choose_model,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        strings.models.get("model-gpt35"), callback_data="model-gpt35"
                    )
                ],
                [
                    InlineKeyboardButton(
                        strings.models.get("model-bing"), callback_data="model-bing"
                    )
                ],
                [
                    InlineKeyboardButton(
                        strings.models.get("model-bard"), callback_data="model-bard"
                    )
                ],
            ]
        ),
    )


# Model selection callback
async def model_selection_callback_handler(query):
    modelname = query.data.replace("model-", "")
    if modelname == "gpt35":
        chatdata = load_chat(query.message.chat.id)
        if chatdata and chatdata.openai_api_key:
            await query.message.edit(
                strings.model_choose_preset,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                strings.gpt35_presets.get("aris"),
                                callback_data="gpt35preset-aris",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                strings.gpt35_presets.get("default"),
                                callback_data="gpt35preset-default",
                            )
                        ],
                    ]
                ),
            )
        else:
            await query.message.edit(f"{strings.no_auth}\n\n{strings.api_key_required}")
    elif modelname == "bing":
        await query.message.edit(
            strings.bing_choose_style,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "creative",
                            callback_data="bingstyle-creative",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "balanced",
                            callback_data="bingstyle-balanced",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "precise",
                            callback_data="bingstyle-precise",
                        )
                    ],
                ]
            ),
        )
    elif modelname == "bard":
        if not gvars.google_bard_cookie:
            await query.message.edit(strings.bard_cookie_unavailable)
        else:
            await query.message.edit(
                strings.model_choose_preset,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                strings.bard_presets.get("default"),
                                callback_data="bardpreset-default",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                strings.bard_presets.get("cn"),
                                callback_data="bardpreset-cn",
                            )
                        ],
                    ]
                ),
            )


# GPT-3.5 preset selection callback
async def gpt35_preset_selection_callback_handler(query):
    preset = query.data.replace("gpt35preset-", "")
    chatdata = load_chat(query.message.chat.id)
    chatdata.set_model(
        {
            "name": "gpt35",
            "args": {"preset": preset},
        }
    )

    await query.message.edit(
        strings.model_changed
        + strings.models.get("model-gpt35")
        + f" ({strings.gpt35_presets.get(preset).split(' ')[0]})"
    )


# Bing style selection callback
async def bing_style_selection_callback_handler(query):
    style = query.data.replace("bingstyle-", "")
    chatdata = load_chat(
        query.message.chat.id,
        create_new=True,
        is_group=await is_group(query.message.chat),
    )
    chatdata.set_model({"name": "bing", "args": {"style": style}})

    await query.message.edit(
        strings.model_changed + strings.models.get("model-bing") + f" ({style})"
    )


# Bard preset selection callback
async def bard_preset_selection_callback_handler(query):
    preset = query.data.replace("bardpreset-", "")
    chatdata = load_chat(
        query.message.chat.id,
        create_new=True,
        is_group=await is_group(query.message.chat),
    )
    chatdata.set_model({"name": "bard", "args": {"preset": preset}})

    await query.message.edit(
        strings.model_changed
        + strings.models.get("model-bard")
        + f" ({strings.bard_presets.get(preset).split(' ')[0]})"
    )


# Set OpenAI API key
async def api_key_handler(message):
    api_key_input = re.sub(r"^/\S*\s*", "", message.text)
    if api_key_input.startswith("sk-"):
        try:
            await openai.ChatCompletion.acreate(
                api_key=api_key_input,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Test message, please reply '1'"}
                ],
            )

            chatdata = load_chat(
                message.chat.id, create_new=True, is_group=await is_group(message.chat)
            )
            chatdata.set_api_key(api_key_input)
            await message.reply(strings.api_key_set)
        except openai.error.OpenAIError as e:
            await message.reply(
                f"{strings.api_key_invalid}\n\nError message:`{e}`\n\n{strings.api_key_common_errors}"
            )
    else:
        await message.reply(strings.api_key_invalid)


# Conversation
async def conversation_handler(message):
    chatdata = load_chat(message.chat.id)
    if not chatdata:
        await message.reply(f"{strings.no_auth}\n\n{strings.api_key_required}")
    else:
        raw_text = await get_raw_text(message)
        input_text = re.sub(r"^/\S*\s*", "", raw_text)

        if message.reply_to_message:
            context = await get_raw_text(message.reply_to_message)
            input_text = f'Context: "{context}";\n{input_text}'

        model_name = chatdata.model.get("name")
        if model_name == "bing":
            placeholder = await message.reply(
                random.choice(strings.placeholder_before_output)
                + strings.placeholer_bing,
                disable_notification=True,
            )

        try:
            model_output = await chatdata.process_message(input_text)
            text = model_output.get("text")
            photo = model_output.get("photo")
            send_text_seperately = model_output.get("send_text_seperately")

            try:
                await placeholder.delete()
            except NameError:
                pass

            if not photo or send_text_seperately:
                await message.reply(
                    text,
                    quote=True,
                )

            if photo:
                if len(photo) == 1:
                    await message.reply_photo(photo[0], quote=True)
                else:
                    # media group length limit: 2-10
                    for i in range(0, len(photo), 10):
                        photo_group = photo[i : i + 10]
                        if len(photo_group) == 1 and i > 0:
                            photo_group.insert(0, photo[i - 1])
                        await message.reply_media_group(photo_group, quote=True)
        except RPCError as e:
            error_message = f"{e}: " + "".join(traceback.format_tb(e.__traceback__))
            logging.error(error_message)
            await message.reply(
                f"{strings.rpc_error}\n\nError message:\n`{error_message}`"
            )
        except Exception as e:
            error_message = f"{e}: " + "".join(traceback.format_tb(e.__traceback__))
            logging.error(error_message)
            await message.reply(
                f"{strings.internal_error}\n\nError message:\n`{error_message}`\n\n{strings.feedback}",
                quote=False,
            )


# Reset chat history
async def reset_handler(message):
    chatdata = load_chat(message.chat.id)
    if chatdata:
        if chatdata.openai_history:
            chatdata.openai_history = None
        if chatdata.bing_chatbot:
            await chatdata.bing_chatbot.close()
            chatdata.bing_chatbot = None
        if chatdata.bard_chatbot:
            chatdata.bard_chatbot = None

    await message.reply(strings.history_cleared)


# Manage mode
async def manage_mode_handler(message):
    await message.reply(
        strings.manage_mode_start,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        strings.manage_mode_options.get("scope-global"),
                        callback_data="manage-scope-global",
                    )
                ],
                [
                    InlineKeyboardButton(
                        strings.manage_mode_options.get("scope-gpt35"),
                        callback_data="manage-scope-gpt35",
                    )
                ],
                [
                    InlineKeyboardButton(
                        strings.manage_mode_options.get("scope-bing"),
                        callback_data="manage-scope-bing",
                    )
                ],
                [
                    InlineKeyboardButton(
                        strings.manage_mode_options.get("scope-bard"),
                        callback_data="manage-scope-bard",
                    )
                ],
            ]
        ),
    )


# Manage mode callback
async def manage_mode_callback_handler(client, query):
    if re.match(r"^manage-scope-(global|gpt35|bing|bard)$", query.data):
        await query.message.edit(
            strings.manage_mode_choose_scope,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            strings.manage_mode_scopes.get("all"),
                            callback_data=query.data + "-all",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            strings.manage_mode_scopes.get("whitelist"),
                            callback_data=query.data + "-whitelist",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            strings.manage_mode_scopes.get("manager"),
                            callback_data=query.data + "-manager",
                        )
                    ],
                ]
            ),
        )
    elif re.match(
        r"^manage-scope-(global|gpt35|bing|bard)-(all|whitelist|manager)$", query.data
    ):
        match = re.match(
            r"^manage-scope-(global|gpt35|bing|bard)-(all|whitelist|manager)$",
            query.data,
        )
        model = match.group(1)
        scope = match.group(2)
        setattr(gvars, "scope_" + model, scope)
        await query.message.edit(
            f"Scope of access to `{model}` has been set to `{scope}`"
        )
