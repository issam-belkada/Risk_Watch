from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import exiger_role
from app.models import User
from app.schemas.auth import UserRead
from app.schemas.users import UserCreate
from app.security import hasher_mot_de_passe

router = APIRouter(prefix="/users", tags=["Utilisateurs"])


@router.get("", response_model=list[UserRead])
def lister_utilisateurs(
    db: Session = Depends(get_db),
    admin: User = Depends(exiger_role("admin")),
):
    requete = (
        select(User)
        .where(User.organisation_id == admin.organisation_id)
        .order_by(User.id)
    )
    return db.scalars(requete).all()


@router.post("", response_model=UserRead, status_code=201)
def creer_utilisateur(
    data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(exiger_role("admin")),
):
    existant = db.scalars(select(User).where(User.email == data.email)).first()
    if existant:
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé")

    user = User(
        email=data.email,
        nom=data.nom,
        mot_de_passe_hache=hasher_mot_de_passe(data.mot_de_passe),
        role=data.role.value,
        organisation_id=admin.organisation_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user