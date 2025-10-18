import asyncio
from datetime import datetime
from qdrant_client import AsyncQdrantClient, models
from typing import List
import uuid

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


    async def store_point(self, text: str):
        try:
            chunk_id = str(uuid.uuid4())
            current_time = datetime.now()
            time_now = current_time.strftime("%Y-%m-%d %H:%M:%S")
            chunk_vector = self.embedder.embed(text)
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=chunk_id,
                        vector=chunk_vector,
                        payload={
                            "text": text,
                            "timestamp": time_now,
                        },
                    )
                ],
            )

        except Exception as e:
            raise VectorSearchException(f"Error while storing memory in Vector DB.")


    async def store_points(self, text: List[str]):
        try:
            chunk_vector = self.embedder.embed_batch(text)
            points_to_store = []
            for i, line in enumerate(text):
                chunk_id = str(uuid.uuid4())
                current_time = datetime.now()
                time_now = current_time.strftime("%Y-%m-%d %H:%M:%S")
                point_to_store = models.PointStruct(
                    id=chunk_id,
                    vector=chunk_vector[i],
                    payload={
                        "text": line,
                        "timestamp": time_now,
                    },
                )
                points_to_store.append(point_to_store)

            await self.client.upsert(
                collection_name=self.collection_name,
                points=points_to_store,
            )

        except Exception as e:
            raise VectorSearchException(f"Error while storing memories in Vector DB.")


    async def delete_points(self):
        # Don't know yet what to delete, so leaving it empty for now.
        return
