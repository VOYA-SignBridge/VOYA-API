from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str
    app_env: str
    app_host: str
    app_port: int
    secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    database_url: str

    class Config:
        env_file = ".env"

settings = Settings()
