BOB = {
    "email": "bob@atelier-dupont.fr",
    "nom": "Bob",
    "mot_de_passe": "motdepasse123",
    "role": "analyste",
}


def headers_de(client, email, mot_de_passe):
    r = client.post("/auth/login", data={"username": email, "password": mot_de_passe})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_lister_en_tant_qu_admin(client, make_headers):
    headers = make_headers()

    r = client.get("/users", headers=headers)

    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["email"] == "alice@atelier-dupont.fr"


def test_creer_utilisateur(client, make_headers):
    headers = make_headers()

    r = client.post("/users", json=BOB, headers=headers)

    assert r.status_code == 201
    assert r.json()["role"] == "analyste"
    moi = client.get("/auth/me", headers=headers).json()
    assert r.json()["organisation_id"] == moi["organisation_id"]
    assert len(client.get("/users", headers=headers).json()) == 2


def test_creer_utilisateur_email_deja_utilise(client, make_headers):
    headers = make_headers()
    client.post("/users", json=BOB, headers=headers)

    r = client.post("/users", json=BOB, headers=headers)

    assert r.status_code == 409


def test_creer_utilisateur_role_invalide(client, make_headers):
    headers = make_headers()

    r = client.post("/users", json={**BOB, "role": "superman"}, headers=headers)

    assert r.status_code == 422


def test_utilisateurs_sans_token(client):
    assert client.get("/users").status_code == 401
    assert client.post("/users", json=BOB).status_code == 401


def test_analyste_ne_peut_pas_gerer_les_utilisateurs(client, make_headers):
    headers_admin = make_headers()
    client.post("/users", json=BOB, headers=headers_admin)
    headers_bob = headers_de(client, BOB["email"], BOB["mot_de_passe"])

    assert client.get("/auth/me", headers=headers_bob).status_code == 200
    assert client.get("/users", headers=headers_bob).status_code == 403
    autre = {**BOB, "email": "autre@atelier-dupont.fr"}
    assert client.post("/users", json=autre, headers=headers_bob).status_code == 403


def test_isolation_entre_organisations(client, make_headers):
    headers_a = make_headers("alice@atelier-dupont.fr", nom_organisation="Atelier Dupont")
    client.post("/users", json=BOB, headers=headers_a)
    headers_b = make_headers("bruno@autre-entreprise.fr", nom_organisation="Autre Entreprise")

    me_a = client.get("/auth/me", headers=headers_a).json()
    me_b = client.get("/auth/me", headers=headers_b).json()
    assert me_a["organisation_id"] != me_b["organisation_id"]

    emails_b = [u["email"] for u in client.get("/users", headers=headers_b).json()]
    assert emails_b == ["bruno@autre-entreprise.fr"]

    emails_a = [u["email"] for u in client.get("/users", headers=headers_a).json()]
    assert sorted(emails_a) == ["alice@atelier-dupont.fr", "bob@atelier-dupont.fr"]