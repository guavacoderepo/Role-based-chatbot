from typing import Dict
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.services.llm import LLMServices
from app.services.ragging import RAGService
from app.schemas.schemes import ChartReqest, User

app = FastAPI()
security = HTTPBasic()

# Dummy user database
users_db: Dict[str, Dict[str, str]] = {
    "Tony": {"password": "password123", "role": "engineering"},
    "Bruce": {"password": "securepass", "role": "marketing"},
    "Sam": {"password": "financepass", "role": "finance"},
    "Peter": {"password": "pete123", "role": "engineering"},
    "Sid": {"password": "sidpass123", "role": "marketing"},
    "Natasha": {"password": "hrpass123", "role": "hr"},
    "Evan": {"password": "evan1111", "role": "executives"}
}


# Authentication dependency
def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> User:
    username = credentials.username
    password = credentials.password
    user = users_db.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return User(username=username, role=user["role"])


# Login endpoint
@app.get("/login")
def login(user=Depends(authenticate)):
    return {"msg": "Login successful", "payload": user}

# Protected test endpoint
@app.get("/test")
def test(user=Depends(authenticate)):
    return {"message": f"Hello {user['username']}! You can now chat.", "role": user["role"]}

@app.get("/rag")
def rag_contents():
     rag =  RAGService()
     rag.retrie_text()
     rag.save_document()
     return "Rag done"
k = User(username="test", role="executives")


@app.get("/coll")
def get_coll():
     rag =  RAGService()
     v = rag.retrive_vectors("", k.role)
     return "Rag done"

@app.get("/history")
def retrieve_history(user:User=Depends(authenticate)):
    # Generate response
    llm = LLMServices(user = user)

    history = llm.retrive_conversations()
    return history

# Protected chat endpoint
@app.post("/chat")
async def query(request: ChartReqest, user:User=Depends(authenticate)):

    try:

        prompt = request.prompt

        # Retrieve relevant context
        rag = RAGService()
        vectors = rag.retrive_vectors(prompt, user.role)
        rag_context = "\n\n".join([v['text'] for v in vectors]) if vectors else ""

        source_path = vectors[0]['source']
        source_url = f"Source url: https://github.com/guavacoderepo/Role-based-chatbot/tree/main/{source_path}"

        rag_context = f"{rag_context}\n\n{source_url}"

        # Generate response
        llm = LLMServices(prompt = prompt, user = user)
        response_text = llm.gpt_conversation_prompt(rag_context=rag_context)

        # Save conversation history
        llm.update_conversation(prompt=prompt, response=response_text)

        return {
            "response": response_text,
            "source": source_url
        }

    except Exception as e:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
