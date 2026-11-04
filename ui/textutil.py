"""ui/textutil.py - teks ramah pemain."""
WORD = {"miss": "MELESET", "hit": "KENA!", "sunk": "KAPAL TENGGELAM!"}


def word(res) -> str:
    if res.result == "sunk" and res.ship:
        return f"KAPAL {res.ship.upper()} TENGGELAM!"
    return WORD[res.result]
