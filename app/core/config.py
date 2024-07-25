from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    port: int
    host: str

    oauth2_secret_key: str
    oauth2_algorithm: str
    oauth2_access_token_expire_days: int

    auth0_domain: str
    auth0_audience: str
    auth0_algorithms: list[str]

    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_name: str
    postgres_test_name: str

    redis_host: str
    redis_port: int
    redis_password: str

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_name}"
        )

    @property
    def postgres_test_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_test_name}"
        )

    model_config = SettingsConfigDict(env_file=".env")


config = AppConfig()
