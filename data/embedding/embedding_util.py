"""Utilities for generating embeddings from log entries"""
import time
import importlib.util
from typing import List, Dict, Any, Optional, Union

from config.config import get_config
from core.enums import NodeType
from data.embedding.vector_log import VectorLogEntry
from data.models.simulation.log_model import LogEntryModel as LogEntry, LogLevel

class EmbeddingUtil:
    """Utility for generating and storing embeddings"""
    
    def __init__(self, embedding_provider: str = "openai"):
        """Initialize with specified embedding provider"""
        self.provider = embedding_provider
        self._embedding_model = None
        
        # Initialize the embedding model
        if embedding_provider == "openai":
            self._init_openai()
        elif embedding_provider == "huggingface":
            self._init_huggingface()
        else:
            raise ValueError(f"Unsupported embedding provider: {embedding_provider}")
    
    def _init_openai(self):
        """Initialize OpenAI embedding model"""
        try:
            import openai
            self._embedding_model = "openai"
            # Check if API key is set in environment
            import os
            config = get_config()
            if config.llm.api_key:
                # openai.api_key = config.llm.api_key.get_secret_value()
                # openai.base_url = config.llm.base_url
                self.client = openai.Client(
                    api_key=config.llm.api_key.get_secret_value(),
                    base_url=config.llm.base_url
                )
            if not os.getenv("OPENAI_API_KEY"):
                print("Warning: OPENAI_API_KEY not found in environment variables")
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
    
    def _init_huggingface(self):
        """Initialize HuggingFace embedding model"""
        try:
            import torch
            from sentence_transformers import SentenceTransformer
            
            # Load the model
            self._embedding_model = SentenceTransformer('all-mpnet-base-v2')
        except ImportError:
            raise ImportError("Required packages not installed. Install with: pip install torch sentence-transformers")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for the given text"""
        if self.provider == "openai":
            return self._generate_openai_embedding(text)
        elif self.provider == "huggingface":
            return self._generate_huggingface_embedding(text)
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")
    
    def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        import openai
        
        # Handle rate limiting with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.embeddings.create(
                    model="models/text-embedding-004",
                    input=text
                )
                return response.data[0].embedding
            except openai.RateLimitError:
                if attempt < max_retries - 1:
                    # Exponential backoff
                    time.sleep(2 ** attempt)
                else:
                    raise
    
    def _generate_huggingface_embedding(self, text: str) -> List[float]:
        """Generate embedding using HuggingFace model"""
        # Generate embeddings
        embedding = self._embedding_model.encode(text)
        return embedding.tolist()
    
    def format_log_for_embedding(self, log: Union[LogEntry, Dict[str, Any]]) -> str:
        """Format log entry as text for embedding"""
        if isinstance(log, LogEntry):
            # Extract fields from LogEntry
            level = log.level.value if hasattr(log.level, 'value') else log.level
            component = log.component
            entity_type = log.entity_type.value if log.entity_type and hasattr(log.entity_type, 'value') else log.entity_type
            entity_id = log.entity_id
            details = log.details
        else:
            # Extract fields from dictionary
            level = log.get('level')
            if isinstance(level, LogLevel):
                level = level.value
            component = log.get('component')
            entity_type = log.get('entity_type')
            if isinstance(entity_type, NodeType):
                entity_type = entity_type.value
            entity_id = log.get('entity_id')
            details = log.get('details', {})
        
        # Format as text
        text_parts = [
            f"Level: {level}",
            f"Component: {component}"
        ]
        
        if entity_type:
            text_parts.append(f"Entity Type: {entity_type}")
        
        if entity_id:
            text_parts.append(f"Entity ID: {entity_id}")
        
        # Process details - the main content of the log
        if details:
            if isinstance(details, dict):
                for k, v in details.items():
                    text_parts.append(f"{k}: {v}")
            else:
                text_parts.append(f"Details: {details}")
        
        return " | ".join(text_parts)
    
    def embed_and_store_log(self, log: Union[LogEntry, Dict[str, Any]]) -> str:
        """Generate embedding for log and store in Redis"""
        # Format log as text
        log_text = self.format_log_for_embedding(log)
        
        # Generate embedding
        embedding = self.generate_embedding(log_text)
        
        # Store in Redis
        return VectorLogEntry.store_log_with_embedding(log, embedding)
    
    def query_logs_by_text(self, 
                         query_text: str, 
                         top_k: int = 5,
                         filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query logs by semantic similarity to the given text"""
        # Generate embedding for query text
        query_embedding = self.generate_embedding(query_text)
        
        # Search for similar logs
        return VectorLogEntry.search_similar(query_embedding, top_k, filters)
    
    def batch_embed_logs(self, logs: List[Union[LogEntry, Dict[str, Any]]]) -> List[str]:
        """Batch embed and store multiple logs"""
        keys = []
        for log in logs:
            key = self.embed_and_store_log(log)
            keys.append(key)
        return keys