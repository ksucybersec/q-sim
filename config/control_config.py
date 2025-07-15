from pydantic import BaseModel


class ControlConfig(BaseModel):
    enable_ai_feature: bool = True
    enable_realtime_log_summary: bool = True
