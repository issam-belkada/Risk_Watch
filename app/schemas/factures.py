from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

from app.services import retards


class StatutFacture(str, Enum):
    a_echoir = "a_echoir"
    en_retard = "en_retard"
    payee = "payee"


class FactureBase(BaseModel):
    numero: str = Field(min_length=1, max_length=50)
    montant_ttc: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    date_emission: date
    date_echeance: date

    @model_validator(mode="after")
    def echeance_apres_emission(self):
        if self.date_echeance < self.date_emission:
            raise ValueError("L'échéance ne peut pas précéder la date d'émission")
        return self


class FactureCreate(FactureBase):
    client_id: int


class FactureUpdate(BaseModel):
    numero: str | None = Field(default=None, min_length=1, max_length=50)
    montant_ttc: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )
    date_emission: date | None = None
    date_echeance: date | None = None

    @field_validator("numero", "montant_ttc", "date_emission", "date_echeance")
    @classmethod
    def refuser_null(cls, v):
        if v is None:
            raise ValueError("Ce champ ne peut pas être vide")
        return v


class PaiementCreate(BaseModel):
    date_paiement: date

    @field_validator("date_paiement")
    @classmethod
    def pas_dans_le_futur(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("La date de paiement ne peut pas être dans le futur")
        return v


class FactureRead(FactureBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    date_paiement: date | None

    @computed_field
    @property
    def statut(self) -> StatutFacture:
        return StatutFacture(
            retards.statut_facture(self.date_echeance, self.date_paiement)
        )

    @computed_field
    @property
    def jours_de_retard(self) -> int:
        return retards.jours_de_retard(self.date_echeance, self.date_paiement)