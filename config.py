from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class _CONFIG(BaseSettings):
    MODEL_PATH: str
    CTX_LENGTH: int = Field(default=32768)
    MODEL_TEMP: float = Field(default=1.0)

    MONGO_USER: str
    MONGO_PASS: str
    MONGO_MSG_DB: str
    MONGODB_URI: str

    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encodings="utf-8")

CONFIG = _CONFIG()
