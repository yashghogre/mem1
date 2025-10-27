import asyncio
from datetime import datetime
from qdrant_client import AsyncQdrantClient, models
from typing import List
import uuid

from config import CONFIG
from infra.embedder import Embedder


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
            print(f"Vector Search setup successfully!")
        except Exception as e:
            raise VectorSearchException(f"Error while setting up Vector Search (Collection creation)")


    async def store_point(self, text: str):
        try:
            chunk_id = str(uuid.uuid4())
            current_timestamp = int(datetime.now().timestamp())
            chunk_vector = await self.embedder.embed(text)
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=chunk_id,
                        vector=chunk_vector,
                        payload={
                            "text": text,
                            "timestamp": current_timestamp,
                        },
                    )
                ],
            )

        except Exception as e:
            raise VectorSearchException(f"Error while storing memory in Vector DB.")


    async def store_points(self, text: List[str]):
        try:
            chunk_vector = await self.embedder.embed_batch(text)
            points_to_store = []
            for i, line in enumerate(text):
                chunk_id = str(uuid.uuid4())
                current_timestamp = int(datetime.now().timestamp())
                point_to_store = models.PointStruct(
                    id=chunk_id,
                    vector=chunk_vector[i],
                    payload={
                        "text": line,
                        "timestamp": current_timestamp,
                    },
                )
                points_to_store.append(point_to_store)

            await self.client.upsert(
                collection_name=self.collection_name,
                points=points_to_store,
            )

        except Exception as e:
            raise VectorSearchException(f"Error while storing memories in Vector DB.")


    async def retrieve_point(self, text: str):
        try:
            text_emb = await self.embedder.embed(text)
            search_results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=text_emb,
                limit=1,
                with_payload=True,
                with_vectors=False,
            )

            if search_results:
                return search_results[0]
            else:
                return None

        except Exception as e:
            raise VectorSearchException(f"Error while retrieving memories in Vector DB.")


    async def retrieve_all_points(self):
        try:
            all_points = []
            next_offset = None

            while True:
                res_points, next_offset = await self.client.scroll(
                    collection_name=self.collection_name,
                    limit=100,
                    offset=next_offset,
                    with_payload=True,
                    with_vectors=False,
                )
                all_points.extend(res_points)
                if next_offset is None:
                    break

            return all_points

        except Exception as e:
            raise VectorSearchException(f"Error while retrieving all memories in Vector DB.")


    async def find_oldest_fact_and_delete(self):
        try:
            oldest_point, _ = await self.client.query_points(
                collection_name=self.collection_name,
                order_by=models.OrderBy(
                    key="timestamp",
                    direction=models.Direction.ASC,
                ),
                limit=1,
                with_payload=False,
                with_vectors=False,
            )

            if oldest_points:
                oldest_point_id = oldest_points[0].id
                await self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(
                        points=[oldest_point_id],
                    ),
                )
                return oldest_point_id
            else:
                return None

        except Exception as e:
            raise VectorSearchException(f"Error while finding oldest fact and deleting it.")


    async def delete_point(self, pnt):
        try:
            pnt_id = pnt.id
            rslt = await self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[pnt_id],
                ),
            )
            return rslt

        except Exception as e:
            raise VectorSearchException(f"Error while deleting a point.")


VectorSearch = _VectorSearch()
