from dotenv import load_dotenv

if not load_dotenv():
    print("Error loading .env file")
    import sys
    sys.exit(-1)

from celery import Celery
from typing import List, Dict, Any, Optional
import asyncio
from ai_agent.src.agents.base.enums import AgentTaskType
from ai_agent.src.agents.log_summarization.structures import RealtimeLogSummaryInput
from ai_agent.src.consts.agent_type import AgentType
from ai_agent.src.orchestration.coordinator import Coordinator
from config.config import get_config

class MyCelery(Celery):

    def on_init(self):
        print("Initializing system...")
        asyncio.run(Coordinator().initialize_system())
        

redis_config = get_config().redis
redis_uri = f'redis://{redis_config.username}:{redis_config.password.get_secret_value()}@{redis_config.host}:{redis_config.port}/{redis_config.db}'
print(redis_uri)
# Configure Celery (adjust broker/backend as needed)
celery_app = MyCelery('simulation_tasks')
celery_app.conf.update(
    broker_url=redis_uri,
    result_backend=redis_uri,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    redis_max_connections=4
)
celery_app.conf.broker_transport_options = {'global_keyprefix': "qsim_celery:"}


@celery_app.task(bind=True)
def summarize_logs_task(self, simulation_id: str, previous_summary: List[str], 
                       new_logs: List[str], conversation_id: str):
    """Celery task to summarize logs in background"""
    try:
        # Create coordinator instance
        coordinator = Coordinator()
        
        agent_args = RealtimeLogSummaryInput(
            simulation_id=simulation_id,
            previous_summary=previous_summary,
            new_logs=new_logs,
            conversation_id=conversation_id,
            optional_instructions=None
        )
        
        # Run the async task synchronously in the worker
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                coordinator._run_agent_task(AgentType.LOG_SUMMARIZER, {
                    'task_id': AgentTaskType.REALTIME_LOG_SUMMARY,
                    'input_data': agent_args
                })
            )
            return result
        finally:
            loop.close()
            
    except Exception as e:
        # Celery will automatically retry on failure
        raise self.retry(exc=e, countdown=60, max_retries=3)