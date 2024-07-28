from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # Server settings
    HOST: str = Field(..., env="HOST")
    PORT: int = Field(..., env="PORT")

    # Database settings
    DB_TYPE: str = Field(..., env="DB_TYPE")
    DB_HOST: str = Field(..., env="DB_HOST")
    DB_PORT: int = Field(default=0, env="DB_PORT")
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
    LOG_MAX_SIZE: int = Field(..., env="LOG_MAX_SIZE")
    LOG_BACKUP_COUNT: int = Field(..., env="LOG_BACKUP_COUNT")

    # Message processing settings
    MESSAGE_PROCESSING_INTERVAL: int = Field(..., env="MESSAGE_PROCESSING_INTERVAL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **data):
        super().__init__(**data)
        self.validate()

    def validate(self):
        # Add any additional validation logic here
        pass