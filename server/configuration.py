import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseSettings, Field, validator
from typing import Dict, Any, Optional

# Get the directory of the current file
current_dir = Path(__file__).resolve().parent

# Construct the path to the .env file (assuming it's in the parent directory)
env_path = current_dir.parent / '.env'

# Load the .env file
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # Server settings
    HOST: str = Field(..., env="HOST")
    PORT: int = Field(..., env="PORT")

    # Database settings
    DB_TYPE: str = Field(..., env="DB_TYPE")
    DB_HOST: str = Field(..., env="DB_HOST")
    DB_PORT: Optional[int] = Field(None, env="DB_PORT")
    DB_NAME: str = Field(..., env="DB_NAME")
    DB_USER: str = Field(..., env="DB_USER")
    DB_PASSWORD: str = Field(..., env="DB_PASSWORD")

    # MQTT settings
    MQTT_BROKER: str = Field(..., env="MQTT_BROKER")
    MQTT_PORT: int = Field(..., env="MQTT_PORT")
    MQTT_USERNAME: str = Field(..., env="MQTT_USERNAME")
    MQTT_PASSWORD: str = Field(..., env="MQTT_PASSWORD")
    MQTT_SUBSCRIBE_TOPIC: str = Field(..., env="MQTT_SUBSCRIBE_TOPIC")
    MQTT_PUBLISH_TOPIC: str = Field(..., env="MQTT_PUBLISH_TOPIC")

    # Logging settings
    LOG_LEVEL: str = Field(..., env="LOG_LEVEL")
    LOG_FILE: str = Field(..., env="LOG_FILE")
    LOG_MAX_SIZE: Optional[int] = Field(None, env="LOG_MAX_SIZE")
    LOG_BACKUP_COUNT: int = Field(..., env="LOG_BACKUP_COUNT")

    # Message processing settings
    MESSAGE_PROCESSING_INTERVAL: Optional[int] = Field(None, env="MESSAGE_PROCESSING_INTERVAL")

    class Config:
        env_file = str(env_path)
        env_file_encoding = "utf-8"

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of {allowed_levels}")
        return v

    @validator("DB_TYPE")
    def validate_db_type(cls, v):
        allowed_types = ["postgres", "mysql", "sqlite"]
        if v not in allowed_types:
            raise ValueError(f"DB_TYPE must be one of {allowed_types}")
        return v

    @validator("PORT", "MQTT_PORT", "LOG_BACKUP_COUNT")
    def validate_positive_int(cls, v):
        if v <= 0:
            raise ValueError(f"Value must be a positive integer, but got {v}")
        return v

    @validator("DB_PORT", "LOG_MAX_SIZE", "MESSAGE_PROCESSING_INTERVAL")
    def validate_optional_positive_int(cls, v):
        if v is not None and v <= 0:
            raise ValueError(f"Value must be a positive integer or None, but got {v}")
        return v

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.validate()

    def validate(self):
        # Add any additional validation logic here
        pass

    @classmethod
    def reload(cls):
        load_dotenv(dotenv_path=env_path, override=True)
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

settings = Settings()

def get_settings():
    return settings

def reload_settings():
    global settings
    settings = Settings.reload()
    return settings