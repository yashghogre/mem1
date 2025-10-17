import json
from beanie import Document
from typing import Optional, Literal
from datetime import datetime

class Message(Document):
    role: Literal["system", "user", "assistant"]
    content: str
    created_at: datetime = json.dumps(datetime.utcnow().isoformat())

    class Settings:
        name = "messages"
