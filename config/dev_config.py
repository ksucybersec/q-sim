from pydantic import BaseModel, Field


class DevConfig(BaseModel):
    enable_mock_responses: bool = Field(
        False,
        description="Enable mock responses for testing purposes.",
    )