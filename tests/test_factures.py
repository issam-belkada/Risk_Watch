from datetime import date, timedelta

import pytest

CLIENT = {
    "raison_sociale": "Hôtel du Parc",
    "secteur": "hotellerie_restauration",
    "tranche_effectif": "10-49",
}


def facture(client_id, numero="F-001", echeance_dans=-10, montant="1200.50"):
    echeance = date.today() + timedelta(days=echeance_dans)
    return {
        "client_id": client_id,
        "numero": numero,
        "montant_ttc": montant,
        "date_emission": (echeance - timedelta(days=30)).isoformat(),
        "date_echeance": echeance.isoformat(),
    }


@pytest.fixture
def headers(make_headers):
    return make_headers()


@pytest.fixture
def client_id(client, headers):
    return client.post("/clients", json=CLIENT, headers=headers).json()["id"]


def test_creer_facture_en_retard(client, headers, client_id):
    r = client.post("/factures", json=facture(client_id, echeance_dans=-10), headers=headers)

    assert r.status_code == 201
    data = r.json()
    assert data["client_id"] == client_id
    assert data["montant_ttc"] == "1200.50"
    assert data["date_paiement"] is None
    assert data["statut"] == "en_retard"
    assert data["jours_de_retard"] == 10


def test_creer_facture_a_echoir(client, headers, client_id):
    r = client.post("/factures", json=facture(client_id, echeance_dans=15), headers=headers)

    assert r.status_code == 201
    assert r.json()["statut"] == "a_echoir"
    assert r.json()["jours_de_retard"] == 0


@pytest.mark.parametrize("montant", ["0", "-5", "12.345"])
def test_creer_facture_montant_invalide(client, headers, client_id, montant):
    r = client.post("/factures", json=facture(client_id, montant=montant), headers=headers)

    assert r.status_code == 422


def test_creer_facture_echeance_avant_emission(client, headers, client_id):
    payload = facture(client_id)
    payload["date_echeance"] = (date.today() - timedelta(days=100)).isoformat()

    r = client.post("/factures", json=payload, headers=headers)

    assert r.status_code == 422


def test_creer_facture_numero_deja_utilise(client, headers, client_id):
    client.post("/factures", json=facture(client_id), headers=headers)

    r = client.post("/factures", json=facture(client_id), headers=headers)

    assert r.status_code == 409


def test_creer_facture_client_inexistant(client, headers):
    r = client.post("/factures", json=facture(9999), headers=headers)

    assert r.status_code == 404


def test_creer_facture_client_d_une_autre_organisation(client, make_headers):
    headers_a = make_headers("alice@atelier-dupont.fr", nom_organisation="Atelier Dupont")
    headers_b = make_headers("bruno@autre-entreprise.fr", nom_organisation="Autre Entreprise")
    cid = client.post("/clients", json=CLIENT, headers=headers_a).json()["id"]

    r = client.post("/factures", json=facture(cid), headers=headers_b)

    assert r.status_code == 404
    assert client.get("/factures", headers=headers_a).json() == []


def test_lecteur_ne_peut_pas_creer_de_facture(client, headers, client_id, se_connecter):
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

    r = client.post("/factures", json=facture(client_id), headers=headers_lecteur)

    assert r.status_code == 403


def test_lister_filtre_par_statut_et_tri(client, headers, client_id):
    client.post("/factures", json=facture(client_id, "F-RETARD", echeance_dans=-10), headers=headers)
    client.post("/factures", json=facture(client_id, "F-FUTUR", echeance_dans=15), headers=headers)
    client.post("/factures", json=facture(client_id, "F-TRES-RETARD", echeance_dans=-40), headers=headers)

    def numeros(url):
        return [f["numero"] for f in client.get(url, headers=headers).json()]

    assert numeros("/factures") == ["F-TRES-RETARD", "F-RETARD", "F-FUTUR"]
    assert numeros("/factures?statut=en_retard") == ["F-TRES-RETARD", "F-RETARD"]
    assert numeros("/factures?statut=a_echoir") == ["F-FUTUR"]
    assert numeros("/factures?statut=payee") == []


def test_lister_filtre_par_client(client, headers, client_id):
    autre = client.post(
        "/clients", json={**CLIENT, "raison_sociale": "Beta"}, headers=headers
    ).json()["id"]
    client.post("/factures", json=facture(client_id, "A-1"), headers=headers)
    client.post("/factures", json=facture(autre, "B-1"), headers=headers)

    r = client.get(f"/factures?client_id={autre}", headers=headers).json()

    assert [f["numero"] for f in r] == ["B-1"]


def test_isolation_des_factures(client, make_headers):
    headers_a = make_headers("alice@atelier-dupont.fr", nom_organisation="Atelier Dupont")
    headers_b = make_headers("bruno@autre-entreprise.fr", nom_organisation="Autre Entreprise")
    cid = client.post("/clients", json=CLIENT, headers=headers_a).json()["id"]
    client.post("/factures", json=facture(cid), headers=headers_a)

    assert client.get("/factures", headers=headers_b).json() == []
    assert len(client.get("/factures", headers=headers_a).json()) == 1


