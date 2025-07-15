"""World model for network simulation"""

from typing import List, Tuple, Dict, Any, Optional, Union
from pydantic import Field
from redis_om import JsonModel, Field as RedisField, Migrator

from data.models.connection.redis import get_redis_conn
from data.models.topology.zone_model import ZoneModal


class WorldModal(JsonModel):
    """Root model representing the entire simulation world"""

    owner: Optional[str] = Field(
        description="Owner of the simulation world", default="Default"
    )
    name: str = RedisField(index=True, description="Name of the simulation world")
    size: Tuple[float, float] = Field(
        description="Size of the simulation world in (x, y) coordinates"
    )
    zones: List[ZoneModal] = Field(
        description="List of zones within the simulation world"
    )
    temporary_world: bool = RedisField(
        default=False, description="Flag to indicate if the world is temporary"
    )
    lab_world: bool = RedisField(
        default=False,
        description="Flag to indicate if the world is a lab world. Mostly ignored and unused in production.",
    )

    def get_host_by_name(self, host_name: str):
        for zone in self.zones:
            if zone.get_host_by_name(host_name):
                return zone.get_host_by_name(host_name)
        return None

    def get_network_by_host(self, host_name: str):
        """Get the network by host name"""
        for zone in self.zones:
            for network in zone.networks:
                for host in network.hosts:
                    if host.name == host_name:
                        return network
        return None

    class Meta:
        global_key_prefix = "network-sim"
        model_key_prefix = "world"
        database = get_redis_conn()


def save_world_to_redis(world: Union[Dict[str, Any], WorldModal]) -> WorldModal:
    """Save world data to Redis"""
    # Ensure we have a connection
    get_redis_conn()

    # Ensure indexes are created
    Migrator().run()

    # Create World instance
    if isinstance(world, dict):
        world = WorldModal(**world)

    # Save to Redis
    world.save()

    return world


def update_world_in_redis(
    primary_key: str, update_data: Dict[str, Any]
) -> Optional[WorldModal]:
    get_redis_conn()

    try:
        world_to_update = WorldModal.get(primary_key)

        for field, value in update_data.items():
            if hasattr(world_to_update, field):
                setattr(world_to_update, field, value)
            else:
                print(
                    f"Warning: Field '{field}' not found in WorldModal model. Skipping update for this field."
                )
        world_to_update.save()
        print(f"Successfully updated WorldModal with PK: {primary_key}")

        # 4. Return the updated object
        return world_to_update
    except Exception as e:
        print(f"Error updating WorldModal with PK '{primary_key}': {e}")
        # Log the full traceback for detailed debugging
        import traceback

        traceback.print_exc()
        return None


def get_topology_from_redis(primary_key: str) -> Optional[WorldModal]:
    """Retrieve world data from Redis by primary key"""
    # Ensure we have a connection
    get_redis_conn()

    try:
        return WorldModal.get(primary_key)
    except Exception as e:
        print(f"Error retrieving world data: {e}")
        return None


def get_all_topologies_from_redis(
    temporary_world=False, owner=None
) -> List[WorldModal]:
    """Retrieve all worlds from Redis"""
    # Ensure we have a connection
    get_redis_conn()

    worlds = WorldModal.find(WorldModal.temporary_world == temporary_world).all()

    print(list(map(lambda w: w.owner, worlds)))

    worlds = list(filter(lambda w: owner is None or w.owner == owner, worlds))

    return worlds


def delete_topology_from_redis(primary_key: str) -> bool:
    """Delete world data from Redis by primary key"""
    # Ensure we have a connection
    get_redis_conn()

    try:
        world = WorldModal.get(primary_key)
        world.delete()
        return True
    except Exception as e:
        print(f"Error deleting world data: {e}")
        return False
