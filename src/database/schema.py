from beanie import Document
from typing import Optional, Literal

class Message(Document):
    role: Literal["system", "user", "assistant"]
    content: str
