from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(120))

    users: Mapped[list["User"]] = relationship(
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