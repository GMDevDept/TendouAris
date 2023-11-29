import re
import json
import openai
import random
import logging
import traceback
from typing import Union
from scripts import gvars, strings, util
from scripts.chatdata import ChatData, GroupChatData
from scripts.types import ModelOutput
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    CallbackQuery,
    ForceReply,
    Message,
)
from pyrogram.errors import RPCError
from pyrogram.raw.functions.messages import UploadMedia
from pyrogram.raw.types import InputMediaPhotoExternal
from async_bing_client.type import Apology


# Global access filter
async def global_access_filter_handler(client, update: Union[Message, CallbackQuery]):
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
async def help_handler(client, message):
    try:
        sender = message.from_user
        name = f"{sender.first_name and sender.first_name or ''} {sender.last_name and sender.last_name or ''}".strip()
    except AttributeError:
        name = ""
    await message.reply(strings.manual.format(name))


# Version info and update log
async def version_handler(client, message):
    await message.reply(strings.version)


# Get current chat id
async def chatid_handler(client, message):
    await message.reply(f"Chat ID: `{message.chat.id}`")


# Model selection
async def model_selection_handler(client, message):
    chatdata = util.load_chat(message.chat.id)
    if (
        chatdata
        and chatdata.is_group
        and chatdata.model_select_admin_only
        and not await util.is_group_update_from_admin(client, message)
    ):
        await message.reply(
            f"{strings.no_auth}\n\n({strings.group_command_admin_only})"
        )
    else:
        await message.reply(
            strings.choose_model,
            quote=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            strings.models.get("model-gpt35"),
                            callback_data="model-gpt35",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            strings.models.get("model-gpt4"), callback_data="model-gpt4"
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
                    [
                        InlineKeyboardButton(
                            strings.models.get("model-claude"),
                            callback_data="model-claude",
                        )
                    ],
                ]
            ),
        )


# Model selection callback
async def model_selection_callback_handler(client, query):
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
                                    strings.gpt35_presets.get("custom"),
                                    callback_data="gpt35preset-custom",
                                )
                            ],
                        ]
                        + [
                            [
                                InlineKeyboardButton(
                                    preset.get("display_name"),
                                    callback_data="gpt35preset-addon-" + id,
                                )
                            ]
                            for id, preset in gvars.gpt35_addons.items()
                        ]
                        + [
                            [
                                InlineKeyboardButton(
                                    strings.gpt35_presets.get("default"),
                                    callback_data="gpt35preset-default",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    strings.github_contributing,
                                    url="https://github.com/ToffeeNeko/TendouAris#contributing",
                                )
                            ],
                        ]
                    ),
                )
            else:
                await query.message.edit(
                    f"{strings.no_auth}\n\n{strings.api_key_required}"
                )
        elif modelname == "gpt4":
            chatdata = util.load_chat(query.message.chat.id)
            if chatdata and (
                chatdata.openai_api_key or chatdata.chat_id in gvars.manager
            ):
                try:
                    await openai.ChatCompletion.acreate(
                        api_key=chatdata.openai_api_key
                        or chatdata.chat_id in gvars.manager
                        and gvars.openai_api_key
                        or "ERROR",  # must be true
                        model="gpt-4",
                        messages=[
                            {
                                "role": "user",
                                "content": "Test message, please reply '1'",
                            }
                        ],
                    )

                    await query.message.edit(
                        strings.model_choose_preset,
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        strings.gpt4_presets.get("default"),
                                        callback_data="gpt4preset-default",
                                    )
                                ],
                                [
                                    InlineKeyboardButton(
                                        strings.gpt4_presets.get("custom"),
                                        callback_data="gpt4preset-custom",
                                    )
                                ],
                            ]
                            + [
                                [
                                    InlineKeyboardButton(
                                        preset.get("display_name"),
                                        callback_data="gpt4preset-addon-" + id,
                                    )
                                ]
                                for id, preset in gvars.gpt4_addons.items()
                            ]
                            + [
                                [
                                    InlineKeyboardButton(
                                        strings.github_contributing,
                                        url="https://github.com/ToffeeNeko/TendouAris#contributing",
                                    )
                                ],
                            ]
                        ),
                    )
                except openai.error.InvalidRequestError as e:
                    await query.message.reply(
                        f"{strings.api_key_not_support_gpt4}\n\nError message: `{e}`"
                    )
                except openai.error.OpenAIError as e:
                    await query.message.reply(
                        f"{strings.api_key_invalid}\n\nError message: `{e}`\n\n{strings.api_key_common_errors}"
                    )
            else:
                await query.message.edit(
                    f"{strings.no_auth}\n\n{strings.api_key_required}"
                )
        elif modelname == "bing":
            if hasattr(gvars, "bing_client"):
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
            else:
                await query.message.edit(strings.bing_cookie_unavailable)
        elif modelname == "bard":
            if not gvars.bard_1psid or not gvars.bard_1psidts:
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
                            ]
                        ]
                    ),
                )
        elif modelname == "claude":
            if hasattr(gvars, "claude_client"):
                await query.message.edit(
                    strings.model_choose_preset,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    strings.claude_presets.get("aris"),
                                    callback_data="claudepreset-aris",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    strings.claude_presets.get("default"),
                                    callback_data="claudepreset-default",
                                )
                            ],
                        ],
                    ),
                )
            else:
                await query.message.edit(strings.claude_cookie_unavailable)


