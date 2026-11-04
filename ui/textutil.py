"""ui/textutil.py - player-friendly result text (English)."""
WORD = {"miss": "MISS!", "hit": "HIT!", "sunk": "SHIP SUNK!"}


def word(res) -> str:
    if res.result == "sunk" and res.ship:
        return f"{res.ship.upper()} SUNK!"
    return WORD[res.result]
