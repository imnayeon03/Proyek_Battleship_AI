"""core/actions.py
Aksi permainan: Shot (menembak satu sel) dan ShotResult (hasilnya).
Penerapan aksi:  hasil = Shot(sel).apply(board), hanya jika precondition terpenuhi
(sel di dalam papan, belum pernah ditembak, permainan belum selesai).
Pemain manusia, Bayesian AI, dan Random AI semuanya memakai Shot.apply() yang sama.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple

from core.state import HIT, MISS, N, SUNK, Cell, label


@dataclass(frozen=True)
class ShotResult:
    result: str                          # "miss" | "hit" | "sunk"
    ship: Optional[str] = None           # nama kapal (hanya diisi jika tenggelam)
    cells: Tuple[Cell, ...] = ()         # seluruh sel kapal yang tenggelam

    @property
    def is_hit(self) -> bool:
        return self.result in (HIT, SUNK)

    @property
    def is_sunk(self) -> bool:
        return self.result == SUNK


@dataclass(frozen=True)
class Shot:
    cell: Cell
    shooter: str = ""

    @property
    def name(self) -> str:
        r, c = self.cell
        return f"Tembak({label(self.cell)})" if 0 <= r < N and 0 <= c < N else f"Tembak{self.cell}"

    def missing_preconditions(self, board) -> List[str]:
        r, c = self.cell
        missing = []
        if not (0 <= r < N and 0 <= c < N):
            missing.append("sel berada di dalam papan")
        elif self.cell in board.shots:
            missing.append(f"sel {label(self.cell)} belum pernah ditembak")
        if board.all_sunk():
            missing.append("permainan belum selesai (masih ada kapal yang hidup)")
        return missing

    def is_applicable(self, board) -> bool:
        return not self.missing_preconditions(board)

    def apply(self, board) -> ShotResult:
        missing = self.missing_preconditions(board)
        if missing:
            raise ValueError(f"Aksi {self.name} tidak dapat dilakukan. Precondition belum terpenuhi: {missing}")
        return board.fire(self.cell)
