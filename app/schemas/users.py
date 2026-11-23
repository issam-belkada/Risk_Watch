from pydantic import BaseModel, EmailStr, Field

from app.schemas.auth import Role


class UserCreate(BaseModel):
    email: EmailStr
    nom: str = Field(min_length=2, max_length=50)
    mot_de_passe: str = Field(min_length=8, max_length=128)
    role: Role = Role.lecteur