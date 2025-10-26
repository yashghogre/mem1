import asyncio
from copy import deepcopy
from enum import StrEnum
from langfuse import observe
from typing import List

from config import CONFIG
from infra.database import DBStore
from infra.database.schema import Message
from infra.inference import Inference
from mem1 import Mem1

from .utils.prompts import SYSTEM_PROMPT


class AssistantException(Exception):
    ...

    
class SPECIAL_COMMANDS(StrEnum):
    EXIT = "/exit"
    RESET = "/reset"


class Assistant:
    def __init__(self):
        self.inference_instance = Inference()
        self.mem1_client = Mem1(
            chat_client=self.inference_instance.get_client(),
            model_name=CONFIG.MODEL_NAME,
        )

    @observe()
    async def handle_commands(self, query: str):
        try:
            match query:
                case SPECIAL_COMMANDS.EXIT.value:
                    #TODO: Figure out the flow and refactor this exit.
                    return  

                case SPECIAL_COMMANDS.RESET.value:
                    #NOTE: For now, we will simply clear all the messages from the DB
                    # instead of changing the thread and retaining the previous messages.
                    await DBStore.delete_messages()

        except Exception as e:
            raise AssistantException(f"Error while handling special commands: {str(e)}")


    @observe()
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


    @observe()
    def _put_system_message(self, msgs: List[Message]):
        system_msg = Message(
            role="system",
            content=SYSTEM_PROMPT,
        )
        msgs_copied = deepcopy(msgs)
        msgs_copied.insert(0, system_msg)
        return msgs_copied


    @observe()
    async def reply(self, query: str) -> str:
        try:
            if query.lower().strip() in [sp_cmd.value for sp_cmd in SPECIAL_COMMANDS]:
                return self.handle_commands(query)
            
            msgs_to_send = await self._get_context_with_current_msg(query)
            await self.mem1_client.process_memory(msgs_to_send)

            msgs_to_send_with_sys_msg = self._put_system_message(msgs_to_send)
            print(f"Context: {msgs_to_send}")

            response = await self.inference_instance.run(msgs_to_send_with_sys_msg)

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
