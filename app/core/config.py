from pydantic_settings import BaseSettings
import os


class AppConfig(BaseSettings):
    port: int
    host: str

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '../../.env')


config = AppConfig()
