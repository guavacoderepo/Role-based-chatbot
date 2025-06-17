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
        - Load the sentence transformer model for embeddings.
        - Set chunk size and overlap for text splitting.
        - Connect to Qdrant vector database.
        """
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device=device)
        self.chunk_size = 300  # Tokens per chunk
        self.overlap = 50      # Overlap tokens between chunks
        self.search_limit = 5  # Number of search results to return
        self.client = QdrantClient(url="http://localhost:6334")  # Qdrant client connection

    def load_text(self, path: str) -> str:
        """
        Read raw text from a file.
        Return empty string if file reading fails.
        """
        try:
            with open(path, encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {path}: {e}")
            return ""

    def chunk_text(self, text: str) -> List[str]:
        """
        Split long text into overlapping chunks using Haystack PreProcessor.
        Respects sentence boundaries for better coherence.
        """
        preprocessor = PreProcessor(
            split_length=self.chunk_size,
            split_overlap=self.overlap,
            split_respect_sentence_boundary=True
        )
        processed = preprocessor.process([{"content": text}])
        # Extract content from processed chunks
        return [d.content for d in processed]
    
    def embed_text(self, text: str) -> List:
        """
        Generate embedding vector for a single text string.
        """
        return self.model.encode(text).tolist()

    def embed_chunks(self, chunks: list[str], source: str) -> list[dict]:
        """
        Embed multiple text chunks and prepare them as Qdrant points.
        Each chunk gets a unique UUID and metadata including original text and source.
        """
        sources = [source] * len(chunks)  # Same source for all chunks
        vectors = self.model.encode(chunks, show_progress_bar=False)  # Batch encode

        # Create Qdrant point payloads with id, vector, and metadata
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
        Save vectors to a Qdrant collection.
        Creates the collection if it doesn't exist.
        """
        if not self.client.collection_exists(collection_name=collection):
            self.client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(
                    size=384,           # Embedding dimension of MiniLM
                    distance="Cosine"   # Similarity metric for search
                ),
                timeout=120
            )
        self.client.upsert(collection, points)  # Insert points

    def search(self, collection: str, query_vector: list[float]) -> list[dict]:
        """
        Search the vector collection for top matching vectors to the query.
        Returns a list of results with id, similarity score, text, and source.
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
        Delete all collections in the Qdrant database.
        Use with caution as this removes all data.
        """
        for c in self.client.get_collections().collections:
            self.client.delete_collection(c.name)

    def get_collections(self):
        """
        Get a list of all collections in the Qdrant database.
        """
        return self.client.get_collections().collections
