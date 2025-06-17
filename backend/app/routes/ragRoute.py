from fastapi import APIRouter
from app.services.ragServices import RAGService

# Create a new API router for RAG-related endpoints
rag_router = APIRouter()

# Endpoint to trigger RAG vector indexing process
@rag_router.get("/")
def rag_contents():
    rag = RAGService()   # Initialize the RAG service
    rag.retrie_text()    # Retrieve text to be indexed
    rag.save_document()  # Save the processed document/vectors
    return "RAG done"    # Return a simple confirmation message
