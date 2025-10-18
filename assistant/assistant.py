import asyncio
from enum import StrEnum
from langfuse import observe
from typing import List

from assistant.database import DBStore
from assistant.database.schema import Message
from assistant.utils.prompts import SYSTEM_PROMPT
from infra.inference import Inference


class AssistantException(Exception):
    ...

    
class SPECIAL_COMMANDS(StrEnum):
    EXIT = "/exit"
    RESET = "/reset"


class Assistant:
    def __init__(self):
        self.inference_instance = Inference()

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
    async def get_context_with_current_msg(self, query: str) -> List[Message]:
        try:
            prev_msgs = await DBStore.get_messages()
            prev_msgs = [
                Message(
                    role=msg.role,
                    content=msg.content,
                ) for msg in prev_msgs
            ]

            system_msg = Message(
                role="system",
                content=SYSTEM_PROMPT,
            )
            user_msg = Message(
                role="user",
                content=query,
            )
            prev_msgs.insert(0, system_msg)
            prev_msgs.append(user_msg)

            return prev_msgs

        except Exception as e:
            raise AssistantException(f"Failed to build context for reply. Error: {str(e)}")


    @observe()
    async def reply(self, query: str) -> str:
        try:
            if query.lower().strip() in [sp_cmd.value for sp_cmd in SPECIAL_COMMANDS]:
                return self.handle_commands(query)
            
            msgs_to_send = await self.get_context_with_current_msg(query)
            print(f"Context: {msgs_to_send}")

            inference_instance = Inference()
            response = await inference_instance.run(msgs_to_send)

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
