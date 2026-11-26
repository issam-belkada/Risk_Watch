from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import Pagination, exiger_role, get_current_user, get_pagination
from app.models import Client, Facture, User
from app.schemas.factures import (
    FactureCreate,
    FactureRead,
    FactureUpdate,
    PaiementCreate,
    StatutFacture,
)
router = APIRouter(prefix="/factures", tags=["Factures"])


def get_facture_de_l_organisation(
    facture_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Facture:
    facture = db.get(Facture, facture_id)
    if facture is None or facture.client.organisation_id != user.organisation_id:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    return facture


@router.post("", response_model=FactureRead, status_code=201)
def creer_facture(
    data: FactureCreate,
    db: Session = Depends(get_db),
    user: User = Depends(exiger_role("analyste", "admin")),
):
    client = db.get(Client, data.client_id)
    if client is None or client.organisation_id != user.organisation_id:
        raise HTTPException(status_code=404, detail="Client introuvable")

    doublon = db.scalars(
        select(Facture).where(
            Facture.client_id == client.id, Facture.numero == data.numero
        )
    ).first()
    if doublon:
        raise HTTPException(
            status_code=409, detail="Ce numéro de facture existe déjà pour ce client"
        )

    facture = Facture(**data.model_dump())
    db.add(facture)
    db.commit()
    db.refresh(facture)
    return facture


@router.get("", response_model=list[FactureRead])
def lister_factures(
    client_id: int | None = None,
    statut: StatutFacture | None = None,
    echeance_min: date | None = None,
    echeance_max: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    pagination: Pagination = Depends(get_pagination),
):
    aujourdhui = date.today()

    requete = (
        select(Facture)
        .join(Client, Facture.client_id == Client.id)
        .where(Client.organisation_id == user.organisation_id)
    )

    if client_id is not None:
        requete = requete.where(Facture.client_id == client_id)

    if statut == StatutFacture.payee:
        requete = requete.where(Facture.date_paiement.is_not(None))
    elif statut == StatutFacture.en_retard:
        requete = requete.where(
            Facture.date_paiement.is_(None), Facture.date_echeance < aujourdhui
        )
    elif statut == StatutFacture.a_echoir:
        requete = requete.where(
            Facture.date_paiement.is_(None), Facture.date_echeance >= aujourdhui
        )

    if echeance_min is not None:
        requete = requete.where(Facture.date_echeance >= echeance_min)
    if echeance_max is not None:
        requete = requete.where(Facture.date_echeance <= echeance_max)

    requete = (
        requete.order_by(Facture.date_echeance, Facture.id)
        .limit(pagination.limite)
        .offset(pagination.decalage)
    )
    return db.scalars(requete).all()


@router.get("/{facture_id}", response_model=FactureRead)
def lire_facture(facture: Facture = Depends(get_facture_de_l_organisation)):
    return facture


@router.post(
    "/{facture_id}/paiement",
    response_model=FactureRead,
    dependencies=[Depends(exiger_role("analyste", "admin"))],
)
def enregistrer_paiement(
    data: PaiementCreate,
    facture: Facture = Depends(get_facture_de_l_organisation),
    db: Session = Depends(get_db),
):
    if facture.date_paiement is not None:
        raise HTTPException(status_code=409, detail="Cette facture est déjà payée")
    if data.date_paiement < facture.date_emission:
        raise HTTPException(
            status_code=422,
            detail="La date de paiement ne peut pas précéder la date d'émission",
        )

    facture.date_paiement = data.date_paiement
    db.commit()
    db.refresh(facture)
    return facture


@router.patch(
    "/{facture_id}",
    response_model=FactureRead,
    dependencies=[Depends(exiger_role("analyste", "admin"))],
)
def modifier_facture(
    data: FactureUpdate,
    facture: Facture = Depends(get_facture_de_l_organisation),
    db: Session = Depends(get_db),
):
    if facture.date_paiement is not None:
        raise HTTPException(
            status_code=409, detail="Une facture payée ne peut plus être modifiée"
        )

    changements = data.model_dump(exclude_unset=True)

    emission = changements.get("date_emission", facture.date_emission)
    echeance = changements.get("date_echeance", facture.date_echeance)
    if echeance < emission:
        raise HTTPException(
            status_code=422,
            detail="L'échéance ne peut pas précéder la date d'émission",
        )

    nouveau_numero = changements.get("numero")
    if nouveau_numero and nouveau_numero != facture.numero:
        doublon = db.scalars(
            select(Facture).where(
                Facture.client_id == facture.client_id,
                Facture.numero == nouveau_numero,
                Facture.id != facture.id,
            )
        ).first()
        if doublon:
            raise HTTPException(
                status_code=409,
                detail="Ce numéro de facture existe déjà pour ce client",
            )

    for champ, valeur in changements.items():
        setattr(facture, champ, valeur)

    db.commit()
    db.refresh(facture)
    return facture


@router.delete(
    "/{facture_id}",
    status_code=204,
    dependencies=[Depends(exiger_role("admin"))],
)
def supprimer_facture(
    facture: Facture = Depends(get_facture_de_l_organisation),
    db: Session = Depends(get_db),
):
    if facture.date_paiement is not None:
        raise HTTPException(
            status_code=409, detail="Une facture payée ne peut pas être supprimée"
        )
    db.delete(facture)
    db.commit()