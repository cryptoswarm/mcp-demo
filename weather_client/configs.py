from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMClientConfig(BaseModel):
    enabled: bool = Field(default=False)
    is_default: bool = Field(default=False)
    host: str = Field(default="aoai")
    endpoint: str = Field(default="")
    custom_url: Optional[str] = Field(default="")
    resource: Optional[str] = Field(default="")
    service: Optional[str] = Field(default="")
    api_key: str = Field(default="")
    model_deployment_id: str = Field(default="")
    model_name: str = Field(default="")
    api_version: Optional[str] = Field(default="")
    organization: Optional[str] = Field(default="")
    project: Optional[str] = Field(default="")


class LlmClientsConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
        env_prefix="LLM_CLIENTS_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    AOAI: LLMClientConfig
