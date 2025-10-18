from langfuse import Langfuse

from config import CONFIG

_langfuse_client = None

def init_langfuse():
    global _langfuse_client

    _langfuse_client = Langfuse(
        public_key=CONFIG.LANGFUSE_PUBLIC_KEY,
        secret_key=CONFIG.LANGFUSE_SECRET_KEY,
        host="http://localhost:3000",
    )
    print(f"Langfuse initialized successfully!")
    return _langfuse_client

def get_langfuse():
    if _langfuse_client is None:
        raise RuntimeError(f"Langfuse instance not found. Call init_langfuse() first.")
    return _langfuse_client
