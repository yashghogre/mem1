import asyncio
from datetime import datetime
import logging
from qdrant_client import AsyncQdrantClient, models
from typing import List
import uuid

from config import CONFIG
from .embedder import Embedder


logger = logging.getLogger(__name__)


class VectorSearchException(Exception):
    ...

class _VectorSearch:
    def __init__(self):
        self.client = AsyncQdrantClient(url=CONFIG.QDRANT_URL)
        self.embedder = Embedder()
        self.collection_name = CONFIG.QDRANT_COLLECTION


    async def setup(self):
        try:
            if not await self.client.collection_exists(CONFIG.QDRANT_COLLECTION):
                await self.client.create_collection(
                    collection_name=CONFIG.QDRANT_COLLECTION,
                    vectors_config=models.VectorParams(
                        size=CONFIG.QDRANT_DIMENSION_SIZE,
                        distance=models.Distance.COSINE,
                    )
                )
            logger.info(f"Vector Search setup successfully!")
        except Exception as e:
            raise VectorSearchException(f"Error while setting up Vector Search (Collection creation)")


    def get_client(self):
        if not self.client:
            logger.error(f"VectorDB Client not found. Initialize it first.")
            raise VectorSearchException(f"VectorDB Client not found. Initialize it first.")
        return self.client


#NOTE: Can move this to assistant or just keep it here.
VectorSearch = _VectorSearch()