# GPT-3.5 preset selection callback
async def gpt35_preset_selection_callback_handler(client, query):
    preset = query.data.replace("gpt35preset-", "")
    chatdata = util.load_chat(query.message.chat.id)

    match preset:
        case "default" | "aris":
            if chatdata.gpt35_history is not None and not (
                chatdata.model["name"] == "gpt35"
                and chatdata.model["args"].get("preset") == preset
            ):
                chatdata.gpt35_chatbot = None
                chatdata.gpt35_history = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_preset_change.format("GPT3.5"),
                )

            chatdata.set_model({"name": "gpt35", "args": {"preset": preset}})

            await query.message.edit(
                strings.model_changed
                + strings.models.get("model-gpt35")
                + f" ({strings.gpt35_presets.get(preset).split(' (')[0]})"
            )
        case "custom":
            await query.message.edit(
                strings.manage_custom_preset,
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
                strings.gpt35_preset_placeholder + strings.custom_preset_template,
                reply_markup=ForceReply(selective=True),
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
                        strings.model_reset_due_to_preset_change.format("GPT3.5"),
                    )

                chatdata.set_model({"name": "gpt35", "args": {"preset": "custom"}})

                await query.message.edit(
                    strings.model_changed
                    + strings.models.get("model-gpt35")
                    + f" ({strings.gpt35_presets.get('custom').split(' (')[0]})\n\n`{json.dumps(chatdata.gpt35_preset, indent=4, ensure_ascii=False)}`"
                )
        case _:
            assert preset.startswith("addon-"), f"Invalid callback: {query.data}"
            if chatdata.gpt35_history is not None and not (
                chatdata.model["name"] == "gpt35"
                and chatdata.model["args"].get("preset") == preset
            ):
                chatdata.gpt35_chatbot = None
                chatdata.gpt35_history = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_preset_change.format("GPT3.5"),
                )

            preset_id = preset.replace("addon-", "")
            chatdata.set_model(
                {
                    "name": "gpt35",
                    "args": {"preset": "addon", "id": preset_id},
                }
            )

            await query.message.edit(
                strings.model_changed
                + strings.models.get("model-gpt35")
                + f" ({gvars.gpt35_addons.get(preset_id).get('display_name')})\n\n{gvars.gpt35_addons.get(preset_id).get('description')}"
            )


