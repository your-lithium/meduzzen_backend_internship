from pydantic_settings import BaseSettings
from pydantic import Field, model_validator
from typing import Optional


class AppConfig(BaseSettings):
    port: int
    host: str

    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_name: str
    postgres_url: Optional[str] = Field(default=None)

    redis_host: str
    redis_port: int
    redis_password: str

    @model_validator(mode="after")
    def assemble_postgres_url(cls, values):
        if all(getattr(values, field) for field in
               ['postgres_user', 'postgres_password', 'postgres_host', 'postgres_port', 'postgres_name']):
            values.postgres_url = (
                f"postgresql+asyncpg://{values.postgres_user}:{values.postgres_password}@"
                f"{values.postgres_host}:{values.postgres_port}/{values.postgres_name}"
            )
        return values

    class Config:
        env_file = '.env'


config = AppConfig()
