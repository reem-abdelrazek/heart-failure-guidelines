from services.milvus_service import MilvusService

milvus_service = MilvusService()


class DBService:
    def query_milvus(self, query, top_k=5):
        """
        Query the Milvus database for similar embeddings.

        Args:
            query: The query text
            top_k: Number of results to return

        Returns:
            List of matches with text and scores
        """
        return milvus_service.search(query, top_k)
