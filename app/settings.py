from os import getenv
from typing import Optional
from pydantic import MongoDsn, Field, StrictBool
from pydantic_settings import BaseSettings, SettingsConfigDict



class _Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_prefix='dester_')
    
    api_v1_str: str = Field("/api/v1")
    on_heroku: bool = StrictBool(getenv("DYNO") is not None)
    port: int = Field(35500)
    dev: bool = Field(False)
    rclone_port: int = Field(35530)
    
    
    mongo_dns: MongoDsn | None = Field(None) # 3.11

settings = _Settings()
