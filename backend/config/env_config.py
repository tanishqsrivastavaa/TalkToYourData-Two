from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str
    LLM_MODEL: str
    model_config = SettingsConfigDict(env_file=".env",env_file_encoding="utf-8")

settings = Settings()
