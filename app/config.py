"""Configuration management using Pydantic Settings"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Azure Bot Configuration
    azure_bot_id: str = Field(default="", alias="AZURE_BOT_ID")
    azure_bot_password: str = Field(default="", alias="AZURE_BOT_PASSWORD")
    
    # Azure OpenAI Configuration
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_api_endpoint: str = Field(default="", alias="OPENAI_API_ENDPOINT")
    openai_api_version: str = Field(default="2024-02-15-preview", alias="OPENAI_API_VERSION")
    openai_deployment_name: str = Field(default="gpt-4o", alias="OPENAI_DEPLOYMENT_NAME")
    
    # GitHub Configuration
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")
    
    # Azure Functions
    azure_web_jobs_storage: str = Field(default="", alias="AzureWebJobsStorage")
    
    @property
    def is_configured(self) -> bool:
        """Check if required configuration is present"""
        return bool(
            self.azure_bot_id and 
            self.azure_bot_password and 
            self.openai_api_key and 
            self.openai_api_endpoint
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
