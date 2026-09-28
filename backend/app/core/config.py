"""Chimera-X Brain — application settings.

Single source of truth for all configuration.
Provider keys fall back to environment variables if not in the DB.
"""

import os
from typing import Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Chimera-X Brain"

    # Provider API keys — fallback to env if not stored in Provider table
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OLLAMA_API_BASE: str = "http://localhost:11434"

    # Simple routing map (legacy — will be replaced by DB-driven router in Phase 2)
    routing_rules: Dict[str, str] = {
        "auto": "gpt-4o-mini",
        "auto-code": "claude-3-5-sonnet-20240620",
        "auto-chat": "gpt-3.5-turbo",
    }

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
