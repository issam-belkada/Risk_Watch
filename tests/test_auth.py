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