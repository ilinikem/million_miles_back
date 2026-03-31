import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    API_KEY: str
    ADMIN_API_KEY: str
    ENVIRONMENT: str

    encar_api_base: str = "https://www.encar.com"
    encar_list_path: str = "/mobileapi/search/car/list/general"
    encar_query: str = ""
    encar_image_base: str = "https://img.encar.com"
    encar_detail_base: str = "https://www.encar.com/dc/dc_cardetailview.do"
    encar_page_size: int = Field(default=30, ge=1, le=600)
    encar_request_delay_sec: float = Field(default=0.5, ge=0)
    encar_beat_hour_utc: int = Field(default=3, ge=0, le=23)
    encar_beat_minute: int = Field(default=0, ge=0, le=59)

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../.env"
        ),
        extra="ignore",
    )

    def get_db_url(self):
        env = os.getenv("ENVIRONMENT", "dev")
        if env == "prod":
            self.DB_HOST = "db"
        return (f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")


settings = Settings()
