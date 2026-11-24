import jwt
from fastapi import Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    erreur = HTTPException(
        status_code=401,
        detail="Identifiants invalides ou token expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
    except jwt.InvalidTokenError:
        raise erreur

    user_id = payload.get("sub")
    if user_id is None:
        raise erreur

    user = db.get(User, int(user_id))
    if user is None:
        raise erreur

    return user


def exiger_role(*roles: str):
    def verifier(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Droits insuffisants")
        return user

    return verifier


@dataclass
class Pagination:
    limite: int
    decalage: int


def get_pagination(
    limite: int = Query(10, ge=1, le=100),
    decalage: int = Query(0, ge=0),
) -> Pagination:
    return Pagination(limite=limite, decalage=decalage)