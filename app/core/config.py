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
    redis_url: str
    supabase_jwt_secret: str
    supabase_project_id: str
    supabase_jwks_url: str
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    class Config:
        env_file = ".env"

settings = Settings()
