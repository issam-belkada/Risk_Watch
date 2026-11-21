from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Role(str, Enum):
    lecteur = "lecteur"
    analyste = "analyste"
    admin = "admin"


class InscriptionCreate(BaseModel):
    nom_organisation: str = Field(min_length=2, max_length=120)
    email: EmailStr
    nom: str = Field(min_length=2, max_length=50)
    mot_de_passe: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nom: str
    role: Role
    organisation_id: int


class Token(BaseModel):
    access_token: str
    token_type: str