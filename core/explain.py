"""core/explain.py
Penjelasan AI yang DIBANGKITKAN dari peta probabilitas dan bukti aktual (bukan kalimat statis).
"""
from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

from core.state import label


@dataclass
class Explanation:
    cell: tuple
    mode: str
    percent: float
    rank: int
    candidates: int
    placements: int
    covering: int
    top: List[Tuple[str, float]] = field(default_factory=list)
    why: List[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return label(self.cell)

    def lines(self) -> List[str]:
        return [f"Saran: {self.text} (probabilitas {self.percent:.1f}%, peringkat {self.rank} dari {self.candidates} sel)"] \
            + [f"- {w}" for w in self.why]


def explain_move(ai, cell=None) -> Explanation:
    """Jelaskan mengapa `cell` (default: sel terbaik menurut peta probabilitas) dipilih BayesAI."""
    prob = ai.probability()
    total = prob.sum()
    if total <= 0:
        raise ValueError("Tidak ada sel kandidat.")
    if cell is None:
        cell = tuple(int(x) for x in np.unravel_index(prob.argmax(), prob.shape))
    pct = float(prob[cell] / total * 100)
    cand = int((prob > 0).sum())
    rank = int((prob > prob[cell]).sum()) + 1
    order = np.argsort(-prob, axis=None)[:5]
    top = [(label((int(i // prob.shape[1]), int(i % prob.shape[1]))), float(prob.flat[i] / total * 100)) for i in order]
    n_place, n_cover = ai.placements_through(cell)
    n_open = int(ai.open_hits.sum())
    why = []
    if ai.mode == "target":
        why.append(f"Mode TARGET: ada {n_open} sel kena yang belum dijelaskan, penempatan yang menutupinya "
                   f"diberi bobot {ai.BOOST:.0f}^k sehingga tembakan difokuskan di sekitarnya.")
    else:
        why.append("Mode HUNT: belum ada sel kena aktif, AI memilih sel yang dilewati paling banyak "
                   "kemungkinan penempatan kapal.")
    why.append(f"{label(cell)} dilewati {n_place} penempatan kapal yang konsisten dengan bukti"
               + (f" ({n_cover} di antaranya menutupi sel kena)." if n_open else "."))
    why.append("Kapal yang masih hidup (panjang): " + ", ".join(map(str, ai.remaining)) + ".")
    return Explanation(cell, ai.mode, pct, rank, cand, n_place, n_cover, top, why)
