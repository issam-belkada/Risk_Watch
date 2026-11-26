import csv
import io

from pydantic import ValidationError

from app.schemas.factures import FactureImport

COLONNES_OBLIGATOIRES = {
    "numero",
    "siren_client",
    "montant_ttc",
    "date_emission",
    "date_echeance",
}
MAX_LIGNES = 5000


class ImportErreur(Exception):
    """Le fichier est inexploitable dans son ensemble."""


def lire_csv(
    contenu: bytes,
) -> tuple[list[tuple[int, FactureImport]], list[dict], int]:
    try:
        texte = contenu.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ImportErreur("Le fichier doit être encodé en UTF-8")

    lignes = texte.splitlines()
    if not lignes:
        raise ImportErreur("Le fichier est vide")

    delimiteur = ";" if ";" in lignes[0] else ","
    lecteur = csv.DictReader(io.StringIO(texte), delimiter=delimiteur)

    colonnes = {c.strip() for c in (lecteur.fieldnames or [])}
    manquantes = COLONNES_OBLIGATOIRES - colonnes
    if manquantes:
        raise ImportErreur("Colonnes manquantes : " + ", ".join(sorted(manquantes)))

    valides: list[tuple[int, FactureImport]] = []
    erreurs: list[dict] = []
    nb_lignes = 0

    for brut in lecteur:
        numero_ligne = lecteur.line_num
        donnees = {
            k.strip(): v.strip()
            for k, v in brut.items()
            if k is not None and v is not None and v.strip() != ""
        }
        if not donnees:
            continue

        nb_lignes += 1
        if nb_lignes > MAX_LIGNES:
            raise ImportErreur(f"Trop de lignes (maximum {MAX_LIGNES})")

        if delimiteur == ";" and "montant_ttc" in donnees:
            donnees["montant_ttc"] = donnees["montant_ttc"].replace(",", ".")

        try:
            valides.append((numero_ligne, FactureImport(**donnees)))
        except ValidationError as e:
            for err in e.errors():
                champ = ".".join(str(x) for x in err["loc"]) or "ligne"
                erreurs.append(
                    {"ligne": numero_ligne, "message": f"{champ} : {err['msg']}"}
                )

    return valides, erreurs, nb_lignes