import re
import json
import openai
import random
import logging
import traceback
from typing import Union
from scripts import gvars, strings, util
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery,
    ForceReply,
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
        await message.reply(
            f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        )


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
        quote=True,
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
    scope = getattr(gvars, "scope_" + modelname)
    access_check = util.access_scope_filter(scope, query.message.chat.id)
    if not access_check:
        await query.message.edit(
            f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        )
    else:
        if modelname == "gpt35":
            chatdata = util.load_chat(query.message.chat.id)
            if chatdata and (
                chatdata.openai_api_key or chatdata.chat_id in gvars.whitelist
            ):
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
                            [
                                InlineKeyboardButton(
                                    strings.gpt35_presets.get("custom"),
                                    callback_data="gpt35preset-custom",
                                )
                            ],
                        ]
                    ),
                )
            else:
                await query.message.edit(
                    f"{strings.no_auth}\n\n{strings.api_key_required}"
                )
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
async def gpt35_preset_selection_callback_handler(client, query):
    preset = query.data.replace("gpt35preset-", "")
    chatdata = util.load_chat(
        query.message.chat.id,
        create_new=True,
        is_group=await util.is_group(query.message.chat),
    )

    match preset:
        case "custom":
            await query.message.edit(
                strings.manage_gpt35_custom_preset,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                strings.custom_preset_options.get("new"),
                                callback_data="gpt35preset-custom-new",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                strings.custom_preset_options.get("continue"),
                                callback_data="gpt35preset-custom-continue",
                            )
                        ],
                    ]
                ),
            )
        case "custom-new":
            await query.message.edit(
                strings.custom_preset_template, reply_markup=ForceReply(selective=True)
            )
        case "custom-continue":
            if not chatdata.gpt35_preset:
                await query.message.edit(strings.custom_preset_unavailable)
            else:
                if chatdata.gpt35_history is not None and not (
                    chatdata.model["name"] == "gpt35"
                    and chatdata.model["args"].get("preset") == "custom"
                ):
                    chatdata.gpt35_chatbot = None
                    chatdata.gpt35_history = None
                    await client.send_message(
                        chatdata.chat_id,
                        strings.model_reset_due_to_preset_change.format("GPT-3.5"),
                    )

                chatdata.set_model({"name": "gpt35", "args": {"preset": "custom"}})

                await query.message.edit(
                    strings.model_changed
                    + strings.models.get("model-gpt35")
                    + f" ({strings.gpt35_presets.get('custom').split(' ')[0]})"
                )
        case _:
            if chatdata.gpt35_history is not None and not (
                chatdata.model["name"] == "gpt35"
                and chatdata.model["args"].get("preset") == preset
            ):
                chatdata.gpt35_chatbot = None
                chatdata.gpt35_history = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_preset_change.format("GPT-3.5"),
                )

            chatdata.set_model({"name": "gpt35", "args": {"preset": preset}})

            await query.message.edit(
                strings.model_changed
                + strings.models.get("model-gpt35")
                + f" ({strings.gpt35_presets.get(preset).split(' ')[0]})"
            )


# Set custom preset
async def custom_preset_handler(client, message):
    chatdata = util.load_chat(message.chat.id)
    if not chatdata:
        await message.reply(strings.chatdata_unavailable)
    else:
        template_dict = None
        try:
            template_json = re.match(r".*?({.*}).*", message.text, re.DOTALL).group(1)
            template_dict = json.loads(template_json)
            assert len(template_dict) == 7, "Invalid template length"
            assert (
                isinstance(template_dict["prompt"], str)
                and isinstance(template_dict["ai_prefix"], str)
                and isinstance(template_dict["ai_self"], str)
                and isinstance(template_dict["human_prefix"], str)
                and isinstance(template_dict["sample_input"], str)
                and isinstance(template_dict["sample_output"], str)
                and isinstance(template_dict["unlock_required"], bool)
            ), "Wrong value type(s)"
        except (
            TypeError,
            AttributeError,
            json.JSONDecodeError,
            KeyError,
            AssertionError,
        ) as e:
            # Handle cases where message.text is None
            # or the regular expression pattern does not match anything
            # or the resulting substring is not a valid JSON object
            # or the required keys are not present/are of the wrong type
            template_dict = None
            await message.reply(
                f"{strings.custom_template_parse_failed}\n\nError message: `{e}`"
            )

        if template_dict:
            if chatdata.gpt35_history is not None:
                chatdata.gpt35_chatbot = None
                chatdata.gpt35_history = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_preset_change.format("GPT-3.5"),
                )

            chatdata.set_gpt35_preset(template_dict)
            chatdata.set_model({"name": "gpt35", "args": {"preset": "custom"}})

            await message.reply_to_message.delete()
            await message.reply(
                strings.model_changed
                + strings.models.get("model-gpt35")
                + f" ({strings.gpt35_presets.get('custom').split(' ')[0]})"
            )


# Bing style selection callback
async def bing_style_selection_callback_handler(query):
    style = query.data.replace("bingstyle-", "")
    chatdata = util.load_chat(
        query.message.chat.id,
        create_new=True,
        is_group=await util.is_group(query.message.chat),
    )
    chatdata.set_model({"name": "bing", "args": {"style": style}})

    await query.message.edit(
        strings.model_changed + strings.models.get("model-bing") + f" ({style})"
    )


# Bard preset selection callback
async def bard_preset_selection_callback_handler(query):
    preset = query.data.replace("bardpreset-", "")
    chatdata = util.load_chat(
        query.message.chat.id,
        create_new=True,
        is_group=await util.is_group(query.message.chat),
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

            chatdata = util.load_chat(
                message.chat.id,
                create_new=True,
                is_group=await util.is_group(message.chat),
            )
            chatdata.set_api_key(api_key_input)
            await message.reply(strings.api_key_set)
        except openai.error.OpenAIError as e:
            await message.reply(
                f"{strings.api_key_invalid}\n\nError message: `{e}`\n\n{strings.api_key_common_errors}"
            )
    else:
        await message.reply(strings.api_key_invalid)


# Conversation
async def conversation_handler(client, message):
    chatdata = util.load_chat(message.chat.id)
    if not chatdata:
        await message.reply(f"{strings.no_auth}\n\n{strings.api_key_required}")
    else:
        raw_text = await util.get_raw_text(message)
        input_text = re.sub(r"^/\S*\s*", "", raw_text)
        sender_id = (
            message.from_user
            and message.from_user.id
            or message.sender_chat
            and message.sender_chat.id
        )

        if message.reply_to_message:
            context = await util.get_raw_text(message.reply_to_message)
            if context and chatdata.last_reply != context:
                input_text = f'Context: "{context}";\n{input_text}'

        placeholder = None
        if chatdata.model.get("name") == "bing":
            placeholder = await message.reply(
                random.choice(strings.placeholder_before_output)
                + strings.placeholer_bing,
                disable_notification=True,
            )

        try:
            model_output = await chatdata.process_message(
                client=client, model_input={"sender_id": sender_id, "text": input_text}
            )
            text = model_output.get("text")
            photo = model_output.get("photo")
            send_text_seperately = model_output.get("send_text_seperately")

            if placeholder is not None:
                await placeholder.delete()

            if not photo or send_text_seperately:
                await message.reply(text, quote=True)

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

            chatdata.last_reply = text
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


# Reset conversation history
async def reset_handler(message):
    chatdata = util.load_chat(message.chat.id)
    if chatdata:
        await chatdata.reset()
        await message.reply(strings.history_cleared)
    else:
        await message.reply(strings.chatdata_unavailable)


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
