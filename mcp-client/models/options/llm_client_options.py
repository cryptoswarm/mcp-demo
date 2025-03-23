from typing import Optional
from pydantic import Field, BaseModel


class LLMClientOptions(BaseModel):
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
