import asyncio
from typing import Literal
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config import CONFIG
from .schema import Message


class _DBStore:
    async def init_db(self):
        client = AsyncIOMotorClient(CONFIG.MONGODB_URI)
        await init_beanie(
            database=client.get_database(CONFIG.MONGO_MSG_DB),
            document_models=[
                Message,
            ],
        )
        print(f"MongoDB setup completed!")


    async def store_message(self, role: Literal["system", "user", "assistant"], content: str):
        message = Message(
            role=role,
            content=content,
        )
        await message.insert()

    async def get_messages(self):
        return await Message.find_all().to_list()

    async def delete_messages(self):
        await Message.find_all().delete()


DBStore = _DBStore()