def test_factures_sans_token(client):
    assert client.get("/factures").status_code == 401
    assert client.post("/factures", json=facture(1)).status_code == 401


def jours(n):
    return (date.today() - timedelta(days=n)).isoformat()


def test_lire_facture(client, headers, client_id):
    fid = client.post("/factures", json=facture(client_id), headers=headers).json()["id"]

    r = client.get(f"/factures/{fid}", headers=headers)

    assert r.status_code == 200
    assert r.json()["numero"] == "F-001"


def test_lire_facture_introuvable_ou_d_une_autre_organisation(client, make_headers):
    headers_a = make_headers("alice@atelier-dupont.fr", nom_organisation="Atelier Dupont")
    headers_b = make_headers("bruno@autre-entreprise.fr", nom_organisation="Autre Entreprise")
    cid = client.post("/clients", json=CLIENT, headers=headers_a).json()["id"]
    fid = client.post("/factures", json=facture(cid), headers=headers_a).json()["id"]

    assert client.get("/factures/9999", headers=headers_a).status_code == 404
    assert client.get(f"/factures/{fid}", headers=headers_b).status_code == 404


def test_paiement_a_temps(client, headers, client_id):
    fid = client.post(
        "/factures", json=facture(client_id, echeance_dans=-10), headers=headers
    ).json()["id"]

    r = client.post(f"/factures/{fid}/paiement", json={"date_paiement": jours(15)}, headers=headers)

    assert r.status_code == 200
    assert r.json()["statut"] == "payee"
    assert r.json()["jours_de_retard"] == 0


def test_paiement_en_retard_de_30_jours(client, headers, client_id):
    fid = client.post(
        "/factures", json=facture(client_id, echeance_dans=-40), headers=headers
    ).json()["id"]

    r = client.post(f"/factures/{fid}/paiement", json={"date_paiement": jours(10)}, headers=headers)

    assert r.status_code == 200
    assert r.json()["statut"] == "payee"
    assert r.json()["jours_de_retard"] == 30


def test_paiement_deja_enregistre(client, headers, client_id):
    fid = client.post("/factures", json=facture(client_id), headers=headers).json()["id"]
    client.post(f"/factures/{fid}/paiement", json={"date_paiement": jours(5)}, headers=headers)

    r = client.post(f"/factures/{fid}/paiement", json={"date_paiement": jours(2)}, headers=headers)

    assert r.status_code == 409


def test_paiement_dans_le_futur(client, headers, client_id):
    fid = client.post("/factures", json=facture(client_id), headers=headers).json()["id"]
    demain = (date.today() + timedelta(days=1)).isoformat()

    r = client.post(f"/factures/{fid}/paiement", json={"date_paiement": demain}, headers=headers)

    assert r.status_code == 422


def test_paiement_avant_l_emission(client, headers, client_id):
    f = client.post("/factures", json=facture(client_id), headers=headers).json()
    avant = (date.fromisoformat(f["date_emission"]) - timedelta(days=1)).isoformat()

    r = client.post(f"/factures/{f['id']}/paiement", json={"date_paiement": avant}, headers=headers)

    assert r.status_code == 422


def test_filtre_payee_apres_paiement(client, headers, client_id):
    fid = client.post(
        "/factures", json=facture(client_id, "F-PAYEE", echeance_dans=-10), headers=headers
    ).json()["id"]
    client.post("/factures", json=facture(client_id, "F-IMPAYEE", echeance_dans=-10), headers=headers)
    client.post(f"/factures/{fid}/paiement", json={"date_paiement": jours(5)}, headers=headers)

    def numeros(url):
        return [f["numero"] for f in client.get(url, headers=headers).json()]

    assert numeros("/factures?statut=payee") == ["F-PAYEE"]
    assert numeros("/factures?statut=en_retard") == ["F-IMPAYEE"]


def test_lecteur_ne_peut_pas_enregistrer_un_paiement(client, headers, client_id, se_connecter):
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
    fid = client.post("/factures", json=facture(client_id), headers=headers).json()["id"]
    headers_lecteur = se_connecter("lea@atelier-dupont.fr")

    r = client.post(f"/factures/{fid}/paiement", json={"date_paiement": jours(5)}, headers=headers_lecteur)

    assert r.status_code == 403


def test_paiement_facture_d_une_autre_organisation(client, make_headers):
    headers_a = make_headers("alice@atelier-dupont.fr", nom_organisation="Atelier Dupont")
    headers_b = make_headers("bruno@autre-entreprise.fr", nom_organisation="Autre Entreprise")
    cid = client.post("/clients", json=CLIENT, headers=headers_a).json()["id"]
    fid = client.post("/factures", json=facture(cid), headers=headers_a).json()["id"]

    r = client.post(f"/factures/{fid}/paiement", json={"date_paiement": jours(5)}, headers=headers_b)

    assert r.status_code == 404
    assert client.get(f"/factures/{fid}", headers=headers_a).json()["statut"] == "en_retard"