# GPT-4 preset selection callback
async def gpt4_preset_selection_callback_handler(client, query):
    preset = query.data.replace("gpt4preset-", "")
    chatdata = util.load_chat(query.message.chat.id)

    match preset:
        case "default":
            if chatdata.gpt4_history is not None and not (
                chatdata.model["name"] == "gpt4"
                and chatdata.model["args"].get("preset") == preset
            ):
                chatdata.gpt4_chatbot = None
                chatdata.gpt4_history = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_preset_change.format("GPT4"),
                )

            chatdata.set_model({"name": "gpt4", "args": {"preset": preset}})

            await query.message.edit(
                strings.model_changed
                + strings.models.get("model-gpt4")
                + f" ({strings.gpt4_presets.get(preset).split(' (')[0]})"
            )
        case "custom":
            await query.message.edit(
                strings.manage_custom_preset,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                strings.custom_preset_options.get("new"),
                                callback_data="gpt4preset-custom-new",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                strings.custom_preset_options.get("continue"),
                                callback_data="gpt4preset-custom-continue",
                            )
                        ],
                    ]
                ),
            )
        case "custom-new":
            await query.message.edit(
                strings.gpt4_preset_placeholder + strings.custom_preset_template,
                reply_markup=ForceReply(selective=True),
            )
        case "custom-continue":
            if not chatdata.gpt4_preset:
                await query.message.edit(strings.custom_preset_unavailable)
            else:
                if chatdata.gpt4_history is not None and not (
                    chatdata.model["name"] == "gpt4"
                    and chatdata.model["args"].get("preset") == "custom"
                ):
                    chatdata.gpt4_chatbot = None
                    chatdata.gpt4_history = None
                    await client.send_message(
                        chatdata.chat_id,
                        strings.model_reset_due_to_preset_change.format("GPT4"),
                    )

                chatdata.set_model({"name": "gpt4", "args": {"preset": "custom"}})

                await query.message.edit(
                    strings.model_changed
                    + strings.models.get("model-gpt4")
                    + f" ({strings.gpt4_presets.get('custom').split(' (')[0]})\n\n`{json.dumps(chatdata.gpt4_preset, indent=4, ensure_ascii=False)}`"
                )
        case _:
            assert preset.startswith("addon-"), f"Invalid callback: {query.data}"
            if chatdata.gpt4_history is not None and not (
                chatdata.model["name"] == "gpt4"
                and chatdata.model["args"].get("preset") == preset
            ):
                chatdata.gpt4_chatbot = None
                chatdata.gpt4_history = None
                await client.send_message(
                    chatdata.chat_id,
                    strings.model_reset_due_to_preset_change.format("GPT4"),
                )

            preset_id = preset.replace("addon-", "")
            chatdata.set_model(
                {
                    "name": "gpt4",
                    "args": {"preset": "addon", "id": preset_id},
                }
            )

            await query.message.edit(
                strings.model_changed
                + strings.models.get("model-gpt4")
                + f" ({gvars.gpt4_addons.get(preset_id).get('display_name')})\n\n{gvars.gpt4_addons.get(preset_id).get('description')}"
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
            assert len(template_dict) == 8, "Invalid template length"
            assert (
                isinstance(template_dict["prompt"], str)
                and isinstance(template_dict["ai_prefix"], str)
                and isinstance(template_dict["ai_self"], str)
                and isinstance(template_dict["human_prefix"], str)
                and isinstance(template_dict["sample_input"], str)
                and isinstance(template_dict["sample_output"], str)
                and isinstance(template_dict["unlock_required"], bool)
                and isinstance(template_dict["keyword_filter"], bool)
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
            # Already validated in filters.custom_preset_filter
            model_name = re.match(
                r"^\s*\[(\S*)\sModel Custom Preset\]", message.reply_to_message.text
            ).group(1)

            if model_name == "GPT3.5":
                if chatdata.gpt35_history is not None:
                    chatdata.gpt35_chatbot = None
                    chatdata.gpt35_history = None
                    await client.send_message(
                        chatdata.chat_id,
                        strings.model_reset_due_to_preset_change.format("GPT3.5"),
                    )

                chatdata.set_gpt35_preset(template_dict)
                chatdata.set_model({"name": "gpt35", "args": {"preset": "custom"}})

                await message.reply_to_message.delete()
                await message.reply(
                    strings.model_changed
                    + strings.models.get("model-gpt35")
                    + f" ({strings.gpt35_presets.get('custom').split(' (')[0]})"
                )
            elif model_name == "GPT4":
                if chatdata.gpt4_history is not None:
                    chatdata.gpt4_chatbot = None
                    chatdata.gpt4_history = None
                    await client.send_message(
                        chatdata.chat_id,
                        strings.model_reset_due_to_preset_change.format("GPT4"),
                    )

                chatdata.set_gpt4_preset(template_dict)
                chatdata.set_model({"name": "gpt4", "args": {"preset": "custom"}})

                await message.reply_to_message.delete()
                await message.reply(
                    strings.model_changed
                    + strings.models.get("model-gpt4")
                    + f" ({strings.gpt4_presets.get('custom').split(' (')[0]})"
                )
            else:
                raise ValueError(f"Invalid model name: {model_name}")


# Bing style selection callback
async def bing_style_selection_callback_handler(client, query):
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
async def bard_preset_selection_callback_handler(client, query):
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
        + f" ({strings.bard_presets.get(preset).split(' (')[0]})"
    )


# Claude preset selection callback
async def claude_preset_selection_callback_handler(client, query):
    preset = query.data.replace("claudepreset-", "")
    chatdata = util.load_chat(
        query.message.chat.id,
        create_new=True,
        is_group=await util.is_group(query.message.chat),
    )
    chatdata.set_model({"name": "claude", "args": {"preset": preset}})

    await query.message.edit(
        strings.model_changed
        + strings.models.get("model-claude")
        + f" ({strings.claude_presets.get(preset).split(' (')[0]})"
    )


# Set OpenAI API key
async def api_key_handler(client, message):
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
            await chatdata.set_api_key(api_key_input)
            await message.reply(strings.api_key_set)
        except openai.error.OpenAIError as e:
            await message.reply(
                f"{strings.api_key_invalid}\n\nError message: `{e}`\n\n{strings.api_key_common_errors}"
            )
    else:
        await message.reply(strings.api_key_invalid)


# Reset conversation history
async def reset_handler(client, message):
    chatdata = util.load_chat(message.chat.id)
    if not chatdata:
        await message.reply(strings.chatdata_unavailable)
    else:
        await chatdata.reset()
        await message.reply(strings.history_cleared)


# Chat settings
async def chat_setting_handler(client, message):
    chatdata = util.load_chat(message.chat.id)
    if not chatdata:
        await message.reply(strings.chatdata_unavailable)
    else:
        await message.reply(
            strings.chat_setting_menu,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            strings.chat_setting_options.get("model_access"),
                            callback_data="chat_setting-model_access",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            strings.chat_setting_options.get("flood_control"),
                            callback_data="chat_setting-flood_control",
                        )
                    ],
                ]
            ),
        )


