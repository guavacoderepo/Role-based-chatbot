from .vectors import VectorService
import glob
from typing import List, Dict
from app.schemas.schemes import Roles

class RAGService:
    def __init__(self, documents: List[Dict[str, List[str]]] = []):
        """
        Initialize the RAGService with an optional list of documents.
        VectorService handles text loading, chunking, embedding, and vector storage.
        """
        self.vector = VectorService()
        self.documents = documents

    def retrie_text(self) -> str:
        """
        Loads text files from the 'resources/data/*/*' directory,
        appends their content with metadata (source path and collection),
        and stores them in self.documents.
        """
        paths: List[str] = glob.glob('resources/data/*/*')  # Get all files in nested folders
        for path in paths:
            text = self.vector.load_text(path)  # Load file content
            if not text:
                continue
            self.documents.append({
                "text": text,
                "source": path,
                "collection": path.split('/')[2]  # Extract collection name from path
            })
        return self.documents

    def save_document(self) -> None:
        """
        Processes each document by:
        - Chunking the text
        - Creating vector embeddings
        - Saving the vectors into their respective collections
        """
        for document in self.documents:
            chunks: list[str] = self.vector.chunk_text(document['text'])  # Split into smaller pieces
            embeddings = self.vector.embed_chunks(chunks, document['source'])  # Create embeddings
            self.vector.save_vectors(document['collection'], embeddings)  # Save to vector DB

    def retrive_vectors(self, prompt: str, collection: Roles) -> List:
        """
        Retrieves the most relevant vectors from the collection(s) for a given prompt:
        - Embeds the prompt
        - If the role is 'executives', search all collections
        - Otherwise, search only in the specified collection
        - Results are sorted by similarity score (highest first)
        """
        prompt_embedding = self.vector.embed_text(text=prompt)

        # Search across all roles if collection is 'executives'
        if collection.value == "executives":
            vectors = []
            for role in self.vector.get_collections():
                vectors.extend(self.vector.search(role.name, prompt_embedding))
            return sorted(vectors, key=lambda a: a['score'], reverse=True)
        else:
            return self.vector.search(collection.value, prompt_embedding)
