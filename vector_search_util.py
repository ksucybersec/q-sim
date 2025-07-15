import pprint
from dotenv import load_dotenv


if not load_dotenv():
    print("Error loading .env file")
    import sys
    sys.exit(-1)

from typing import Optional
from argparse import ArgumentParser

from data.embedding.vector_log import VectorLogEntry
from data.embedding.embedding_util import EmbeddingUtil


def get_relevant_logs(simulation_id: str, query: Optional[str] = '*', limit: int=100):
    print(f"Getting relevant logs for simulation {simulation_id} with query '{query}'")
    """Retrieve logs relevant to a question using vector similarity"""
    if query == "*":
        return VectorLogEntry.get_by_simulation(simulation_id)

    embedding_util = EmbeddingUtil()

    # Generate embedding for query
    query_embedding = embedding_util.generate_embedding(query)

    # Search for relevant logs
    return VectorLogEntry.search_similar(
        query_embedding, top_k=limit, filters={"simulation_id": simulation_id}
    )


if __name__ == '__main__':
    parser = ArgumentParser(description='Get relevant logs for a question')
    parser.add_argument('--simulation_id', type=str, required=True)
    parser.add_argument('--query', type=str, default="*")
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()
    relevant_logs = get_relevant_logs(args.simulation_id, args.query, args.limit)
    pprint.pprint(relevant_logs)