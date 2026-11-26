from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(120))

    users: Mapped[list["User"]] = relationship(
        back_populates="organisation", cascade="all, delete-orphan"
    )
    
    clients: Mapped[list["Client"]] = relationship(
        back_populates="organisation", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(
        ForeignKey("organisations.id"), index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nom: Mapped[str] = mapped_column(String(50))
    mot_de_passe_hache: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="lecteur")

    organisation: Mapped["Organisation"] = relationship(back_populates="users")


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("organisation_id", "siren"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(
        ForeignKey("organisations.id"), index=True
    )
    raison_sociale: Mapped[str] = mapped_column(String(200))
    siren: Mapped[str | None] = mapped_column(String(9))
    secteur: Mapped[str] = mapped_column(String(50))
    tranche_effectif: Mapped[str] = mapped_column(String(20))
    date_creation: Mapped[date | None]
    delai_paiement_jours: Mapped[int] = mapped_column(default=30)

    organisation: Mapped["Organisation"] = relationship(back_populates="clients")
    factures: Mapped[list["Facture"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )


class Facture(Base):
    __tablename__ = "factures"
    __table_args__ = (
        UniqueConstraint("client_id", "numero"),
        CheckConstraint("montant_ttc > 0", name="ck_factures_montant_positif"),
        CheckConstraint(
            "date_echeance >= date_emission",
            name="ck_factures_echeance_apres_emission",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    numero: Mapped[str] = mapped_column(String(50))
    montant_ttc: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    date_emission: Mapped[date]
    date_echeance: Mapped[date]
    date_paiement: Mapped[date | None]

    client: Mapped["Client"] = relationship(back_populates="factures")