import uuid
import asyncio
from qdrant_client import AsyncQdrantClient, models
from typing import List

from config import CONFIG
from infra.embedder import Embedder


class VectorSearchException(Exception):
    ...

class VectorSearch:
    def __init__(self):
        self.client = AsyncQdrantClient(url=CONFIG.QDRANT_URL)
        self.embedder = Embedder()
        self.collection_name = CONFIG.QDRANT_COLLECTION


    async def setup(self):
        try:
            if not await self.client.collection_exists(CONFIG.QDRANT_COLLECTION):
                await self.client.create_collection(collection_name=CONFIG.QDRANT_COLLECTION)
            print(f"Vector Search setup successfully!")
        except Exception as e:
            raise VectorSearchException(f"Error while setting up Vector Search (Collection creation)")


    async def store_memory(self, text: str):
        try:
            chunk_id = str(uuid.uuid4())
            chunk_vector = self.embedder.embed(text)
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=chunk_id,
                        vector=chunk_vector,
                        payload={
                            "text": text,
                        },
                    )
                ],
            )

        except Exception as e:
            raise VectorSearchException(f"Error while storing memory in Vector DB.")


    async def store_memories(self, text: List[str]):
        try:
            chunk_vector = self.embedder.embed_batch(text)
            points_to_store = []
            for i, line in enumerate(text):
                chunk_id = str(uuid.uuid4())
                point_to_store = models.PointStruct(
                    id=chunk_id,
                    vector=chunk_vector[i],
                    payload={
                        "text": line,
                    },
                )
                points_to_store.append(point_to_store)

            await self.client.upsert(
                collection_name=self.collection_name,
                points=points_to_store,
            )

        except Exception as e:
            raise VectorSearchException(f"Error while storing memories in Vector DB.")


    async def delete_memories(self):
        # Don't know yet what to delete, so leaving it empty for now.
        return
