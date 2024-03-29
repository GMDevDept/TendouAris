import json
import asyncio
from asyncio import Task
from typing import Optional

from Bard import AsyncChatbot as BardChatbot
from async_bing_client import Bing_Client
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from google.generativeai import ChatSession

from scripts import gvars, strings
from scripts.types import ModelInput, ModelOutput
from srv.gemini import process_message_gemini
from srv.gpt import process_message_gpt35, process_message_gpt4
from srv.bing import process_message_bing
from srv.bard import process_message_bard
from srv.claude import process_message_claude


class ChatData:
    total = 0

    def __init__(
        self,
        chat_id: int,
        model: dict = {"name": "gemini", "args": {"preset": "aris"}},
        **kwargs,
    ):
        self.chat_id: int = chat_id
        self.is_group: Optional[bool] = None
        self.model: dict = model  # {"name": str, "args": dict}
        self.version: str = kwargs.get("version") or strings.version
        self.openai_api_key: Optional[str] = kwargs.get("openai_api_key")
        self.gemini_preset: Optional[dict] = kwargs.get("gemini_preset")
        self.gemini_session: Optional[ChatSession] = None
        self.gemini_clear_task: Optional[Task] = None
        self.gpt35_preset: Optional[dict] = kwargs.get("gpt35_preset")
        self.gpt35_chatbot: Optional[ConversationChain] = None
        self.gpt35_history: Optional[ConversationSummaryBufferMemory] = None
        self.gpt35_clear_task: Optional[Task] = None
        self.gpt4_preset: Optional[dict] = kwargs.get("gpt4_preset")
        self.gpt4_chatbot: Optional[ConversationChain] = None
        self.gpt4_history: Optional[ConversationSummaryBufferMemory] = None
        self.gpt4_clear_task: Optional[Task] = None
        self.bing_chatbot: Optional[Bing_Client] = None
        self.bing_clear_task: Optional[Task] = None
        self.bard_chatbot: Optional[BardChatbot] = None
        self.bard_clear_task: Optional[Task] = None
        self.claude_uuid: Optional[str] = None
        self.claude_clear_task: Optional[Task] = None
        self.last_reply: Optional[str] = None
        self.concurrent_lock: set = set()  # {model}

    @property
    def persistent_data(self) -> dict:
        return {
            "chat_id": self.chat_id,
            "is_group": self.is_group,
            "version": self.version,
            "model": self.model,
            "openai_api_key": self.openai_api_key,
            "gemini_preset": self.gemini_preset,
            "gpt35_preset": self.gpt35_preset,
            "gpt4_preset": self.gpt4_preset,
        }

    def save(self):
        assert self.chat_id
        if self.chat_id not in gvars.all_chats:
            ChatData.total += 1
        gvars.all_chats.update({self.chat_id: self})
        data_json = json.dumps(self.persistent_data)
        gvars.db_chatdata.set(self.chat_id, data_json)

    @classmethod
    def load(cls, data_json: str) -> "ChatData":
        data = json.loads(data_json)
        if data.get("is_group"):
            chatdata = GroupChatData(**data)
        else:
            chatdata = ChatData(**data)

        if chatdata.chat_id not in gvars.all_chats:
            ChatData.total += 1
            if data.get("is_group"):
                GroupChatData.total += 1

        gvars.all_chats.update({data["chat_id"]: chatdata})

        return chatdata

    def set_model(self, model: dict):
        self.model = model
        self.save()
        self.reset()

    async def set_api_key(self, api_key: str):
        self.openai_api_key = api_key
        self.save()

        self.gpt35_chatbot = None
        self.gpt35_history = None
        self.gpt4_chatbot = None
        self.gpt4_history = None

        if self.gpt35_clear_task:
            self.gpt35_clear_task.cancel()
            self.gpt35_clear_task = None

        if self.gpt4_clear_task:
            self.gpt4_clear_task.cancel()
            self.gpt4_clear_task = None

    def set_gemini_preset(self, preset: dict):
        self.gemini_preset = preset
        self.save()

    def set_gpt35_preset(self, preset: dict):
        self.gpt35_preset = preset
        self.save()

    def set_gpt4_preset(self, preset: dict):
        self.gpt4_preset = preset
        self.save()

    async def process_message(self, model_input: ModelInput) -> ModelOutput:
        model_name, model_args = self.model["name"], self.model["args"]
        match model_name:
            case "gemini":
                model_output = await process_message_gemini(
                    chatdata=self,
                    model_args=model_args,
                    model_input=model_input,
                )
            case "gpt35":
                model_output = await process_message_gpt35(
                    chatdata=self,
                    model_args=model_args,
                    model_input=model_input,
                )
            case "gpt4":
                model_output = await process_message_gpt4(
                    chatdata=self,
                    model_args=model_args,
                    model_input=model_input,
                )
            case "bing":
                model_output = await process_message_bing(
                    chatdata=self,
                    model_args=model_args,
                    model_input=model_input,
                )
            case "bard":
                model_output = await process_message_bard(
                    chatdata=self,
                    model_args=model_args,
                    model_input=model_input,
                )
            case "claude":
                model_output = await process_message_claude(
                    chatdata=self,
                    model_args=model_args,
                    model_input=model_input,
                )
        return model_output

    def reset(self):
        self.gemini_session = None
        self.gpt35_chatbot = None
        self.gpt35_history = None
        self.gpt4_chatbot = None
        self.gpt4_history = None
        self.bing_chatbot = None
        self.bard_chatbot = None
        self.claude_uuid = None
        self.last_reply = None
        self.concurrent_lock.clear()

        if self.gemini_clear_task:
            self.gemini_clear_task.cancel()
            self.gemini_clear_task = None

        if self.gpt35_clear_task:
            self.gpt35_clear_task.cancel()
            self.gpt35_clear_task = None

        if self.gpt4_clear_task:
            self.gpt4_clear_task.cancel()
            self.gpt4_clear_task = None

        if self.bing_clear_task:
            self.bing_clear_task.cancel()
            self.bing_clear_task = None

        if self.bard_clear_task:
            self.bard_clear_task.cancel()
            self.bard_clear_task = None

        if self.claude_clear_task:
            self.claude_clear_task.cancel()
            self.claude_clear_task = None