# Chat settings callback
async def chat_setting_callback_handler(client, query):
    option = query.data.replace("chat_setting-", "")
    chatdata = util.load_chat(query.message.chat.id)
    if not chatdata:
        await query.message.reply(strings.chatdata_unavailable)
    else:
        match option:
            case "model_access":
                await query.message.edit(
                    strings.chat_setting_options.get("model_access"),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    strings.model_access_options.get("all"),
                                    callback_data="chat_setting-model_access-all",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    strings.model_access_options.get("admin"),
                                    callback_data="chat_setting-model_access-admin",
                                )
                            ],
                        ]
                    ),
                )
            case "model_access-all":
                chatdata.set_model_select_admin_only(False)
                await query.message.edit(
                    f"{strings.chat_setting_options.get('model_access')}: {strings.model_access_options.get('all')}"
                )
            case "model_access-admin":
                chatdata.set_model_select_admin_only(True)
                await query.message.edit(
                    f"{strings.chat_setting_options.get('model_access')}: {strings.model_access_options.get('admin')}"
                )
            case "flood_control":
                await query.message.edit(
                    strings.chat_setting_options.get("flood_control"),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    strings.flood_control_options.get("on").format(
                                        gvars.flood_control_count,
                                        gvars.flood_control_interval,
                                    ),
                                    callback_data="chat_setting-flood_control-on",
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    strings.flood_control_options.get("off"),
                                    callback_data="chat_setting-flood_control-off",
                                )
                            ],
                        ]
                    ),
                )
            case "flood_control-on":
                chatdata.set_flood_control(True)
                await query.message.edit(
                    f"{strings.chat_setting_options.get('flood_control')}: {strings.flood_control_options.get('on').format(gvars.flood_control_count, gvars.flood_control_interval)}"
                )
            case "flood_control-off":
                chatdata.set_flood_control(False)
                await query.message.edit(
                    f"{strings.chat_setting_options.get('flood_control')}: {strings.flood_control_options.get('off')}"
                )


