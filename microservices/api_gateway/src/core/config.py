import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = os.getenv("POSTGRES_HOST", "db")
    DB_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    DB_USER: str = os.getenv("POSTGRES_USER", "user")
    DB_PASS: str = os.getenv("POSTGRES_PASSWORD", "password")
    DB_NAME: str = os.getenv("POSTGRES_DB", "portfolio_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_super_secret_key_that_is_long_and_random")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
