from pydantic import PostgresDsn, validator, BaseModel
from pydantic_settings import BaseSettings


class DataBaseSettings(BaseSettings):
    POSTGRES_USER: str = "ava"
    POSTGRES_PASSWORD: str = "ava"
    POSTGRES_DB: str = "ava"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"

    @property
    def uri(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


class DramatiqSettings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def broker(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


class MinioSettings(BaseSettings):
    MINIO_ACCESS_KEY: str = "kk3seAiMQRLcCrbhL8mo"
    MINIO_SECRET_KEY: str = "8LpQHc9LTuM1Ev4Io7k1b7Yu4g4wu8q7QB3YLVrn"
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


class Settings(BaseModel):
    db: DataBaseSettings = DataBaseSettings()
    dramatiq: DramatiqSettings = DramatiqSettings()
    minio: MinioSettings = MinioSettings()


cfg = Settings()
