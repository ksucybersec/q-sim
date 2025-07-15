
from fastapi import APIRouter
from config.config import get_config

config_router = APIRouter(
    prefix="/config",
    tags=["Config"],
)

@config_router.get("/")
async def handle_config_request():
    config = get_config()

    return config.control_config