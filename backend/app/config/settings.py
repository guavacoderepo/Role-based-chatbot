from pydantic import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    SECRET_KEY:str
    DB_PATH:str
    env: str = "development"

    class Config:
        env_file =  "backend/.env"
