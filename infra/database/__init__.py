import asyncio
import logging
from typing import Literal
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config import CONFIG
from .schema import Message, ChatSummary


logger = logging.getLogger(__name__)

class _DBStore:
    def __init__(self):
        self.client = None

    async def init_db(self):
        try:
            self.client = AsyncIOMotorClient(CONFIG.MONGODB_URI)

            await self.client.admin.command("ping")

            await init_beanie(
                database=self.client.get_database(CONFIG.MONGO_MSG_DB),
                document_models=[
                    Message,
                    ChatSummary,
                ],
            )
            logger.info(f"MongoDB setup completed!")

        except Exception as e:
            logger.error(f"MongoDB setup failed. Error: {str(e)}")


    # Message Methods
    async def store_message(self, role: Literal["system", "user", "assistant"], content: str):
        if self.client is None:
            logger.error(f"DB client is not initialized. Initialize if first.")
            raise Exception(f"DB client is not initialized. Initialize if first.")

        message = Message(
            role=role,
            content=content,
        )
        await message.insert()

    async def get_messages(self):
        if self.client is None:
            logger.error(f"DB client is not initialized. Initialize if first.")
            raise Exception(f"DB client is not initialized. Initialize if first.")

        return await Message.find_all().to_list()

    async def delete_messages(self):
        if self.client is None:
            logger.error(f"DB client is not initialized. Initialize if first.")
            raise Exception(f"DB client is not initialized. Initialize if first.")

        await Message.find_all().delete()


    # Chat Summary Methods
    async def store_chat_summary(self, summary: str):
        if self.client is None:
            logger.error(f"DB client is not initialized. Initialize if first.")
            raise Exception(f"DB client is not initialized. Initialize if first.")

        if await ChatSummary.find_all().to_list():
            chat_summary = await ChatSummary.find_all().to_list()[0]
            chat_summary.summary = summary
            chat_summary.save()
        else:
            chat_summary = ChatSummary(summary=summary)
            await chat_summary.insert()


    async def get_chat_summary(self):
        if self.client is None:
            logger.error(f"DB client is not initialized. Initialize if first.")
            raise Exception(f"DB client is not initialized. Initialize if first.")

        return await ChatSummary.find_all().to_list()[0]


DBStore = _DBStore()
