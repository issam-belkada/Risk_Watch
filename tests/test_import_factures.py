import pytest

CLIENT = {
    "raison_sociale": "Hôtel du Parc",
    "siren": "732829320",
    "secteur": "hotellerie_restauration",
    "tranche_effectif": "10-49",
}

EN_TETE = "numero,siren_client,montant_ttc,date_emission,date_echeance,date_paiement\n"

CSV_OK = (
    EN_TETE
    + "F-001,732829320,1200.50,2026-01-10,2026-02-09,2026-03-01\n"
    + "F-002,732829320,800.00,2026-02-01,2026-03-03,\n"
    + "F-003,732 829 320,50.25,2026-03-01,2026-03-31,2026-03-20\n"
)


def envoyer(client, headers, contenu):
    if isinstance(contenu, str):
        contenu = contenu.encode("utf-8")
    return client.post(
        "/factures/import",
        files={"fichier": ("factures.csv", contenu, "text/csv")},
        headers=headers,
    )


@pytest.fixture
def headers(make_headers):
    return make_headers()


@pytest.fixture
def client_siren(client, headers):
    return client.post("/clients", json=CLIENT, headers=headers).json()["id"]


def test_import_ok(client, headers, client_siren):
    r = envoyer(client, headers, CSV_OK)

    assert r.status_code == 201
    assert r.json() == {"lignes_lues": 3, "factures_importees": 3, "erreurs": []}

    factures = client.get("/factures?limite=100", headers=headers).json()
    assert [f["numero"] for f in factures] == ["F-001", "F-002", "F-003"]
    assert [f["client_id"] for f in factures] == [client_siren] * 3
    assert factures[0]["statut"] == "payee"
    assert factures[0]["jours_de_retard"] == 20
    assert factures[1]["statut"] == "en_retard"
    assert factures[2]["jours_de_retard"] == 0


def test_import_format_francais(client, headers, client_siren):
    contenu = (
        "numero;siren_client;montant_ttc;date_emission;date_echeance;date_paiement\n"
        "F-001;732829320;1200,50;2026-01-10;2026-02-09;\n"
    )

    r = envoyer(client, headers, contenu)

    assert r.status_code == 201
    factures = client.get("/factures", headers=headers).json()
    assert factures[0]["montant_ttc"] == "1200.50"


def test_import_avec_erreurs_n_importe_rien(client, headers, client_siren):
    contenu = (
        EN_TETE
        + "F-001,732829320,1200.50,2026-01-10,2026-02-09,\n"
        + "F-002,732829320,-5,2026-01-10,2026-02-09,\n"
        + "F-003,552100554,100.00,2026-01-10,2026-02-09,\n"
        + "F-004,732829320,100.00,2026-02-09,2026-01-10,\n"
    )

    r = envoyer(client, headers, contenu)

    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["factures_importees"] == 0
    assert detail["lignes_lues"] == 4
    assert [e["ligne"] for e in detail["erreurs"]] == [3, 4, 5]
    assert client.get("/factures", headers=headers).json() == []


def test_import_colonnes_manquantes(client, headers, client_siren):
    contenu = "numero,siren_client,date_emission,date_echeance\nF-001,732829320,2026-01-10,2026-02-09\n"

    r = envoyer(client, headers, contenu)

    assert r.status_code == 422
    assert "montant_ttc" in r.json()["detail"]


def test_import_encodage_invalide(client, headers, client_siren):
    contenu = (EN_TETE + "F-é,732829320,100.00,2026-01-10,2026-02-09,\n").encode("latin-1")

    r = envoyer(client, headers, contenu)

    assert r.status_code == 422
    assert "UTF-8" in r.json()["detail"]


def test_import_doublon_dans_le_fichier(client, headers, client_siren):
    contenu = (
        EN_TETE
        + "F-001,732829320,100.00,2026-01-10,2026-02-09,\n"
        + "F-001,732829320,200.00,2026-01-10,2026-02-09,\n"
    )

    r = envoyer(client, headers, contenu)

    assert r.status_code == 422
    assert [e["ligne"] for e in r.json()["detail"]["erreurs"]] == [3]
    assert client.get("/factures", headers=headers).json() == []


def test_import_numero_deja_existant(client, headers, client_siren):
    client.post(
        "/factures",
        json={
            "client_id": client_siren,
            "numero": "F-001",
            "montant_ttc": "10.00",
            "date_emission": "2026-01-10",
            "date_echeance": "2026-02-09",
        },
        headers=headers,
    )
    contenu = EN_TETE + "F-001,732829320,100.00,2026-01-10,2026-02-09,\n"

    r = envoyer(client, headers, contenu)

    assert r.status_code == 422
    assert [e["ligne"] for e in r.json()["detail"]["erreurs"]] == [2]
    assert len(client.get("/factures", headers=headers).json()) == 1


def test_import_ne_voit_pas_les_clients_d_une_autre_organisation(client, make_headers):
    headers_a = make_headers("alice@atelier-dupont.fr", nom_organisation="Atelier Dupont")
    headers_b = make_headers("bruno@autre-entreprise.fr", nom_organisation="Autre Entreprise")
    client.post("/clients", json=CLIENT, headers=headers_a)

    r = envoyer(client, headers_b, CSV_OK)

    assert r.status_code == 422
    assert "aucun client" in r.json()["detail"]["erreurs"][0]["message"]
    assert client.get("/factures", headers=headers_a).json() == []


def test_lecteur_ne_peut_pas_importer(client, headers, client_siren, se_connecter):
    client.post(
        "/users",
        json={
            "email": "lea@atelier-dupont.fr",
            "nom": "Léa",
            "mot_de_passe": "motdepasse123",
            "role": "lecteur",
        },
        headers=headers,
    )
    headers_lecteur = se_connecter("lea@atelier-dupont.fr")

    r = envoyer(client, headers_lecteur, CSV_OK)

    assert r.status_code == 403
    assert client.get("/factures", headers=headers).json() == []


def test_import_sans_token(client):
    r = client.post(
        "/factures/import",
        files={"fichier": ("factures.csv", CSV_OK.encode(), "text/csv")},
    )

    assert r.status_code == 401


def test_import_fichier_trop_volumineux(client, headers, client_siren, monkeypatch):
    monkeypatch.setattr("app.routers.factures.TAILLE_MAX_IMPORT", 10)

    r = envoyer(client, headers, CSV_OK)

    assert r.status_code == 413