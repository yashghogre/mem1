import asyncio
import httpx
from typing import List, Optional

from config import CONFIG


class EmbedderException(Exception):
    ...


class Embedder:
    def __init__(self):
        self.timeout = 10.0
        self.client = httpx.AsyncClient(base_url=CONFIG.EMBEDDING_URL, timeout=self.timeout)
        self.embed_endpoint = "/embed"


    async def embed(self, text: str) -> List[float]:
        try:
            payload = {"inputs": [text]}

            response = await self.client.post(self.embed_endpoint, json=payload)
            response.raise_for_status()
            embeddings = response.json()

            return embeddings[0]
        
        except httpx.HTTPStatusError as e:
            raise EmbedderException(f"HTTP error occurred: {str(e)}")

        except httpx.RequestError as e:
            raise EmbedderException(f"An error occurred while requesting {e.request.url!r}: {str(e)}")


    async def embed_batch(self, text: List[str]) -> List[float]:
        try:
            payload = {"inputs": text}

            response = await self.client.post(self.embed_endpoint, json=payload)
            response.raise_for_status()
            embeddings = response.json()

            return embeddings

        except httpx.HTTPStatusError as e:
            raise EmbedderException(f"HTTP error occurred: {str(e)}")

        except httpx.RequestError as e:
            raise EmbedderException(f"An error occurred while requesting {e.request.url!r}: {str(e)}")
