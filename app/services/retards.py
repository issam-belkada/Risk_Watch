from datetime import date


def jours_de_retard(
    date_echeance: date,
    date_paiement: date | None,
    aujourdhui: date | None = None,
) -> int:
    aujourdhui = aujourdhui or date.today()
    reference = date_paiement or aujourdhui
    return max(0, (reference - date_echeance).days)


def statut_facture(
    date_echeance: date,
    date_paiement: date | None,
    aujourdhui: date | None = None,
) -> str:
    aujourdhui = aujourdhui or date.today()
    if date_paiement is not None:
        return "payee"
    if aujourdhui > date_echeance:
        return "en_retard"
    return "a_echoir"