from pydantic import BaseModel
from typing import Optional
from enum import Enum

class Roles(Enum):
    Engineering = "engineering"
    Employee = "general"
    Finance = "finance"
    Executives = "executives"
    Marketing = "marketing"
    HR = "hr"

class QueryRequest(BaseModel):
    role: Roles
    question: str


class User(BaseModel):
    username:str
    role: Roles


class Conversation(BaseModel):
    user: User
    prompt: str
    response: Optional[str]
    date: str


class ChatReqest(BaseModel):
    prompt:str


class chatResponse(BaseModel):
    response: str