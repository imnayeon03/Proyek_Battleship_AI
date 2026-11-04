"""core/state.py
Representasi STATE papan permainan Battleship dan fungsi koordinat.
Koordinat memakai notasi papan: E5 = kolom E, baris 5.
Internal disimpan sebagai (baris, kolom) berindeks 0.
"""
from typing import Dict, Iterable, List, Set, Tuple

N = 10
COLS = "ABCDEFGHIJ"
FLEET = {"Carrier": 5, "Battleship": 4, "Cruiser": 3, "Submarine": 3, "Destroyer": 2}

Cell = Tuple[int, int]
FleetLayout = Dict[str, List[Cell]]        # nama kapal -> daftar sel yang ditempati

# hasil sebuah tembakan (juga dipakai sebagai nilai riwayat tembakan di Board.shots)
MISS, HIT, SUNK = "miss", "hit", "sunk"


def label(cell: Cell) -> str:
    r, c = cell
    return f"{COLS[c]}{r + 1}"


def parse_cell(s: str) -> Cell:
    s = s.strip().upper().replace(" ", "")
    if len(s) < 2 or s[0] not in COLS:
        raise ValueError(f"Koordinat '{s}' tidak valid. Contoh yang benar: E5 (kolom A-J, baris 1-{N}).")
    try:
        r = int(s[1:]) - 1
    except ValueError:
        raise ValueError(f"Koordinat '{s}' tidak valid. Contoh yang benar: E5.")
    if not 0 <= r < N:
        raise ValueError(f"Baris harus antara 1 dan {N}.")
    return (r, COLS.index(s[0]))


def ship_cells(start: Cell, length: int, orient: str) -> List[Cell]:
    r, c = start
    return [(r, c + i) for i in range(length)] if orient == "H" else [(r + i, c) for i in range(length)]


def cells_ok(cells: Iterable[Cell], occupied: Set[Cell]) -> bool:
    cells = list(cells)
    return all(0 <= r < N and 0 <= c < N for r, c in cells) and not any(x in occupied for x in cells)


def orientation(cells: List[Cell]) -> str:
    return "H" if len(cells) == 1 or cells[0][0] == cells[1][0] else "V"


def all_cells() -> List[Cell]:
    return [(r, c) for r in range(N) for c in range(N)]


def format_shots(shots: Dict[Cell, str]) -> str:
    """Riwayat tembakan sebagai teks, mis. {A1:miss, E5:hit} (urut papan)."""
    return "{" + ", ".join(f"{label(c)}:{v}" for c, v in sorted(shots.items())) + "}"
