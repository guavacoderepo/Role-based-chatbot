from .vectors import VectorService
import glob
from typing import List, Dict
from app.schemas.schemes import Roles

class RAGService:
    def __init__(self, documents: List[Dict[str, List[str]]] = []):
        self.vector = VectorService()
        self.documents = documents

    def retrie_text(self) -> str:
        paths:List[str] = glob.glob('resources/data/*/*')
        for path in paths:
            text = self.vector.load_text(path)
            if not text:
                continue
            self.documents.append({
                "text": text,
                "source": path,
                "collection": path.split('/')[2]
            })
        return self.documents

    def save_document(self) -> None:
        for document in self.documents:
            chunks:list[str] = self.vector.chunk_text(document['text'])
            embeddings = self.vector.embed_chunks(chunks, document['source'])
            self.vector.save_vectors(document['collection'], embeddings)

    def retrive_vectors(self, prompt:str, collection:Roles) -> List:
        prompt_embedding = self.vector.embed_text(text=prompt)
        if collection.value == "executives":
            vectors = []
            for role in self.vector.get_collections():
                vectors.extend(self.vector.search(role.name, prompt_embedding))
            return sorted(vectors, key=lambda a: a['score'], reverse=True)
        else:
            return self.vector.search(collection.value, prompt_embedding)
    


    


