from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from models.options.llm_client_options import LLMClientOptions


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="allow", env_nested_delimiter="__", case_sensitive=False
    )

    LLM_CLIENTS: List[LLMClientOptions]

    @field_validator("LLM_CLIENTS", mode="before")
    @classmethod
    def decode_llmclients_providers(cls, providers: dict) -> list[LLMClientOptions]:
        """Decode llm clients from the settings"""
        return [LLMClientOptions(**values) for host, values in providers.items()]
