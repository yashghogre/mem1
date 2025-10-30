import asyncio
from enum import StrEnum
import logging

from ..infra.database import DBStore
from ..infra.vector_db import VectorSearch


logger = logging.getLogger(__name__)


class SPECIAL_COMMANDS(StrEnum):
    EXIT = "/exit"
    RESET = "/reset"

async def handle_commands(query: str):
    try:
        match query:
            case SPECIAL_COMMANDS.EXIT.value:
                logger.info(f"User exit the application.")
                print("Exiting...")
                return  

            case SPECIAL_COMMANDS.RESET.value:
                #NOTE: For now, we will simply clear all the messages from the DB
                # instead of changing the thread and retaining the previous messages.
                logger.info(f"User reset the context.")
                await DBStore.delete_messages()
                await VectorSearch.delete_all_points()
                print("\nContext cleared!\n")

            case _:
                logger.info(f"Unknown command from user: {query}")

    except Exception as e:
        raise Exception(f"Error while handling special commands: {str(e)}")
