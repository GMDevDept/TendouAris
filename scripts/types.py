from typing import Optional
from collections import deque

from google.ai.generativelanguage import Content
from pyrogram.types import Message, InlineKeyboardMarkup
from pydantic import BaseModel


class Image(BaseModel):
    url: str


class ModelInput(BaseModel):
    text: str
    sender_id: int
    message: Message


class ModelOutput(BaseModel):
    text: str
    images: Optional[list[Image]] = None
    markup: Optional[InlineKeyboardMarkup] = None


class GeminiHistory(BaseModel):
    thread: list[Content]
    index: list[int]  # Message id


class GeminiHistoryTrace(deque[GeminiHistory]):
    def traceback(self, msgid: int) -> list[Content]:
        return
