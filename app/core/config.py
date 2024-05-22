from pydantic_settings import BaseSettings
from pydantic import Field, PrivateAttr
from typing import Optional


class AppConfig(BaseSettings):
    port: int
    host: str

    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_name: str
    _postgres_url: Optional[str] = PrivateAttr(default=None)

    redis_host: str
    redis_port: int
    redis_password: str

    @property
    def postgres_url(self) -> str:
        if self._postgres_url is None:
            self._postgres_url = (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
                f"{self.postgres_host}:{self.postgres_port}/{self.postgres_name}"
            )
        return self._postgres_url

    class Config:
        env_file = '.env'


config = AppConfig()
