import json
from beanie import Document
from typing import Optional, Literal
from datetime import datetime

class Message(Document):
    role: Literal["system", "user", "assistant"]
    content: str
    created_at: str = json.dumps(datetime.utcnow().isoformat())

    #TODO: Allow it to take extra args and keep them in `core`
    # and return the messages with complete information.

    class Settings:
        name = "messages"
