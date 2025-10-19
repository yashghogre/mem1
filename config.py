from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class _CONFIG(BaseSettings):
    MODEL_PATH: str
    CTX_LENGTH: int = Field(default=32768)

    MODEL_TEMP: float = Field(default=1.0)
    MODEL_NAME: str
    MODEL_BASE_URL: str
    MODEL_API_KEY: str

    INFERENCE_TYPE: Literal["local", "api"] = Field(default="api")

    MONGO_USER: str
    MONGO_PASS: str
    MONGO_MSG_DB: str
    MONGODB_URI: str

    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str

    EMBEDDING_URL: str
    EMBEDDING_MODEL: str

    QDRANT_URL: str
    QDRANT_COLLECTION: str

    GRAPHDB_URL: str
    GRAPHDB_USER: str
    GRAPHDB_PASS: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encodings="utf-8")

CONFIG = _CONFIG()
