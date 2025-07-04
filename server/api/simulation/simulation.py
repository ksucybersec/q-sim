import logging
from fastapi import APIRouter, HTTPException, status, Body
from typing import Dict, Any

from pydantic import BaseModel


from data.models.topology.world_model import get_topology_from_redis
from server.api.simulation.manager import SimulationManager

simulation_router = APIRouter(prefix="/simulation", tags=["Simulation"])

try:
    manager = SimulationManager.get_instance()
except Exception as e:
    print(f"CRITICAL: Failed to initialize SimulationManager: {e}")
    manager = None


class SendMessageRequest(BaseModel):
    from_node_name: str
    to_node_name: str
    message: str


@simulation_router.get("/status/", summary="Get current simulation status")
async def get_simulation_status():
    """
    Returns whether the simulation managed by the SimulationManager is currently running.
    """
    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulation Manager not initialized",
        )
    return {"is_running": manager.is_running}


@simulation_router.post(
    "/message/",
    status_code=status.HTTP_200_OK,
    summary="Send a message/command to the running simulation",
)
async def send_simulation_message(message_data: SendMessageRequest):
    """
    Sends a command (provided as JSON in the request body)
    to the simulation via the SimulationManager.
    Requires the simulation to be running.
    """
    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulation Manager not initialized",
        )

    if not manager.is_running:
        # Use HTTPException for errors - more standard in FastAPI
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Simulation Not Running"
        )

    try:
        manager.send_message_command(**message_data.model_dump())

        return {"message": "Message command sent"}
    except TypeError as e:
        logging.exception("Invalid message data format: ", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid message data format: {e}",
        )
    except Exception as e:
        print(f"Error sending simulation message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


@simulation_router.delete("/", summary="Stop the currently running simulation")
async def stop_simulation():
    """
    Stops the simulation if it is currently running.
    """
    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulation Manager not initialized",
        )

    if not manager.is_running:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Simulation not running"
        )

    try:
        manager.stop()
        return {"message": "Simulation Stopped"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop simulation: {str(e)}",
        )


@simulation_router.api_route(
    "/{topology_id}",
    methods=["GET", "POST"],
    status_code=status.HTTP_201_CREATED,
    summary="Start the simulation using the network file",
    responses={
        status.HTTP_409_CONFLICT: {"description": "Simulation already running"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Error during simulation start"
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Simulation Manager not initialized"
        },
    },
)
async def execute_simulation(topology_id: str):
    """
    Starts the simulation using the predefined 'network.json' file.
    Returns 201 Created on success.
    Returns 409 Conflict if the simulation is already running.
    Returns 500 Internal Server Error if starting fails.
    Accessible via both GET and POST requests.
    """
    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulation Manager not initialized",
        )

    world = get_topology_from_redis(topology_id)

    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topology with ID '{topology_id}' not found.",
        )

    try:
        simulation_started = manager.start_simulation(world)

        if not simulation_started:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Simulation already running",
            )

        return simulation_started

    except Exception as e:
        print(f"Error starting simulation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting simulation: {str(e)}",
        )
