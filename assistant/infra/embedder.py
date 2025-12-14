import asyncio
import httpx
import logging
from typing import List, Optional

from config import CONFIG


logger = logging.getLogger(__name__)


class EmbedderException(Exception): ...


class Embedder:
    def __init__(self):
        self.timeout = 10.0
        self.client = httpx.AsyncClient(
            base_url=CONFIG.EMBEDDING_URL, timeout=self.timeout
        )
        self.embed_endpoint = "/embed"

    def get_client(self):
        if not self.client:
            logger.error(f"Embedder client not found. Initialize it first.")
            raise EmbedderException(f"Embedder client not found. Initialize it first.")
        return self.client
