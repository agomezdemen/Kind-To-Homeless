from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Kind-To-Homeless API"
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

