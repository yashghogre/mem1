import asyncio
from qdrant_client import AsyncQdrantClient

from config import CONFIG


class VectorSearchException(Exception):
    ...

class VectorSearch:
    def __init__(self):
        self.client = AsyncQdrantClient(url=CONFIG.QDRANT_URL)

    async def setup(self):
        try:
            if not await self.client.collection_exists(CONFIG.QDRANT_COLLECTION):
                await self.client.create_collection(collection_name=CONFIG.QDRANT_COLLECTION)
            print(f"Vector Search setup successfully!")
        except Exception as e:
            raise VectorSearchException(f"Error while setting up Vector Search (Collection creation)")
