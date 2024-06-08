from pydantic_settings import BaseSettings
from pydantic import PrivateAttr, ConfigDict


class AppConfig(BaseSettings):
    port: int
    host: str

    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_name: str
    postgres_test_name: str
    _postgres_url: str | None = PrivateAttr(default=None)
    _postgres_test_url: str | None = PrivateAttr(default=None)

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

    @property
    def postgres_test_url(self) -> str:
        if self._postgres_test_url is None:
            self._postgres_test_url = (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
                f"{self.postgres_host}:{self.postgres_port}/{self.postgres_test_name}"
            )
        return self._postgres_test_url

    model_config = ConfigDict(env_file=".env")


config = AppConfig()
