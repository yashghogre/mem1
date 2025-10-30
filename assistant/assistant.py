import asyncio
from copy import deepcopy
from enum import StrEnum
from langfuse import observe
import logging
from typing import List

from config import CONFIG
from mem1 import Mem1

from .infra.database import DBStore
from .infra.database.schema import Message, ChatSummary
from .infra.embedder import Embedder
from .infra.inference import Inference
from .infra.vector_db import VectorSearch
from .utils.prompts import SYSTEM_PROMPT


logger = logging.getLogger(__name__)


class AssistantException(Exception):
    ...

    
class Assistant:
    def __init__(self):
        self.inference_instance = Inference()
        self.embedder = Embedder()
        self.mem1_client = Mem1(
            chat_client=self.inference_instance.get_client(),
            model_name=CONFIG.MODEL_NAME,
            vector_db_client=VectorSearch.get_client(),
            vector_db_collection=CONFIG.QDRANT_COLLECTION,
            embedder_client=self.embedder.get_client(),
            database_client=DBStore.get_client(),
            database_collection=ChatSummary,
        )


    # @observe()
    async def _get_context_with_current_msg(self, query: str) -> List[Message]:
        try:
            prev_msgs = await DBStore.get_messages()
            prev_msgs = [
                Message(
                    role=msg.role,
                    content=msg.content,
                ) for msg in prev_msgs
            ]

            user_msg = Message(
                role="user",
                content=query,
            )
            prev_msgs.append(user_msg)

            return prev_msgs

        except Exception as e:
            raise AssistantException(f"Failed to build context for reply. Error: {str(e)}")


    # @observe()
    def _put_system_message(self, msgs: List[Message]):
        system_msg = Message(
            role="system",
            content=SYSTEM_PROMPT,
        )
        msgs_copied = deepcopy(msgs)
        msgs_copied.insert(0, system_msg)
        return msgs_copied


    # @observe()
    async def reply(self, query: str) -> str:
        try:
            msgs_to_send = await self._get_context_with_current_msg(query)

            # Processing memory here.
            await self.mem1_client.process_memory(msgs_to_send)

            msgs_to_send_with_sys_msg = self._put_system_message(msgs_to_send)

            # Loading memory into the context here.
            msgs_with_memories = await self.mem1_client.load_memory(msgs_to_send_with_sys_msg)
            logger.info(f"Context: {msgs_with_memories}")

            response = await self.inference_instance.run(msgs_with_memories)

            await DBStore.store_message(
                role="user",
                content=query,
            )
            await DBStore.store_message(
                role="assistant",
                content=response,
            )

            return response

        except Exception as e:
            raise AssistantException(f"Failed to process reply. Error: {str(e)}")
