INSCRIPTION = {
    "nom_organisation": "Atelier Dupont",
    "email": "alice@atelier-dupont.fr",
    "nom": "Alice",
    "mot_de_passe": "motdepasse123",
}


def test_inscription_ok(client):
    r = client.post("/auth/register", json=INSCRIPTION)

    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "alice@atelier-dupont.fr"
    assert data["role"] == "admin"
    assert "mot_de_passe" not in data
    assert "mot_de_passe_hache" not in data


def test_inscription_email_deja_utilise(client):
    client.post("/auth/register", json=INSCRIPTION)

    r = client.post("/auth/register", json=INSCRIPTION)

    assert r.status_code == 409


def test_inscription_mot_de_passe_trop_court(client):
    r = client.post("/auth/register", json={**INSCRIPTION, "mot_de_passe": "court"})

    assert r.status_code == 422


def test_login_ok(client):
    client.post("/auth/register", json=INSCRIPTION)

    r = client.post(
        "/auth/login",
        data={"username": INSCRIPTION["email"], "password": INSCRIPTION["mot_de_passe"]},
    )

    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_mauvais_mot_de_passe(client):
    client.post("/auth/register", json=INSCRIPTION)

    r = client.post(
        "/auth/login",
        data={"username": INSCRIPTION["email"], "password": "mauvais"},
    )

    assert r.status_code == 401


def test_login_email_inconnu(client):
    r = client.post(
        "/auth/login",
        data={"username": "inconnu@exemple.fr", "password": "motdepasse123"},
    )

    assert r.status_code == 401


def test_me_sans_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_token_invalide(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer pas.un.vrai.token"})

    assert r.status_code == 401


def test_me_avec_token(client, make_headers):
    headers = make_headers()

    r = client.get("/auth/me", headers=headers)

    assert r.status_code == 200
    assert r.json()["email"] == "alice@atelier-dupont.fr"
    assert r.json()["role"] == "admin"