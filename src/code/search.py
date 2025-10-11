from qdrant_client import QdrantClient, models
import toml
import json

class Search:
    def __init__(self, model, collection_name, model_name, history_storage, secrets_path):
        config = toml.load(secrets_path)
        qdrant_url = getattr(config["qdrant"], "QDRANT_URL", "http://localhost:6333")
        self.qd_client = QdrantClient(qdrant_url)
        self.model = model
        self.collection_name = collection_name
        self.model_name = model_name
        self.history_storage = history_storage

    def search(self, query, limit=5):
        results = self.qd_client.query_points(
            collection_name=self.collection_name,
            query=self.model.encode(query).tolist(),
            limit=limit,
            with_payload=True
        )
        return results.points

    def search_with_history(self, query, limit=5):
        results = self.qd_client.query_points(
            collection_name=self.collection_name,
            query=self.model.encode(query).tolist(),
            limit=limit,
            with_payload=True
        )
        record = {}
        record['query'] = query
        record['ground_truth_points'] = []
        record['limit'] = limit
        record['result_points_scores'] = [(point.id, point.score) for point in results.points]
        with open(self.history_storage, "a+") as f:
            f.write(json.dumps(record) + "\n")
        return results.points

    def rrf_search(self, query: str, limit: int = 5):
        results = self.qd_client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(
                    query=self.model.encode(query).tolist(),
                    using=self.model_name,
                    limit=(5 * limit),
                ),
                models.Prefetch(
                    query=models.Document(
                        text=query,
                        model="Qdrant/bm25",
                    ),
                    using="bm25",
                    limit=(5 * limit),
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            with_payload=True
        )
        return results.points
