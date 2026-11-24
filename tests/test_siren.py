import pytest

from app.services.siren import siren_valide


def test_siren_valide():
    assert siren_valide("732829320")


@pytest.mark.parametrize(
    "siren",
    [
        "732829321",    # clé de contrôle fausse
        "12345",        # trop court
        "abcdefghi",    # pas des chiffres
        "",             # vide
        "7328293200",   # trop long
    ],
)
def test_siren_invalide(siren):
    assert not siren_valide(siren)