from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams
from qdrant_client.http.models import PointStruct
from haystack.nodes import PreProcessor
import uuid
import requests
from io import BytesIO
from PyPDF2 import PdfReader
from docx import Document

class VectorEmbedding:
    def __init__(self, path=None, device='cpu'):
        self.path = path
        self.device = device
        self.model_name = 'sentence-transformers/all-MiniLM-L6-v2'
        self.model = SentenceTransformer(self.model_name, device=self.device)
        self.chunk_size = 300
        self.overlap = 60
        self.search_limit = 3
        self.client = QdrantClient(url="http://localhost:6334")
        self.text = self.load_document() or ""

    def load_document(self):
        """Load and extract text from PDF file"""
        if self.path:
            try:
                response = requests.get(self.path['url'])
                response.raise_for_status()
                file_stream = BytesIO(response.content)
                file_ext = self.path['mime_type']

                print(file_ext)

                if 'pdf' in str(file_ext).lower():
                    reader = PdfReader(file_stream)
                    return "".join(page.extract_text() or "" for page in reader.pages)
                else:
                    doc = Document(file_stream)
                    return "\n".join(para.text for para in doc.paragraphs if para.text)
                
            except Exception as e:
                print(f"[load_document] Error: {e}")
                return None

    def chunk_text(self):
        """Split the loaded document text into overlapping chunks"""
        if not self.text:
            print("No text to chunk.")
            return []

        preprocessor = PreProcessor(
            split_length=self.chunk_size,
            split_overlap=self.overlap,
            split_respect_sentence_boundary=True
        )
        processed_docs = preprocessor.process([{"content": self.text}])
        return [doc.content for doc in processed_docs]
    
    def embed_chunks(self):
        """Generate embeddings for each text chunk and return point structures"""
        chunks = self.chunk_text()
        if not chunks:
            return []

        embeddings = self.model.encode(chunks, show_progress_bar=True)

        return [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={"text": chunk}
            ).dict()
            for chunk, embedding in zip(chunks, embeddings)
        ]

    def embed_text(self, text=None):
        """Generate embedding for entire text or a query"""
        input_text = text if text else self.text
        return self.model.encode(input_text).tolist()
    
    def save_vector(self, collection_name, points):
        """Create collection if not exists, then save vectors"""
        if not self.client.collection_exists(collection_name=collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=384,
                    distance="Cosine"
                ),
                timeout=120
            )
        self.client.upsert(collection_name=collection_name, points=points)
        
    
    def vector_search(self, collection_name, embedding):
        """Search the vector store for the most similar vectors"""
        try:
            return self.client.search(
                collection_name=collection_name,
                query_vector=embedding,
                limit=self.search_limit
            )
        except Exception as e:
            print(f"[vector_search] Error: {e}")
            return []

    def clear_collections(self):
        """Delete all collections in the Qdrant vector database."""
        try:
            collections = self.client.get_collections().collections

            for collection in collections:
                name = collection.name
                print(f"Deleting collection: {name}")
                self.client.delete_collection(collection_name=name)
            print("All collections cleared.")
        except Exception as e:
            print(f"[clear_collections] Error: {e}")