# Manage mode
async def manage_mode_handler(client, message):
    await message.reply(
        f"{strings.manage_mode_menu}\n\nActive chat count: {ChatData.total}\nActive group chat count: {GroupChatData.total}\nDatabase entry count: {gvars.db_chatdata.dbsize()}",
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
                        strings.manage_mode_options.get("scope-gpt4"),
                        callback_data="manage-scope-gpt4",
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
                [
                    InlineKeyboardButton(
                        strings.manage_mode_options.get("scope-claude"),
                        callback_data="manage-scope-claude",
                    )
                ],
            ]
        ),
    )


# Manage mode callback
async def manage_mode_callback_handler(client, query):
    if re.match(r"^manage-scope-(global|gpt35|gpt4|bing|bard|claude)$", query.data):
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
        r"^manage-scope-(global|gpt35|gpt4|bing|bard|claude)-(all|whitelist|manager)$",
        query.data,
    ):
        match = re.match(
            r"^manage-scope-(global|gpt35|gpt4|bing|bard|claude)-(all|whitelist|manager)$",
            query.data,
        )
        model = match.group(1)
        scope = match.group(2)
        setattr(gvars, "scope_" + model, scope)
        await query.message.edit(
            f"Scope of access to `{model}` has been set to `{scope}`"
        )


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
        if (
            chatdata.model.get("name") == "bing"
            or chatdata.model.get("name") == "gpt4"
            or (
                chatdata.model.get("name") == "claude"
                and chatdata.model.get("args").get("preset") != "default"
            )
        ):
            placeholder = await message.reply(
                random.choice(strings.placeholder_before_output)
                + (
                    chatdata.model.get("name") == "bing"
                    and strings.placeholder_bing
                    or chatdata.model.get("name") == "gpt4"
                    and strings.placeholder_gpt4
                    or chatdata.model.get("name") == "claude"
                    and strings.placeholder_claude
                ),
                disable_notification=True,
            )

        try:
            model_output: ModelOutput = await chatdata.process_message(
                client=client, model_input={"sender_id": sender_id, "text": input_text}
            )
            text: str = model_output.text
            photos: list[str] | None = model_output.photos and [photo.url for photo in model_output.photos]

            if placeholder is not None:
                await placeholder.delete()

            valid_media = []
            if photos:
                fallback_text = "\n\n"
                for url in photos:
                    try:
                        await client.invoke(
                            UploadMedia(
                                peer=await client.resolve_peer(chatdata.chat_id),
                                media=InputMediaPhotoExternal(url=url),
                            )
                        )
                        valid_media.append(url)
                    except RPCError:
                        fallback_text += f"[Invalid Media]({url})\n"
                    except Exception as e:
                        logging.error(f"Error occurred during processing media: {e}")
                        fallback_text += f"[Invalid Media]({url})\n"

                text += fallback_text.rstrip()

            if valid_media:
                if len(valid_media) == 1:
                    await message.reply_photo(
                        valid_media[0], quote=True, caption=len(text) < 1024 and text
                    )
                else:
                    media_group = [
                        InputMediaPhoto(
                            url,
                            caption=i == len(valid_media) - 1
                            and len(text) < 1024
                            and text,
                        )
                        for i, url in enumerate(valid_media)
                    ]

                    # media group length limit: 2-10
                    for i in range(0, len(media_group), 10):
                        batch = media_group[i : i + 10]
                        if len(batch) == 1:
                            batch.insert(0, media_group[i - 1])
                        await message.reply_media_group(batch, quote=True)

            # Max caption length limit = 1024
            if not valid_media or len(text) >= 1024:
                # Max text message length limit = 4096
                for i in range(0, len(text), 4096):
                    text_chunk = text[i : i + 4096]
                    await message.reply(text_chunk, quote=True)

            chatdata.last_reply = text
        except RPCError as e:
            logging.error(f"{e}: " + "".join(traceback.format_tb(e.__traceback__)))
            await message.reply(f"{strings.rpc_error}\n\nError message:\n`{str(e)[:100]}`")
        except Exception as e:
            logging.error(f"{e}: " + "".join(traceback.format_tb(e.__traceback__)))
            await message.reply(
                f"{strings.internal_error}\n\nError message:\n`{str(e)[:100]}`\n\n{strings.feedback}",
                quote=False,
            )


