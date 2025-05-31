from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer

from configuration.config import EMBEDDING_MODEL, MILVUS_HOST, MILVUS_PORT, COLLECTION_NAME, METRIC_TYPE


class MilvusService:
    def __init__(self):
        """Initialize Milvus connection and load the embedding model."""
        # Connect to Milvus
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)

        # Initialize the embedding model
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)

        # Get collection
        self.collection = Collection(name=COLLECTION_NAME)

        # Load collection to memory
        self.collection.load()

    def search(self, query, top_k=5):
        """
        Search for similar embeddings in Milvus.

        Args:
            query: The query text to search for
            top_k: Number of top results to return

        Returns:
            List of matches with metadata
        """
        # Generate embedding for query
        query_embedding = self.embedder.encode(query).tolist()

        # Search in Milvus
        search_params = {"metric_type": METRIC_TYPE, "params": {
            "itopk_size": 16, "search_width": 16, "team_size": 8}}
        results = self.collection.search(
            data=[query_embedding], anns_field="embedding", param=search_params, limit=top_k, output_fields=["text"])

        # Format results
        matches = []
        if results and len(results) > 0:
            hits = results[0]  # Get hits from the first (and only) query
            for hit in hits:
                matches.append({"id": hit.id, "score": hit.score, "metadata": {
                               "text": hit.entity.get("text")}})

        return matches
