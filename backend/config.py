"""
Application configuration loaded from environment variables.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from project root (parent of Backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


class Settings(BaseSettings):
    # --- Kaggle ---
    KAGGLE_USERNAME: str = ""
    KAGGLE_KEY: str = ""

    # --- HuggingFace (public API works without token) ---
    HUGGINGFACE_TOKEN: str = ""

    # --- GitHub (public API works without token, token = higher rate limit) ---
    GITHUB_TOKEN: str = ""

    # --- App ---
    MAX_DATASET_SIZE_MB: int = 200
    DOWNLOAD_DIR: str = "./downloads"

    @property
    def kaggle_available(self) -> bool:
        return bool(self.KAGGLE_USERNAME and self.KAGGLE_KEY)

    @property
    def max_dataset_bytes(self) -> int:
        return self.MAX_DATASET_SIZE_MB * 1024 * 1024

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Push Kaggle creds into env so the kaggle SDK picks them up
if settings.kaggle_available:
    os.environ["KAGGLE_USERNAME"] = settings.KAGGLE_USERNAME
    os.environ["KAGGLE_KEY"] = settings.KAGGLE_KEY
