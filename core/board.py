"""core/board.py
Satu armada + riwayat tembakan yang diterimanya (state dunia permainan).
"""
from typing import List

from core.actions import ShotResult
from core.state import HIT, MISS, N, SUNK, Cell, FleetLayout


class Board:
    def __init__(self, layout: FleetLayout):
        self.layout = {k: list(v) for k, v in layout.items()}
        self.owner = {cell: nm for nm, cells in self.layout.items() for cell in cells}
        self.hits = {nm: set() for nm in self.layout}
        self.shots = {}          # (r,c) -> "hit" | "miss"
        self.sunk: List[str] = []   # urutan kapal yang tenggelam

    def fire(self, cell: Cell) -> ShotResult:
        r, c = cell
        if not (0 <= r < N and 0 <= c < N):
            raise ValueError("Sel di luar papan.")
        if cell in self.shots:
            raise ValueError("Sel itu sudah pernah ditembak.")
        nm = self.owner.get(cell)
        if nm is None:
            self.shots[cell] = MISS
            return ShotResult(MISS)
        self.shots[cell] = HIT
        self.hits[nm].add(cell)
        if len(self.hits[nm]) == len(self.layout[nm]):
            self.sunk.append(nm)
            return ShotResult(SUNK, nm, tuple(self.layout[nm]))
        return ShotResult(HIT)                   # lawan TIDAK diberi tahu nama kapalnya

    def all_sunk(self) -> bool:
        return len(self.sunk) == len(self.layout)

    def alive(self) -> List[str]:
        return [nm for nm in self.layout if nm not in self.sunk]

    def count(self, kind: str) -> int:
        return sum(1 for v in self.shots.values() if v == kind)
