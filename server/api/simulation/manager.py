import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pprint import pprint
import threading
import time
from typing import List, Optional, Dict, Any
import traceback

from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.log_summarization.structures import RealtimeLogSummaryInput
from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.orchestration.coordinator import Coordinator
from config.config import get_config
from core.base_classes import World
from core.enums import SimulationEventType
from core.event import Event
from data.embedding.embedding_util import EmbeddingUtil
from data.models.simulation.log_model import LogEntryModel, add_log_entry
from data.models.simulation.simulation_model import (
    SimulationModal,
    SimulationStatus,
    save_simulation,
    update_simulation_status,
)
from data.models.topology.world_model import WorldModal
from json_parser import simulate_from_json
from server.socket_server.socket_server import ConnectionManager
from tasks import summarize_logs_task

# Thread pool for in-process log summarization so the simulation thread is not blocked
_summary_executor: Optional[ThreadPoolExecutor] = None


def _get_summary_executor() -> ThreadPoolExecutor:
    global _summary_executor
    if _summary_executor is None:
        _summary_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="log_summary")
    return _summary_executor


def _run_summarization_inprocess(
    simulation_id: str,
    previous_summary: List[str],
    new_logs: List[str],
    conversation_id: str,
    main_event_loop: asyncio.AbstractEventLoop,
    on_done,  # callable(manager, result, error) invoked on main loop
    manager: "SimulationManager",
) -> None:
    """Run log summarization in a worker thread (same logic as Celery task). Calls on_done on main loop when done."""
    result, error = None, None
    try:
        coordinator = Coordinator()
        agent_args = RealtimeLogSummaryInput(
            simulation_id=simulation_id,
            previous_summary=previous_summary,
            new_logs=new_logs,
            conversation_id=conversation_id,
            optional_instructions=None,
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                coordinator._run_agent_task(AgentType.LOG_SUMMARIZER, {
                    "task_id": AgentTaskType.REALTIME_LOG_SUMMARY,
                    "input_data": agent_args,
                })
            )
        finally:
            loop.close()
    except Exception as e:
        error = e
    main_event_loop.call_soon_threadsafe(on_done, manager, result, error)


def _handle_inprocess_result(manager: "SimulationManager", result: Any, error: Optional[Exception]) -> None:
    """Called on main event loop when in-process summarization finishes. Updates state and emits event."""
    manager.last_summarized_on = time.time()
    if error is not None:
        print(f"Error in in-process log summarization: {error}")
        return
    if result is None:
        return
    try:
        new_summary = result.get("summary_text") if isinstance(result, dict) else None
        if new_summary is not None:
            if len(new_summary) == 1:
                manager.current_log_summary.append(new_summary[0])
            else:
                manager.current_log_summary = new_summary
        summary_result = dict(result)
        summary_result["summary_text"] = manager.current_log_summary
        manager.emit_event("simulation_summary", summary_result)
    except Exception as e:
        print(f"Error handling in-process summary result: {e}")


