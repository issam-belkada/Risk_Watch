def siren_valide(siren: str) -> bool:
    if not (siren.isdigit() and len(siren) == 9):
        return False

    total = 0
    for i, chiffre in enumerate(reversed(siren)):
        n = int(chiffre)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n

    return total % 10 == 0