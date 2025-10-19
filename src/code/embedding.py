import os
import pathlib
import json
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

class EmbeddingUploader:
    def __init__(self, model_name, collection_name, cache_folder="./models"):
        self.model_name = model_name
        self.collection_name = collection_name
        self.sparse_model_name = "bm25"
        self.model = SentenceTransformer(self.model_name, trust_remote_code=True, cache_folder=cache_folder)
        self.emb_dimensions = self.model.get_sentence_embedding_dimension()
        self.meta = {}
        self.content = []

    def read_metadata(self, file_path: str):
        """
        Reads metadata from a file.
        If no metadata is present, empty dict is returned to properties.
        Returns meta_found: bool
        """
        meta_found = False
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()

        json_block = data.strip()
        print("Found metadata block in", file_path)
        try:
            self.meta = json.loads(json_block)
            meta_found = True
        except Exception as e:
            # invalid JSON: fall back to empty metadata
            print(f"Error parsing metadata JSON: {e}")
            self.meta = {}
        return meta_found


    def upload_embeddings(self, content_path, qdrant_url="http://localhost:6333"):
        client = QdrantClient(qdrant_url)
        if not client.collection_exists(self.collection_name):
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.emb_dimensions, # type: ignore
                    distance=models.Distance.COSINE
                )
            )

        config = client.get_collection(self.collection_name)

        # Validate collection config
        vectors = getattr(config.config.params, "vectors", None)
        if vectors is None:
            raise AssertionError(f"Collection '{self.collection_name}' missing vectors config")
        vec_keys = list(vectors.keys()) if hasattr(vectors, "keys") else list(vectors)
        assert [self.model_name] == vec_keys, f"Collection '{self.collection_name}' vector config does not match model '{self.model_name}'"
   

        data_content = json.loads(pathlib.Path(content_path).read_text())
        points = []
        root_chapter = ""
        title = self.meta.get('title', 'Unknown Manual')
        for index, chapter in enumerate(data_content):
            if chapter[0] == 1:
                root_chapter = chapter[1]
            point = models.PointStruct(
                id=index,
                vector=self.model.encode(chapter[-1]).tolist(),
                payload={
                    "content": chapter[-1],
                    "main_chapter": root_chapter,
                    "chapter": chapter[1],
                    "manual": title,
                    "page": chapter[2]
                }
            )
            points.append(point)
        client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        return len(points)

    def upload_hybrid_embeddings(self, content_path, qdrant_url="http://localhost:6333"):
        client = QdrantClient(qdrant_url)
        if client.collection_exists(self.collection_name):
            config = client.get_collection(self.collection_name)
        else:
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    self.model_name: models.VectorParams(
                        size=self.emb_dimensions, # type: ignore
                        distance=models.Distance.COSINE
                    ),
                },
                sparse_vectors_config={
                    self.sparse_model_name: models.SparseVectorParams(
                        modifier=models.Modifier.IDF,
                    )
                }
            )
            config = client.get_collection(self.collection_name)

        # Validate collection config
        vectors = getattr(config.config.params, "vectors", None)
        if vectors is None:
            raise AssertionError(f"Collection '{self.collection_name}' missing vectors config")
        vec_keys = list(vectors.keys()) if hasattr(vectors, "keys") else list(vectors)
        assert [self.model_name] == vec_keys, f"Collection '{self.collection_name}' vector config does not match model '{self.model_name}'"

        sparse = getattr(config.config.params, "sparse_vectors", None)
        if sparse is None:
            raise AssertionError(f"Collection '{self.collection_name}' missing sparse_vectors config")
        sparse_keys = list(sparse.keys()) if hasattr(sparse, "keys") else list(sparse)
        assert [self.sparse_model_name] == sparse_keys, f"Collection '{self.collection_name}' sparse vector config does not match model '{self.sparse_model_name}'"
        
        data_content = json.loads(pathlib.Path(content_path).read_text())
        points = []
        meta_path = content_path.replace("_chunked.json", "_meta.json")
        meta_found = self.read_metadata(meta_path)
        if meta_found:
            title = self.meta.get('title', 'Unknown Manual')
        else:
            title = 'Unknown Manual'
        print("Uploading hybrid embeddings for manual:", title)
        root_chapter = ""
        for index, chapter in enumerate(data_content):
            if chapter[0] == 1:
                root_chapter = chapter[1]
            point = models.PointStruct(
                id=index,
                vector={
                    self.model_name: self.model.encode(chapter[-1]).tolist(),
                    self.sparse_model_name: models.Document(
                        text=chapter[-1],
                        model="Qdrant/"+self.sparse_model_name,
                    ),
                },
                payload={
                    "content": chapter[-1],
                    "main_chapter": root_chapter,
                    "chapter": chapter[1],
                    "manual": title,
                    "page": chapter[2]
                }
            )
            points.append(point)
        print(f"Uploading {len(points)} points to collection '{self.collection_name}'...")
        client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        return len(points)