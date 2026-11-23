from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import exiger_role
from app.models import User
from app.schemas.auth import UserRead

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