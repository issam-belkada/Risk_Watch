from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Organisation, User
from app.schemas.auth import InscriptionCreate, Token, UserRead
from app.security import creer_token, hasher_mot_de_passe, verifier_mot_de_passe

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


@router.post("/login", response_model=Token)
def connexion(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.scalars(select(User).where(User.email == form.username)).first()

    if user is None or not verifier_mot_de_passe(
        form.password, user.mot_de_passe_hache
    ):
        raise HTTPException(
            status_code=401,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(access_token=creer_token(user.id), token_type="bearer")


@router.get("/me", response_model=UserRead)
def moi(current_user: User = Depends(get_current_user)):
    return current_user