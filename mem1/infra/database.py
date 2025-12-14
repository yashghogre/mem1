import asyncio
from beanie import Document
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)


class DatabaseUtils:
    def __init__(self, db_client: AsyncIOMotorClient, collection: Document):
        self.client = db_client
        self.collection = collection
        # NOTE: For now, I am taking the collection from the assistant [bad practice :(],
        # but I will change this entire thing soon.
        # TODO: Make the collection inside Mem1 and add it into the client from here.

    async def store_chat_summary(self, summary: str):
        if self.client is None:
            logger.error(f"Database client is not initialized. Initialize it first.")
            raise Exception(f"Database client is not initialized. Initialize it first.")

        chat_summary = await self.collection.find_all().to_list()
        if chat_summary:
            chat_summary = chat_summary[0]
            chat_summary.summary = summary
            await chat_summary.save()
        else:
            chat_summary = self.collection(summary=summary)
            await chat_summary.insert()

    async def get_chat_summary(self):
        if self.client is None:
            logger.error(f"DB client is not initialized. Initialize if first.")
            raise Exception(f"DB client is not initialized. Initialize if first.")

        chat_summary = await self.collection.find_all().to_list()

        if chat_summary:
            return chat_summary[0]
        else:
            return None
