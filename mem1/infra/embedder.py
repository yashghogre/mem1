import asyncio
import httpx
import logging
from typing import List, Optional


logger = logging.getLogger(__name__)


class EmbedderUtils:
    def __init__(self, embedder_client: httpx.AsyncClient):
        self.client = embedder_client
        self.embed_endpoint = "/embed"


    async def embed(self, text: str) -> List[float]:
        try:
            payload = {"inputs": [text]}

            response = await self.client.post(self.embed_endpoint, json=payload)
            response.raise_for_status()
            embeddings = response.json()

            return embeddings[0]
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {str(e)}")
            raise EmbedderException(f"HTTP error occurred: {str(e)}")

        except httpx.RequestError as e:
            logger.error(f"An error occurred while requesting {e.request.url!r}: {str(e)}")
            raise EmbedderException(f"An error occurred while requesting {e.request.url!r}: {str(e)}")


    async def embed_batch(self, text: List[str]) -> List[float]:
        try:
            payload = {"inputs": text}

            response = await self.client.post(self.embed_endpoint, json=payload)
            response.raise_for_status()
            embeddings = response.json()

            return embeddings

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {str(e)}")
            raise EmbedderException(f"HTTP error occurred: {str(e)}")

        except httpx.RequestError as e:
            logger.error(f"An error occurred while requesting {e.request.url!r}: {str(e)}")
            raise EmbedderException(f"An error occurred while requesting {e.request.url!r}: {str(e)}")
