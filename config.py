from pydantic_settings import BaseSettings, SettingsConfigDict

class _CONFIG(BaseSettings):
    MODEL_PATH: str
    CTX_LENGTH: int = 32768
    MODEL_TEMP: float = 1.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encodings="utf-8")

CONFIG = _CONFIG()
