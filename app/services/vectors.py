from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams
from qdrant_client.http.models import PointStruct
from haystack.nodes import PreProcessor
import uuid
from typing import List

class VectorService:
    def __init__(self, device='cpu'):
        """
        Initialize the vector service:
        - Loads the sentence transformer model.
        - Sets up chunking parameters.
        - Connects to the Qdrant vector database.
        """
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device=device)
        self.chunk_size = 300  # Number of tokens per chunk
        self.overlap = 50      # Overlapping tokens between chunks
        self.search_limit = 5  # Top N similar results to retrieve
        self.client = QdrantClient(url="http://localhost:6334")

    def load_text(self, path: str) -> str:
        """
        Load raw text content from a file.
        Returns an empty string if file cannot be read.
        """
        try:
            with open(path, encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {path}: {e}")
            return ""

    def chunk_text(self, text: str) -> List[str]:
        """
        Chunk long documents into smaller, overlapping segments using Haystack's PreProcessor.
        """
        preprocessor = PreProcessor(
            split_length=self.chunk_size,
            split_overlap=self.overlap,
            split_respect_sentence_boundary=True
        )
        processed = preprocessor.process([{"content": text}])
        return [d.content for d in processed]
    
    def embed_text(self, text: str) -> List:
        """
        Embed a single piece of text and return a vector (list of floats).
        """
        return self.model.encode(text).tolist()

    def embed_chunks(self, chunks: list[str], source: str) -> list[dict]:
        """
        Embed a list of text chunks and return Qdrant-compatible vector payloads.
        Each chunk is associated with a UUID and metadata.
        """
        sources = [source] * len(chunks)
        vectors = self.model.encode(chunks, show_progress_bar=False)
        
        return [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=v.tolist(),
                payload={"text": c, "source": s}
            ).dict()
            for c, v, s in zip(chunks, vectors, sources)
        ]

    def save_vectors(self, collection: str, points: list[dict]) -> None:
        """
        Save embedded vectors to a specific Qdrant collection.
        If the collection doesn't exist, create it first.
        """
        if not self.client.collection_exists(collection_name=collection):
            self.client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(
                    size=384,           # Vector dimension for MiniLM
                    distance="Cosine"   # Similarity metric
                ),
                timeout=120
            )
        self.client.upsert(collection, points)

    def search(self, collection: str, query_vector: list[float]) -> list[dict]:
        """
        Search the collection for vectors most similar to the query vector.
        Returns top `search_limit` results.
        """
        try:
            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=self.search_limit
            )
            return [{
                "id": str(result.id),
                "score": result.score,
                "text": result.payload.get("text", ""),
                "source": result.payload.get("source", "")
            } for result in results]
        except Exception as e:
            print(f"[search] Error: {e}")
            return []

    def delete_all_collections(self) -> None:
        """
        Deletes all collections in Qdrant. Use with caution.
        """
        for c in self.client.get_collections().collections:
            self.client.delete_collection(c.name)

    def get_collections(self):
        """
        Return a list of all collections available in Qdrant.
        """
        return self.client.get_collections().collections
