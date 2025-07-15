"""LangChain integration for network simulation logs"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from langchain.docstore.document import Document as LangchainDocument

from data.embedding.embedding_util import EmbeddingUtil
from data.embedding.vector_log import VectorLogEntry
from data.models.connection.redis import get_redis_conn
from data.models.simulation.log_model import get_logs_by_simulation


class OpenAIEmbeddings(Embeddings):
    """LangChain compatible wrapper for OpenAI embeddings"""

    def __init__(self):
        """Initialize the embedding utility"""
        self.embedding_util = EmbeddingUtil()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        return [self.embedding_util.generate_embedding(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Embed a query"""
        return self.embedding_util.generate_embedding(text)


class HuggingFaceEmbeddings(Embeddings):
    """LangChain compatible wrapper for HuggingFace embeddings"""

    def __init__(self):
        """Initialize the embedding utility"""
        self.embedding_util = EmbeddingUtil()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        return [self.embedding_util.generate_embedding(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Embed a query"""
        return self.embedding_util.generate_embedding(text)


class SimulationLogRetriever:
    """LangChain compatible retriever for simulation logs"""

    def __init__(self, embedding_provider: str = "openai"):
        """Initialize with redis and embedding provider"""
        self.redis_conn = get_redis_conn()
        self.embedding_provider = embedding_provider

        # Create the embeddings instance
        if embedding_provider == "openai":
            self.embeddings = OpenAIEmbeddings()
        elif embedding_provider == "huggingface":
            self.embeddings = HuggingFaceEmbeddings()
        else:
            raise ValueError(f"Unsupported embedding provider: {embedding_provider}")

        # Ensure vector index exists
        VectorLogEntry.create_index(self.redis_conn, True)

        # Initialize vector store
        # self.vector_store = RedisVectorStore(
        #     config=RedisConfig(
        #         redis_client=self.redis_conn,
        #         index_name="logs_vector_idx",
        #         key_prefix=f"simlog:vector:",
        #     ),
        #     embeddings=self.embeddings,
        # )

    def _log_to_document(self, log: Dict[str, Any]) -> LangchainDocument:
        """Convert a log entry to a LangChain Document"""
        # Format log content
        if isinstance(log.get("timestamp"), datetime):
            timestamp_str = log["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp_str = str(log.get("timestamp", ""))

        # Format content based on details field (JSON log)
        content = f"""
        Time: {timestamp_str}
        Level: {log.get('level', '')}
        Component: {log.get('component', '')}
        """

        if log.get("entity_type"):
            content += f"\nEntity Type: {log.get('entity_type')}"

        if log.get("entity_id"):
            content += f"\nEntity ID: {log.get('entity_id')}"

        # Process details field as the main content
        if log.get("details"):
            if isinstance(log["details"], dict):
                for k, v in log["details"].items():
                    content += f"\n{k}: {v}"
            else:
                content += f"\nDetails: {log['details']}"

        # Create metadata
        metadata = {
            "simulation_id": log.get("simulation_id", ""),
            "timestamp": timestamp_str,
            "level": log.get("level", ""),
            "component": log.get("component", ""),
            "entity_type": log.get("entity_type", ""),
            "entity_id": log.get("entity_id", ""),
            "pk": log.get("pk", ""),
        }

        return LangchainDocument(page_content=content, metadata=metadata)

    def index_simulation_logs(self, simulation_id: str, batch_size: int = 100) -> int:
        """Index all logs for a specific simulation into vector store"""
        # Get logs for the simulation
        logs = get_logs_by_simulation(simulation_id)

        # Convert logs to documents
        documents = [self._log_to_document(log.dict()) for log in logs]

        # Process in batches to avoid overwhelming the API
        total_indexed = 0
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            self.vector_store.add_documents(batch)
            total_indexed += len(batch)

        return total_indexed

    def search_logs_by_text(
        self, query_text: str, simulation_id: Optional[str] = None, top_k: int = 5
    ) -> List[LangchainDocument]:
        """Search logs by semantic similarity to the query text"""
        # Build filter if simulation_id provided
        filter_dict = {}
        if simulation_id:
            filter_dict["simulation_id"] = simulation_id

        # Execute similarity search
        return self.vector_store.similarity_search(
            query_text, k=top_k, filter=filter_dict
        )

    def search_logs_with_metadata_filter(
        self, query_text: str, filter_dict: Dict[str, str], top_k: int = 5
    ) -> List[LangchainDocument]:
        """Search logs with both text similarity and metadata filters"""
        return self.vector_store.similarity_search(
            query_text, k=top_k, filter=filter_dict
        )

    def get_logs_by_time_range(
        self, simulation_id: str, start_time: datetime, end_time: datetime = None
    ) -> List[LangchainDocument]:
        """Retrieve logs within a specific time range"""
        # Default end_time to now if not provided
        if end_time is None:
            end_time = datetime.now()

        # Format timestamps
        start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        # Query using metadata filters
        results = self.vector_store.similarity_search(
            "time range",  # This is just a placeholder, the filter is what matters
            k=100,  # Get a larger number to ensure we cover the time range
            filter={
                "simulation_id": simulation_id,
                "timestamp": {"$gte": start_str, "$lte": end_str},
            },
        )

        return results
