from datetime import date

from app.services.retards import jours_de_retard, statut_facture

ECHEANCE = date(2026, 3, 31)


def test_a_echoir_avant_l_echeance():
    aujourdhui = date(2026, 3, 20)

    assert statut_facture(ECHEANCE, None, aujourdhui) == "a_echoir"
    assert jours_de_retard(ECHEANCE, None, aujourdhui) == 0


def test_le_jour_de_l_echeance_n_est_pas_un_retard():
    assert statut_facture(ECHEANCE, None, ECHEANCE) == "a_echoir"
    assert jours_de_retard(ECHEANCE, None, ECHEANCE) == 0


def test_en_retard_apres_l_echeance():
    aujourdhui = date(2026, 4, 10)

    assert statut_facture(ECHEANCE, None, aujourdhui) == "en_retard"
    assert jours_de_retard(ECHEANCE, None, aujourdhui) == 10


def test_payee_a_temps():
    paiement = date(2026, 3, 25)
    aujourdhui = date(2026, 5, 1)

    assert statut_facture(ECHEANCE, paiement, aujourdhui) == "payee"
    assert jours_de_retard(ECHEANCE, paiement, aujourdhui) == 0


def test_payee_en_retard_garde_son_retard_reel():
    paiement = date(2026, 5, 15)
    aujourdhui = date(2026, 6, 1)

    assert statut_facture(ECHEANCE, paiement, aujourdhui) == "payee"
    assert jours_de_retard(ECHEANCE, paiement, aujourdhui) == 45