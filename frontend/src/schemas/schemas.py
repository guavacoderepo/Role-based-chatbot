from pydantic import BaseModel
from enum import Enum


class Roles(Enum):
    Engineering = "engineering"
    Employee = "general"
    Finance = "finance"
    Executives = "executives"
    Marketing = "marketing"
    HR = "hr"

class User(BaseModel):
    id:int
    username:str
    role: Roles

class UserModel(BaseModel):
    status: bool
    user: User
    token: str = None