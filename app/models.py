from pydantic import BaseModel

class UserRegister(BaseModel):
    email: str
    password: str
    nom: str = None

class UserLogin(BaseModel):
    email: str
    password: str