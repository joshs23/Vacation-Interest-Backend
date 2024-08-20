from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_PASSWORD: str
    DB_USERNAME: str
    DB_NAME: str
    DB_HOST: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRES_MINUTES: int

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()