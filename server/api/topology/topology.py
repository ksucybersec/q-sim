import logging
import aiofiles  # Library for async file operations
from fastapi import APIRouter, Body, HTTPException, Header, Response, Request, status
from typing import Any, List, Optional

from pydantic import ValidationError

from classical_network.presets.connection_presets import CONFIG_PRESETS
from data.models.topology.world_model import (
    WorldModal,
    get_all_topologies_from_redis,
    get_topology_from_redis,
    save_world_to_redis,
    update_world_in_redis,
)  # For type hinting the request body


topology_router = APIRouter(
    prefix="/topology",  # Matches url_prefix
    tags=["Topology"],  # Optional: For grouping in API docs
)

NETWORK_FILE = "network.json"  # Keep the constant

@topology_router.get("/connection_config_presets", status_code=status.HTTP_200_OK)
async def get_connection_config_presets():
    """
    Retrieves all connection configuration presets and returns them as JSON.
    """
    preset_json = []
    for preset_name, preset_config in CONFIG_PRESETS.items():
        preset_json.append({
            "preset_name": preset_name,
            "preset_config": preset_config.to_dict(),
        })
    return preset_json

@topology_router.put("/{topology_id}", status_code=status.HTTP_201_CREATED)
@topology_router.put("/", status_code=status.HTTP_201_CREATED)
async def update_topology(
    topology_data: WorldModal = Body(), topology_id: Optional[str] = None, owner=Header(None, alias='Authorization')
):
    """
    Receives topology data (expected as JSON in the request body),
    validates basic structure (by virtue of FastAPI parsing it),
    and saves it to the network file asynchronously.

    The topology_id is expected in the URL, with a default value of 'default'.

    Returns the saved data.
    """
    topology_data.owner = owner
    try:
        if topology_id:
            topology_data = update_world_in_redis(topology_id, topology_data.model_dump())
        else:
            topology_data = save_world_to_redis(topology_data)

        return topology_data

    except TypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data provided, cannot serialize to JSON: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save topology data due to a server error.",
        )


@topology_router.get(
    "/{topology_id}", status_code=status.HTTP_200_OK
)
async def get_topology(topology_id: str, owner=Header(None, alias='Authorization')):
    """
    Reads the topology data from the network file asynchronously
    and returns its content directly.
    """

    try:
        world = get_topology_from_redis(topology_id)
        if not world:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topology with id '{topology_id}' not found.",
            )
        return world

    except ValidationError as e:
        logging.exception("Validation error while retrieving topologies: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'error': f"Invalid data provided, cannot serialize to JSON",
                'details': e.errors(),
            },
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not read topology data due to a server error.",
        )


@topology_router.get('/')
async def list_all_topologies(owner=Header(None, alias='Authorization')):
    """
    Lists all topologies available in the Redis database.
    """
    try:
        # Assuming you have a function to list all topologies
        topologies = get_all_topologies_from_redis(owner=owner)
        return topologies

    except ValidationError as e:
        logging.exception("Validation error while retrieving topologies: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'error': f"Invalid data provided, cannot serialize to JSON",
                'details': e.errors(),
            },
        )
    
    except Exception as e:
        logging.exception("Error retrieving topologies from Redis: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve topology data due to a server error.",
        )