class GroupChatData(ChatData):
    total = 0

    def __init__(self, chat_id: int, **kwargs):
        super().__init__(chat_id, **kwargs)
        self.is_group = True
        self.flood_control_enabled: bool = kwargs.get("flood_control_enabled") is True  # default to be False
        self.flood_control_record: Optional[dict] = None
        self.model_select_admin_only: bool = (
            kwargs.get("model_select_admin_only") is not False  # default to be True
        )

    @property
    def persistent_data(self):
        data = super().persistent_data
        data.update(
            {
                "flood_control_enabled": self.flood_control_enabled,
                "model_select_admin_only": self.model_select_admin_only,
            }
        )
        return data

    def save(self):
        if self.chat_id not in gvars.all_chats:
            GroupChatData.total += 1
        return super().save()

    def set_flood_control(self, enable: bool):
        self.flood_control_enabled = enable
        self.save()

    def set_model_select_admin_only(self, enable: bool):
        self.model_select_admin_only = enable
        self.save()

    async def process_message(self, model_input: ModelInput) -> ModelOutput:
        if not self.flood_control_enabled:
            return await super().process_message(model_input)
        else:
            if not self.flood_control_record:
                self.flood_control_record = {}

            sender_id = model_input.sender_id
            if (
                sender_id in self.flood_control_record
                and self.flood_control_record[sender_id]["count"]
                >= gvars.flood_control_count
            ):
                return ModelOutput(
                    text=strings.flood_control_activated.format(
                        gvars.flood_control_count, gvars.flood_control_interval
                    )
                )

            model_output = await super().process_message(model_input)

            async def clear_flood_control_counter():
                await asyncio.sleep(gvars.flood_control_interval)
                if self.flood_control_record and sender_id in self.flood_control_record:
                    self.flood_control_record[sender_id]["count"] = 0
                    self.flood_control_record[sender_id]["clear_task"] = None

            if sender_id not in self.flood_control_record:
                self.flood_control_record[sender_id] = {
                    "count": 0,
                    "clear_task": None,
                }

            self.flood_control_record[sender_id]["count"] += 1
            if self.flood_control_record[sender_id]["clear_task"] is not None:
                self.flood_control_record[sender_id]["clear_task"].cancel()
            self.flood_control_record[sender_id]["clear_task"] = asyncio.create_task(
                clear_flood_control_counter()
            )

            return model_output
