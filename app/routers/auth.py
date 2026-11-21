from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Organisation, User
from app.schemas.auth import InscriptionCreate, UserRead
from app.security import hasher_mot_de_passe

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/register", response_model=UserRead, status_code=201)
def inscription(data: InscriptionCreate, db: Session = Depends(get_db)):
    existant = db.scalars(select(User).where(User.email == data.email)).first()
    if existant:
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé")

    organisation = Organisation(nom=data.nom_organisation)
    user = User(
        email=data.email,
        nom=data.nom,
        mot_de_passe_hache=hasher_mot_de_passe(data.mot_de_passe),
        role="admin",
        organisation=organisation,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user