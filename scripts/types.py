from typing import Optional
from pydantic import BaseModel


class Photo(BaseModel):
    url: str


class ModelOutput(BaseModel):
    text: str
    photos: Optional[list[Photo]]