# Generate image
async def draw_handler(client, message):
    prompt_input = re.sub(r"^/\S*\s*", "", message.text)
    if not prompt_input:
        await message.reply(strings.draw_prompt_invalid)
    elif not hasattr(gvars, "bing_client"):
        await message.reply(strings.bing_cookie_unavailable)
    elif not util.access_scope_filter(gvars.scope_bing, message.chat.id):
        await message.reply(
            f"{strings.no_auth}\n\nError message: `{strings.globally_disabled}`"
        )
    else:
        placeholder = await message.reply(
            random.choice(strings.placeholder_before_output),
            disable_notification=True,
        )
        try:
            response = await gvars.bing_client.draw(
                prompt_input
            )  # draw -> List[Image] | Apology
            if isinstance(response, Apology):
                await message.reply(
                    f"{strings.api_error}\n\nError Message:\n`{response.content}`",
                    quote=True,
                )
                return
            elif isinstance(response, list):
                text = strings.draw_success
                photos = [photo.url for photo in response]
            else:  # should not happen
                await message.reply(
                    f"{strings.internal_error}\n\n{strings.feedback}",
                    quote=False,
                )
                return

            valid_media = []
            if photos:
                fallback_text = "\n\n"
                for url in photos:
                    try:
                        await client.invoke(
                            UploadMedia(
                                peer=await client.resolve_peer(message.chat.id),
                                media=InputMediaPhotoExternal(url=url),
                            )
                        )
                        valid_media.append(url)
                    except RPCError:
                        fallback_text += f"[Invalid Media]({url})\n"
                    except Exception as e:
                        logging.error(f"Error occurred during processing media: {e}")
                        fallback_text += f"[Invalid Media]({url})\n"

                text += fallback_text.rstrip()

            if valid_media:
                if len(valid_media) == 1:
                    await message.reply_photo(
                        valid_media[0], quote=True, caption=len(text) < 1024 and text
                    )
                else:
                    media_group = [
                        InputMediaPhoto(
                            url,
                            caption=i == len(valid_media) - 1
                            and len(text) < 1024
                            and text,
                        )
                        for i, url in enumerate(valid_media)
                    ]

                    # media group length limit: 2-10
                    for i in range(0, len(media_group), 10):
                        batch = media_group[i : i + 10]
                        if len(batch) == 1:
                            batch.insert(0, media_group[i - 1])
                        await message.reply_media_group(batch, quote=True)

            # Max caption length limit = 1024
            if not valid_media or len(text) >= 1024:
                # Max text message length limit = 4096
                for i in range(0, len(text), 4096):
                    text_chunk = text[i : i + 4096]
                    await message.reply(text_chunk, quote=True)
        except RPCError as e:
            logging.error(f"{e}: " + "".join(traceback.format_tb(e.__traceback__)))
            await message.reply(f"{strings.rpc_error}\n\nError message:\n`{str(e)[:100]}`")
        except Exception as e:
            logging.error(f"{e}: " + "".join(traceback.format_tb(e.__traceback__)))
            await message.reply(
                f"{strings.internal_error}\n\nError message:\n`{str(e)[:100]}`\n\n{strings.feedback}",
                quote=False,
            )
        finally:
            await placeholder.delete()
