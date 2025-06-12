from pydantic import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    env: str = "development"

    class Config:
        env_file = ".env"
