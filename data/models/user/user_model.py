from typing import Optional
from pydantic import Field
from redis_om import JsonModel, Field as RedisField

from data.models.connection.redis import get_redis_conn


class UserModal(JsonModel):
    username: str = RedisField(description="Unique identifier for the user", index=True)
    name: Optional[str] = Field(description="First name of the user", default="")
    
    class Meta:
        global_key_prefix = "network-sim"
        model_key_prefix = "user"
        database = get_redis_conn()