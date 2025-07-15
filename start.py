from dotenv import load_dotenv

if not load_dotenv():
    print("Error loading .env file")
    import sys
    sys.exit(-1)

import os
import traceback
from fastapi import FastAPI
from server.app import get_app
from fastapi.concurrency import asynccontextmanager

app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # try:
    #     # Set Langchain env variables
    #     config = load_config()
    #     if config.llm.langchain_tracing:
    #         os.environ["LANGSMITH_TRACING"] = 'true'
    #         os.environ['LANGCHAIN_TRACING_V2'] = 'true'
    #         os.environ["LANGSMITH_API_KEY"] = config.llm.langchain_api_key.get_secret_value()
    #         os.environ["LANGSMITH_ENDPOINT"] = config.llm.langsmith_endpoint
    #         os.environ["LANGCHAIN_PROJECT"] = config.llm.langchain_project_name
    #         os.environ['OPENAI_API_KEY'] = config.llm.api_key.get_secret_value()
    #         print("Lifespan: Langchain environment variables set.")
    #     else:
    #         logging.info("Lifespan: Langchain tracing is disabled.")
    #         os.environ["LANGCHAIN_TRACING_V2"] = "false"
    # except Exception as e:
    #     print(f"Lifespan ERROR: Failed to set Langchain environment variables: {e}")

    try:
        from data.models.connection.redis import get_redis_conn
        if get_redis_conn().ping():
            pass
        else:
            raise Exception("Failed to connect to Redis")

    except Exception as e:
        print(f"Lifespan ERROR: Failed to connect to Redis: {e}")

    try:
        from ai_agent.src.orchestration.coordinator import Coordinator
        # Initialize the Coordinate class
        await Coordinator().initialize_system()
    except Exception as e:
        traceback.print_exc()
        print(f"Lifespan ERROR: Failed to initialize Coordinate class: {e}")

    try:
        from data.embedding.vector_log import VectorLogEntry
        VectorLogEntry.create_index(get_redis_conn())
    except Exception as e:
        traceback.print_exc()
        print(f"Lifespan ERROR: Failed to create VectorLogEntry index: {e}")

    yield
    # Shutdown
    print("Lifespan: Disconnecting from Redis...")
    try:
        redis_conn = get_redis_conn()
        if redis_conn:
            redis_conn.close()
            print("Lifespan: Disconnected from Redis.")
        else:
            print("Lifespan: No Redis connection to close.")
    except Exception as e:
        print(f"Lifespan ERROR: Failed to disconnect from Redis: {e}")

app = get_app(lifespan=lifespan)

if __name__ == '__main__':
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5174"))
    reload_flag = os.getenv("DEBUG", "True").lower() in ["true", "1", "t"]
    
    import uvicorn
    uvicorn.run(
        "start:app",
        host=host,
        port=port,
        reload=reload_flag,
        access_log=True
    )