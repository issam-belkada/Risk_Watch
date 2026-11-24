CLIENT = {
    "raison_sociale": "Hôtel du Parc",
    "siren": "732 829 320",
    "secteur": "hotellerie_restauration",
    "tranche_effectif": "10-49",
    "delai_paiement_jours": 45,
}

SANS_SIREN = {k: v for k, v in CLIENT.items() if k != "siren"}


def test_creer_client(client, make_headers):
    headers = make_headers()

    r = client.post("/clients", json=CLIENT, headers=headers)

    assert r.status_code == 201
    data = r.json()
    assert data["siren"] == "732829320"
    assert data["delai_paiement_jours"] == 45
    moi = client.get("/auth/me", headers=headers).json()
    assert data["organisation_id"] == moi["organisation_id"]


def test_creer_client_siren_invalide(client, make_headers):
    headers = make_headers()

    r = client.post("/clients", json={**CLIENT, "siren": "123456789"}, headers=headers)

    assert r.status_code == 422


def test_creer_client_secteur_invalide(client, make_headers):
    headers = make_headers()

    r = client.post("/clients", json={**CLIENT, "secteur": "magie"}, headers=headers)

    assert r.status_code == 422


def test_creer_client_siren_deja_utilise(client, make_headers):
    headers = make_headers()
    client.post("/clients", json=CLIENT, headers=headers)

    r = client.post("/clients", json=CLIENT, headers=headers)

    assert r.status_code == 409


def test_plusieurs_clients_sans_siren(client, make_headers):
    headers = make_headers()

    for nom in ["Alpha", "Beta", "Gamma"]:
        r = client.post(
            "/clients", json={**SANS_SIREN, "raison_sociale": nom}, headers=headers
        )
        assert r.status_code == 201


def test_lecteur_peut_lister_mais_pas_creer(client, make_headers, se_connecter):
    headers_admin = make_headers()
    client.post(
        "/users",
        json={
            "email": "lea@atelier-dupont.fr",
            "nom": "Léa",
            "mot_de_passe": "motdepasse123",
            "role": "lecteur",
        },
        headers=headers_admin,
    )
    client.post("/clients", json=CLIENT, headers=headers_admin)
    headers_lecteur = se_connecter("lea@atelier-dupont.fr")

    liste = client.get("/clients", headers=headers_lecteur)
    assert liste.status_code == 200
    assert len(liste.json()) == 1

    creation = client.post("/clients", json=SANS_SIREN, headers=headers_lecteur)
    assert creation.status_code == 403


def test_pagination_et_tri(client, make_headers):
    headers = make_headers()
    for nom in ["Delta", "Alpha", "Charlie", "Bravo", "Echo"]:
        client.post(
            "/clients", json={**SANS_SIREN, "raison_sociale": nom}, headers=headers
        )

    def noms(url):
        return [c["raison_sociale"] for c in client.get(url, headers=headers).json()]

    assert noms("/clients?limite=2") == ["Alpha", "Bravo"]
    assert noms("/clients?limite=2&decalage=2") == ["Charlie", "Delta"]
    assert noms("/clients?limite=2&decalage=4") == ["Echo"]


def test_pagination_limite_invalide(client, make_headers):
    headers = make_headers()

    assert client.get("/clients?limite=0", headers=headers).status_code == 422
    assert client.get("/clients?limite=1000", headers=headers).status_code == 422


def test_clients_sans_token(client):
    assert client.get("/clients").status_code == 401
    assert client.post("/clients", json=CLIENT).status_code == 401


def test_isolation_des_clients(client, make_headers):
    headers_a = make_headers("alice@atelier-dupont.fr", nom_organisation="Atelier Dupont")
    headers_b = make_headers("bruno@autre-entreprise.fr", nom_organisation="Autre Entreprise")
    client.post("/clients", json=CLIENT, headers=headers_a)

    assert client.get("/clients", headers=headers_b).json() == []

    # Le même SIREN est permis dans une autre organisation
    r = client.post("/clients", json=CLIENT, headers=headers_b)
    assert r.status_code == 201
    assert len(client.get("/clients", headers=headers_a).json()) == 1