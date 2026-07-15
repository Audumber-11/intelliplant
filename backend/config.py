from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    app_name: str = "IntelliPlant Safety Intelligence"
    app_version: str = "2.0.0"
    debug: bool = Field(default=True, validation_alias="DEBUG")
    
    # Database - use SQLite for development
    database_url: str = Field(
        default="sqlite+aiosqlite:///./intelliplant.db",
        validation_alias="DATABASE_URL"
    )
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # ChromaDB
    chroma_path: str = Field(default="./chroma_db", validation_alias="CHROMA_PATH")
    chroma_collection: str = "industrial_safety"
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")
    
    # Kafka (for sensor streams)
    kafka_bootstrap_servers: str = Field(default="localhost:9092", validation_alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_sensor_topic: str = "sensor.readings"
    kafka_permit_topic: str = "permits.events"
    kafka_alert_topic: str = "safety.alerts"
    
    # Anthropic
    anthropic_api_key: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    anthropic_model: str = "claude-sonnet-4-6"
    
    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 1000
    
    # Risk Engine
    risk_evaluation_interval_seconds: int = 10
    risk_correlation_window_minutes: int = 60
    risk_alert_cooldown_minutes: int = 5
    
    # Geospatial
    plant_layout_geojson: str = Field(default="./data/plant_layout.geojson", validation_alias="PLANT_LAYOUT_GEOJSON")
    asset_tracking_enabled: bool = True
    
    # Emergency
    emergency_webhook_url: str = Field(default="", validation_alias="EMERGENCY_WEBHOOK_URL")
    emergency_sms_provider: str = Field(default="twilio", validation_alias="EMERGENCY_SMS_PROVIDER")
    emergency_sms_account_sid: str = Field(default="", validation_alias="EMERGENCY_SMS_ACCOUNT_SID")
    emergency_sms_auth_token: str = Field(default="", validation_alias="EMERGENCY_SMS_AUTH_TOKEN")
    emergency_sms_from_number: str = Field(default="", validation_alias="EMERGENCY_SMS_FROM_NUMBER")
    
    # Compliance
    oisd_standards_path: str = Field(default="./data/standards/oisd", validation_alias="OISD_STANDARDS_PATH")
    factory_act_path: str = Field(default="./data/standards/factory_act", validation_alias="FACTORY_ACT_PATH")
    dgms_standards_path: str = Field(default="./data/standards/dgms", validation_alias="DGMS_STANDARDS_PATH")
    
    # Logging
    log_level: str = Field(default="DEBUG", validation_alias="LOG_LEVEL")
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()