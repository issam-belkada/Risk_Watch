from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import Pagination, exiger_role, get_current_user, get_pagination
from app.models import Client, User
from app.schemas.clients import ClientCreate, ClientRead

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("", response_model=ClientRead, status_code=201)
def creer_client(
    data: ClientCreate,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_role("analyste", "admin")),
):
    if data.siren:
        existant = db.scalars(
            select(Client).where(
                Client.organisation_id == user.organisation_id,
                Client.siren == data.siren,
            )
        ).first()
        if existant:
            raise HTTPException(
                status_code=409, detail="Un client avec ce SIREN existe déjà"
            )

    client = Client(
        raison_sociale=data.raison_sociale,
        siren=data.siren,
        secteur=data.secteur.value,
        tranche_effectif=data.tranche_effectif.value,
        date_creation=data.date_creation,
        delai_paiement_jours=data.delai_paiement_jours,
        organisation_id=user.organisation_id,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=list[ClientRead])
def lister_clients(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    pagination: Pagination = Depends(get_pagination),
):
    requete = (
        select(Client)
        .where(Client.organisation_id == user.organisation_id)
        .order_by(Client.raison_sociale)
        .limit(pagination.limite)
        .offset(pagination.decalage)
    )
    return db.scalars(requete).all()