from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    port: int
    host: str

    class Config:
        env_file = '.env'


config = AppConfig()
