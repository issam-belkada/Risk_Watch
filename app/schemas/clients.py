from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.siren import siren_valide


class Secteur(str, Enum):
    commerce = "commerce"
    industrie = "industrie"
    services = "services"
    construction = "construction"
    transport = "transport"
    hotellerie_restauration = "hotellerie_restauration"
    sante = "sante"
    autre = "autre"


class TrancheEffectif(str, Enum):
    micro = "0-9"
    petite = "10-49"
    moyenne = "50-249"
    grande = "250+"


def nettoyer_siren(v: str | None) -> str | None:
    if v is None:
        return v
    v = v.replace(" ", "")
    if not siren_valide(v):
        raise ValueError("SIREN invalide")
    return v


def verifier_date_creation(v: date | None) -> date | None:
    if v is not None and v > date.today():
        raise ValueError("La date de création ne peut pas être dans le futur")
    return v


class ClientBase(BaseModel):
    raison_sociale: str = Field(min_length=2, max_length=200)
    siren: str | None = None
    secteur: Secteur
    tranche_effectif: TrancheEffectif
    date_creation: date | None = None
    delai_paiement_jours: int = Field(default=30, ge=0, le=180)

    @field_validator("siren")
    @classmethod
    def valider_siren(cls, v: str | None) -> str | None:
        return nettoyer_siren(v)

    @field_validator("date_creation")
    @classmethod
    def valider_date_creation(cls, v: date | None) -> date | None:
        return verifier_date_creation(v)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    raison_sociale: str | None = Field(default=None, min_length=2, max_length=200)
    siren: str | None = None
    secteur: Secteur | None = None
    tranche_effectif: TrancheEffectif | None = None
    date_creation: date | None = None
    delai_paiement_jours: int | None = Field(default=None, ge=0, le=180)

    @field_validator("siren")
    @classmethod
    def valider_siren(cls, v: str | None) -> str | None:
        return nettoyer_siren(v)

    @field_validator("date_creation")
    @classmethod
    def valider_date_creation(cls, v: date | None) -> date | None:
        return verifier_date_creation(v)

    @field_validator(
        "raison_sociale", "secteur", "tranche_effectif", "delai_paiement_jours"
    )
    @classmethod
    def refuser_null(cls, v):
        if v is None:
            raise ValueError("Ce champ ne peut pas être vide")
        return v


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int