from typing import Optional

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
