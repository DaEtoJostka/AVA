from pydantic import PostgresDsn, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MINIO_ACCESS_KEY: str = "z7RUf7Ne4FFqHh4UyuqU"
    MINIO_SECRET_KEY: str = "Le5xtxj2eQ6rKXZ4ac65WUKmYDheBOfzwEw7aru4"
    MINIO_HOST: str = "localhost"
    MINIO_PORT: int = 9000
    MINIO_SECURE: bool = False

    @property
    def minio_endpoint(self) -> str:
        return f"{self.MINIO_HOST}:{self.MINIO_PORT}"

    @property
    def minio_credentials(self) -> dict:
        return {
            "access_key": self.MINIO_ACCESS_KEY,
            "secret_key": self.MINIO_SECRET_KEY
        }

cfg = Settings()
