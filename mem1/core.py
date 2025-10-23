import asyncio
from textwrap import dedent
from typing import List, Optional

from assistant.database.schema import Message
from infra.graph_db import GraphDB
from infra.inference import Inference
from infra.vector_db import VectorSearch


class Mem1Exception(Exception):
    def __init__(
        self,
        error: str,
        message: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        self.error = error
        self.message = message  # This isn't making sense for now XD
        self.suggestion = suggestion

    def __repr__(self):
        return dedent(f"""
        Error in Mem1 Client.
        Error: {self.error}.
        Suggestion: {self.suggestion or " "}
        """)


class Mem1:
    def __init__(
        self,
        *
        max_memories_in_vector_db: Optional[int] = 10,
        message_interval_for_summary: Optional[int] = 5,
    ):
        self.max_memories_in_vector_db = max_memories_in_vector_db
        self.message_interval_for_summary = message_interval_for_summary


    async def add(self, messages: List[Message]):
        try:
            
            
        except Exception as e:
            raise Mem1Exception(error=str(e))
