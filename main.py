from typing import Dict
from fastapi import FastAPI, HTTPException, Depends, status, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.services.llm import LLMServices
from app.services.ragging import RAGService
from app.schemas.schemes import ChatReqest, User, chatResponse
from app.utils.markdown_pdf import markdown_pdf
import re
import os

# Initialize FastAPI app and security for basic HTTP authentication
app = FastAPI()
security = HTTPBasic()

# In-memory user database with username, password, and role
users_db: Dict[str, Dict[str, str]] = {
    "Tony": {"password": "password123", "role": "engineering"},
    "Bruce": {"password": "securepass", "role": "marketing"},
    "Sam": {"password": "financepass", "role": "finance"},
    "Peter": {"password": "pete123", "role": "engineering"},
    "Sid": {"password": "sidpass123", "role": "marketing"},
    "Natasha": {"password": "hrpass123", "role": "hr"},
    "Evan": {"password": "evan1111", "role": "executives"}
}

# Dependency that authenticates users from `users_db`
def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> User:
    username = credentials.username
    password = credentials.password
    user = users_db.get(username)

    # Reject if credentials are invalid
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return User(username=username, role=user["role"])

# Endpoint to confirm valid login
@app.get("/login")
def login(user=Depends(authenticate)):
    return {"msg": "Login successful", "payload": user}

# Test endpoint to confirm role-based access
@app.get("/test")
def test(user=Depends(authenticate)):
    return {
        "message": f"Hello {user['username']}! You can now chat.",
        "role": user["role"]
    }

# Endpoint to trigger RAG vector indexing
@app.get("/rag")
def rag_contents():
    rag = RAGService()
    rag.retrie_text()      # Load and preprocess documents
    rag.save_document()    # Save as chunks in vector DB
    return "RAG done"

# Get a user's past chat history
@app.get("/history")
def retrieve_history(user: User = Depends(authenticate)):
    llm = LLMServices(user=user)
    history = llm.retrive_conversations()
    return history

# Main chat endpoint: handles both normal and export/download prompts
@app.post("/chat")
async def query(request: ChatReqest, user: User = Depends(authenticate)) -> chatResponse:
    try:
        prompt = request.prompt

        # Regex pattern to detect download/export-related keywords
        pattern = re.compile(
            r"\b(download|get|save|export|fetch|send|give me|copy|retrieve|dl|grab)\b",
            re.IGNORECASE
        )

        # If prompt suggests a download action, generate and return a PDF
        if re.search(pattern, prompt):
            llm = LLMServices(prompt=prompt, user=user)
            history = llm.retrive_conversations()
            return await download_pdf(history[-1]['response'])

        # Otherwise, run through the normal RAG + LLM workflow
        rag = RAGService()
        vectors = rag.retrive_vectors(prompt, user.role)

        # Combine RAG results as context and extract source path
        rag_context = "\n\n".join([v['text'] for v in vectors]) if vectors else ""
        source_path = vectors[0]['source'] if vectors else "no_source_found"
        source_url = f"[🔗 View source](https://github.com/guavacoderepo/Role-based-chatbot/tree/main/{source_path})"

        # Generate answer using LLM
        llm = LLMServices(prompt=prompt, user=user)
        response_text = llm.gpt_conversation_prompt(rag_context=rag_context, source_url=source_url)

        # If the response is from RAG context, append the source link
        if "That information is not available" not in response_text:
            response_text = f"{response_text}\n\n{source_url}"

        # Save this chat to conversation history
        llm.update_conversation(prompt=prompt, response=response_text)

        return {"response": response_text}

    except Exception as e:
        # Catch and report any errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Helper function to convert markdown to PDF and return as HTTP response
async def download_pdf(markdown_txt: str):
    pdf_path = markdown_pdf(markdown_txt)  # Convert to PDF
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    os.remove(pdf_path)  # Delete temp file after reading

    return Response(content=pdf_bytes, media_type="application/pdf")
