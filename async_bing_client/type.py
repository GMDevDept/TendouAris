from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Text(BaseModel):
    content: str
    type: str = "Text"

    def __add__(self, other):
        if isinstance(other, Text):
            return Text(content=self.content + other.content)
        else:
            return NotImplemented

    def __str__(self):
        return str(self.content)


class SuggestRely(BaseModel):
    content: str
    type: str = "SuggestRely"

    def __str__(self):
        return str(self.content)


class Notice(BaseModel):
    content: str
    type: str = "Notice"

    def __str__(self):
        return str(self.content)


class Image(BaseModel):
    name: str = "image.png"
    url: str
    base64: Optional[str] = None
    type: str = "Image"

    def __str__(self):
        return f"![{self.name}]({self.url})"


class Apology(BaseModel):
    content: str
    type: str = "Apology"

    def __str__(self):
        return str(self.content)


class Response(BaseModel):
    content: dict
    type: str = "Response"


class SourceAttribution(BaseModel):
    display_name: str = 'Source'
    see_more_url: str
    image: Optional[Image] = None
    type: str = "SourceAttribution"

    def __str__(self):
        _str_ = f"[{self.display_name}]({self.see_more_url})"
        if self.image and self.image.url:
            _str_ += f"\n![{self.display_name}]({self.image.url})"
        return _str_


class SearchResult(BaseModel):
    content: list | str
    type: str = "SearchResult"

    def __str__(self):
        string = "Search Result:\n"
        if isinstance(self.content, list):
            for outer_index, each in enumerate(self.content):
                string += f"\n({outer_index + 1}){each.get('title')}:\n"
                for index, snippet in enumerate(each['snippets']):
                    string += f"[{index + 1}]:{snippet}\n"
            return string + "\n"
        else:
            return string + "\n" + self.content


class Limit(BaseModel):
    max_num_user_messages: int
    num_user_messages: int
    max_num_long_doc_summary_user_messages: int
    num_long_doc_summary_user_messages: int
    type: str = 'Limit'

    def __str__(self):
        return str(f"\n{self.num_user_messages} of {self.max_num_user_messages}")


class NewChat(BaseModel):
    chat: dict
    type: str = 'NewChat'
