from pydantic import BaseModel


class ControlConfig(BaseModel):
    enable_ai_feature: bool = True
    enable_realtime_log_summary: bool = True
    # When True, run log summarization in Celery workers; when False, run in main process (in a thread pool to avoid blocking).
    realtime_log_summary_use_celery: bool = True