class SimulationManager:
    _instance: Optional["SimulationManager"] = None
    simulation_world: World = None
    logs_to_summarize :List[LogEntryModel]= []
    last_summarized_on: int = None
    agent_coordinator = Coordinator()
    current_log_summary: List[str] = []
    socket_conn: ConnectionManager = None
    config = get_config()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SimulationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.is_running = False
        self.socket_conn = ConnectionManager()
        self.current_simulation = None
        self.simulation_data: SimulationModal = None
        self.main_event_loop = None
        self.embedding_util = EmbeddingUtil()

    @classmethod
    def get_instance(cls) -> "SimulationManager":
        """Get or create the singleton instance"""
        if cls._instance is None:
            return cls()
        return cls._instance

    @classmethod
    def destroy_instance(cls) -> None:
        """Reset the singleton instance"""
        if cls._instance is not None:
            cls._instance.stop()
            cls._instance = None

    def start_simulation(self, network: WorldModal) -> bool:
        if self.is_running:
            return False

        try:
            self.is_running = True
            self.simulation_data = SimulationModal(
                world_id=network.pk,
                name=network.name,
                status=SimulationStatus.PENDING,
                start_time=datetime.now(),
                end_time=None,
                configuration=network,
                metrics=None,
            )
            self.save_simulation = save_simulation(self.simulation_data)
            try:
                self.main_event_loop = asyncio.get_running_loop()
                print(f"Captured main event loop: {self.main_event_loop}. Using Celery: {self.config.control_config.realtime_log_summary_use_celery}")
            except RuntimeError:
                print(
                    "CRITICAL WARNING: Could not get running loop when starting simulation. "
                    "Ensure start_simulation is called from an async context (e.g., await manager.start_simulation). "
                    "Event broadcasting will likely fail."
                )
                self.main_event_loop = None  # Ensure it's None if failed
            # Start the simulation process
            self._run_simulation(network)

            return self.simulation_data

        except Exception as e:
            self.emit_event(
                "simulation_error",
                {
                    "message": f"Error starting simulation: {str(e)}",
                    "traceback": traceback.format_exc(),
                },
            )
            raise

    def on_update(self, event: Event) -> None:
        self.emit_event("simulation_event", event)
        log_entry = add_log_entry(
            {
                "simulation_id": self.simulation_data.pk,
                "timestamp": datetime.now(),
                "level": event.log_level,
                "component": event.node.name,
                "entity_type": getattr(event.node, "type", None),
                "details": event.to_dict(),
            }
        )
        if event.event_type not in [SimulationEventType.TRANSMISSION_STARTED, SimulationEventType.DATA_SENT]:
            self.embedding_util.embed_and_store_log(log_entry)
        self.logs_to_summarize.append(log_entry)

    def _summarize_delta_logs(self) -> None:
        SUMMARIZE_EVERY_SECONDS = 2

        if (self.last_summarized_on is None or 
            time.time() - self.last_summarized_on >= SUMMARIZE_EVERY_SECONDS) and self.logs_to_summarize:
            
            logs_to_summarize = self.logs_to_summarize.copy()
            self.logs_to_summarize.clear()
            new_logs_str = [l.to_human_string() for l in logs_to_summarize]
            use_celery = self.config.control_config.realtime_log_summary_use_celery

            if use_celery:
                task = summarize_logs_task.delay(
                    simulation_id=self.simulation_data.pk,
                    previous_summary=self.current_log_summary,
                    new_logs=new_logs_str,
                    conversation_id=self.simulation_data.pk
                )
                def schedule_result_handler():
                    asyncio.create_task(self._handle_celery_result(task))
                self.main_event_loop.call_soon_threadsafe(schedule_result_handler)
            else:
                # Run in main process via thread pool so simulation thread is not blocked
                executor = _get_summary_executor()

                executor.submit(
                    _run_summarization_inprocess,
                    self.simulation_data.pk,
                    self.current_log_summary,
                    new_logs_str,
                    self.simulation_data.pk,
                    self.main_event_loop,
                    _handle_inprocess_result,
                    self,
                )
    
    async def _handle_celery_result(self, task):
        """Handle Celery task result asynchronously"""
        try:
            # Poll for result without blocking
            while not task.ready():
                await asyncio.sleep(0.1)
            
            summary_result = task.result
            self.last_summarized_on = time.time()
            
            if summary_result is not None:
                new_summary = summary_result['summary_text']
                if len(new_summary) == 1:
                    self.current_log_summary.append(new_summary[0])
                else:
                    self.current_log_summary = new_summary
                    
                summary_result['summary_text'] = self.current_log_summary
                self.emit_event("simulation_summary", summary_result)
                
        except Exception as e:
            print(f"Error handling Celery result: {e}")

    def _run_simulation(self, topology_data: WorldModal) -> None:
        """
        Run the actual simulation process
        This would be where your simulation logic lives
        """
        try:
            import time
            from threading import Thread

            def simulation_worker():
                try:
                    self.emit_event(
                        "simulation_started", {"time": datetime.now().timestamp()}
                    )

                    # Mark as running
                    self.simulation_data.status = SimulationStatus.RUNNING
                    update_simulation_status(
                        self.simulation_data.pk, SimulationStatus.RUNNING
                    )

                    self.simulation_world = simulate_from_json(
                        topology_data.model_dump(), self.on_update
                    )

                    while self.simulation_world.is_running:
                        time.sleep(2)
                        if self.config.control_config.enable_realtime_log_summary and self.config.control_config.enable_ai_feature:
                            try:
                                self._summarize_delta_logs()
                            except Exception as e:
                                print(f"Error summarizing delta logs: {e}")
                                traceback.print_exc()

                    self.emit_event(
                        "simulation_completed",
                        {"results": self.simulation_data["results"]},
                    )
                    self.simulation_data.status = SimulationStatus.COMPLETED
                    update_simulation_status(
                        self.simulation_data.pk, SimulationStatus.COMPLETED
                    )

                except Exception as e:
                    self._handle_error(e)
                    self.simulation_data.status = SimulationStatus.FAILED
                    update_simulation_status(
                        self.simulation_data.pk, SimulationStatus.FAILED
                    )

                finally:
                    # Reset run state if this wasn't from an external stop
                    if self.is_running:
                        self.is_running = False

            # Run simulation in background
            Thread(target=simulation_worker).start()

        except Exception as e:
            self._handle_error(e)

    def send_message_command(
        self, from_node_name: str, to_node_name: str, message: str, **kwargs
    ):
        from_node = to_node = None
        for network in self.simulation_world.networks:
            for node in network.nodes:
                if node.name == from_node_name:
                    from_node = node
                    continue
                if node.name == to_node_name:
                    to_node = node
                    continue

        if not (from_node and to_node):
            self.emit_event(
                "simulation_error", {"error": "Nodes not found for sending message"}
            )
            return


        from_node.send_data(message, to_node)

    def stop(self) -> None:
        """Stop the running simulation"""
        if not self.is_running:
            return

        self.is_running = False

        if self.current_simulation is not None:
            # Add logic to safely stop your simulation
            # self.current_simulation.stop()
            self.current_simulation = None

        self.simulation_data.status = SimulationStatus.COMPLETED
        update_simulation_status(self.simulation_data.pk, SimulationStatus.COMPLETED)
        self.simulation_world.stop()

    def get_status(self) -> Dict[str, Any]:
        """Get current simulation status"""
        return {
            "is_running": self.is_running,
            "progress": self.simulation_data.get("progress", 0),
            "status": self.simulation_data.get("status", "idle"),
            "results": self.simulation_data.get("results"),
            "error": self.simulation_data.get("error"),
        }

    def emit_event(self, event: str, data: Dict[str, Any]) -> None:
        """
        Emit event to connected clients via Socket using run_coroutine_threadsafe.
        This method is designed to be called safely FROM A WORKER THREAD.

        Args:
            event: Event name
            data: Event data
        """
        # Check if we have the connection manager and the main loop reference
        if not self.socket_conn:
            print(
                f"[{threading.current_thread().name}] Warning: Socket connection manager not available. Cannot emit '{event}'."
            )
            return
        if not self.main_event_loop or not self.main_event_loop.is_running():
            print(
                f"[{threading.current_thread().name}] Warning: Main event loop not available or not running. Cannot emit '{event}'."
            )
            return

        try:
            if hasattr(data, "to_dict"):
                data = data.to_dict()
        except Exception as e:
            print(
                f"[{threading.current_thread().name}] Error serializing data for event '{event}': {e}"
            )
            pprint(data)
            return

        coro_to_run = self.socket_conn.broadcast(dict(event=event, data=data))
        future = asyncio.run_coroutine_threadsafe(coro_to_run, self.main_event_loop)

    def _handle_error(self, error: Exception) -> None:
        """
        Handle simulation errors

        Args:
            error: The exception that occurred
        """
        error_info = {"message": str(error), "traceback": traceback.format_exc()}

        self.simulation_data.status = "error"
        self.is_running = False

        self.emit_event("simulation_error", error_info)

        raise error

    def _on_progress_update(self, progress: int, message: str) -> None:
        """
        Handle progress updates from the simulation

        Args:
            progress: Progress percentage (0-100)
            message: Progress message
        """
        self.simulation_data["progress"] = progress
        self.emit_event(
            "simulation_progress", {"progress": progress, "message": message}
        )
