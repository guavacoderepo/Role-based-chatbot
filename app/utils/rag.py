import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.vector_embedding import VectorEmbedding
from db import execute_query

DOCUMENT_QUERY = """
    SELECT url, mime_type 
    FROM documents 
    WHERE id = %s
"""

CATEGORY_QUERY = """
    SELECT ct.title 
    FROM modules AS m
    JOIN courses AS c ON m.course_id = c.id
    JOIN categories AS ct ON c.category_id = ct.id
    WHERE m.id = %s
"""

class RAG:
    def __init__(self, documents_ids=None, module_id=None):
        self.documents_ids = documents_ids or []
        self.module_id = module_id
        self.documents = self.retrie_docments()
        self.category = self.get_category()

    def retrie_docments(self):
        documents = []
        if self.documents_ids:
            for doc in self.documents_ids:
                result = execute_query(DOCUMENT_QUERY, (doc,))[0]
                documents.append({'url': result['url'], 'mime_type': result['mime_type']})
        return documents

    def get_category(self):
        return execute_query(CATEGORY_QUERY, (self.module_id,))[0]['title']

    def save_document(self):
        for doc in self.documents:
            rag = VectorEmbedding(doc)
            rag.chunk_text()
            embeddings = rag.embed_chunks()
            rag.save_vector(self.get_category(), embeddings)
        print("✅ Embeddings saved!!")

    def retrive_vectors(self, prompt):
        rag = VectorEmbedding()
        prompt_embedding = rag.embed_text(text=prompt)
        return rag.vector_search(self.get_category(), prompt_embedding)
    
    def web_search_rag(self, prompt):
        pass


rag = RAG(module_id = 1)


vectors = rag.retrive_vectors('What are variables in python?')

print(vectors)
