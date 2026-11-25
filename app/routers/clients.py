from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import Pagination, exiger_role, get_current_user, get_pagination
from app.models import Client, User
from app.schemas.clients import ClientCreate, ClientRead, ClientUpdate

router = APIRouter(prefix="/clients", tags=["Clients"])

def get_client_de_l_organisation(
    client_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Client:
    client = db.get(Client, client_id)
    if client is None or client.organisation_id != user.organisation_id:
        raise HTTPException(status_code=404, detail="Client introuvable")
    return client


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


@router.get("/{client_id}", response_model=ClientRead)
def lire_client(client: Client = Depends(get_client_de_l_organisation)):
    return client


@router.patch(
    "/{client_id}",
    response_model=ClientRead,
    dependencies=[Depends(exiger_role("analyste", "admin"))],
)
def modifier_client(
    data: ClientUpdate,
    client: Client = Depends(get_client_de_l_organisation),
    db: Session = Depends(get_db),
):
    changements = data.model_dump(exclude_unset=True)

    nouveau_siren = changements.get("siren")
    if nouveau_siren:
        doublon = db.scalars(
            select(Client).where(
                Client.organisation_id == client.organisation_id,
                Client.siren == nouveau_siren,
                Client.id != client.id,
            )
        ).first()
        if doublon:
            raise HTTPException(
                status_code=409, detail="Un client avec ce SIREN existe déjà"
            )

    for champ, valeur in changements.items():
        setattr(client, champ, valeur)

    db.commit()
    db.refresh(client)
    return client