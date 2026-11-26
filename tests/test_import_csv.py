from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.services.import_factures import ImportErreur, lire_csv

EN_TETE = "numero,siren_client,montant_ttc,date_emission,date_echeance,date_paiement\n"

CSV_OK = (
    EN_TETE
    + "F-001,732829320,1200.50,2026-01-10,2026-02-09,2026-03-01\n"
    + "F-002,732829320,800.00,2026-02-01,2026-03-03,\n"
    + "F-003,732 829 320,50.25,2026-03-01,2026-03-31,2026-03-20\n"
)


def test_lecture_ok():
    valides, erreurs, nb = lire_csv(CSV_OK.encode())

    assert erreurs == []
    assert nb == 3
    assert [ligne for ligne, _ in valides] == [2, 3, 4]
    premiere = valides[0][1]
    assert premiere.numero == "F-001"
    assert premiere.siren_client == "732829320"
    assert premiere.montant_ttc == Decimal("1200.50")
    assert premiere.date_paiement == date(2026, 3, 1)
    assert valides[1][1].date_paiement is None
    assert valides[2][1].siren_client == "732829320"


def test_format_francais_point_virgule_et_virgule_decimale():
    contenu = (
        "numero;siren_client;montant_ttc;date_emission;date_echeance;date_paiement\n"
        "F-001;732829320;1200,50;2026-01-10;2026-02-09;\n"
    )

    valides, erreurs, _ = lire_csv(contenu.encode())

    assert erreurs == []
    assert valides[0][1].montant_ttc == Decimal("1200.50")


def test_erreurs_signalees_par_ligne():
    contenu = (
        EN_TETE
        + "F-001,732829320,1200.50,2026-01-10,2026-02-09,\n"
        + "F-002,732829320,-5,2026-01-10,2026-02-09,\n"
        + "F-003,111111111,100.00,2026-01-10,2026-02-09,\n"
        + "F-004,732829320,100.00,2026-02-09,2026-01-10,\n"
    )

    valides, erreurs, nb = lire_csv(contenu.encode())

    assert nb == 4
    assert [ligne for ligne, _ in valides] == [2]
    assert [e["ligne"] for e in erreurs] == [3, 4, 5]
    assert erreurs[0]["message"].startswith("montant_ttc")
    assert erreurs[1]["message"].startswith("siren_client")
    assert erreurs[2]["message"].startswith("ligne")


def test_paiement_incoherent():
    demain = (date.today() + timedelta(days=1)).isoformat()
    contenu = (
        EN_TETE
        + "F-001,732829320,100.00,2026-02-01,2026-03-01,2026-01-15\n"
        + f"F-002,732829320,100.00,2026-02-01,2026-03-01,{demain}\n"
    )

    valides, erreurs, _ = lire_csv(contenu.encode())

    assert valides == []
    assert [e["ligne"] for e in erreurs] == [2, 3]


def test_colonnes_manquantes():
    contenu = (
        "numero,siren_client,date_emission,date_echeance\n"
        "F-001,732829320,2026-01-10,2026-02-09\n"
    )

    with pytest.raises(ImportErreur, match="montant_ttc"):
        lire_csv(contenu.encode())


def test_encodage_invalide():
    contenu = (EN_TETE + "F-é,732829320,100.00,2026-01-10,2026-02-09,\n").encode("latin-1")

    with pytest.raises(ImportErreur, match="UTF-8"):
        lire_csv(contenu)


def test_bom_lignes_vides_et_colonnes_en_plus():
    contenu = (
        "\ufeffnumero,siren_client,montant_ttc,date_emission,date_echeance,date_paiement,commentaire\n"
        "\n"
        "F-001,732829320,100.00,2026-01-10,2026-02-09,,test\n"
        ",,,,,,\n"
    )

    valides, erreurs, nb = lire_csv(contenu.encode("utf-8"))

    assert erreurs == []
    assert nb == 1
    assert len(valides) == 1


def test_trop_de_lignes(monkeypatch):
    monkeypatch.setattr("app.services.import_factures.MAX_LIGNES", 2)

    with pytest.raises(ImportErreur, match="Trop de lignes"):
        lire_csv(CSV_OK.encode())


def test_fichier_vide():
    with pytest.raises(ImportErreur, match="vide"):
        lire_csv(b"")