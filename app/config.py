from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Background Removal API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Limits & Validation
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_CONTENT_TYPES: List[str] = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp"
    ]
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp"]

    # Engine Settings
    REMBG_MODEL: str = "u2net"

    # Authentication
    API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
