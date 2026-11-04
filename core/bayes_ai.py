"""core/bayes_ai.py
Bayesian AI (kategori Uncertainty). Untuk setiap kapal yang masih hidup (panjang L), AI menghitung semua
penempatan yang TIDAK bertentangan dengan bukti:
  * tidak boleh menutupi sel meleset atau sel milik kapal yang sudah tenggelam;
  * penempatan yang menutupi k sel 'kena' yang belum dijelaskan diberi bobot BOOST**k (likelihood).
P(r,c) ~ jumlah bobot semua penempatan yang melewati (r,c). AI menembak sel dengan P tertinggi.
"""
import random

import numpy as np

from core.state import FLEET, N


class BayesAI:
    name = "Bayesian AI"
    BOOST = 30.0

    def __init__(self, rng=None, fleet=None):
        self.rng = rng or random.Random()
        self.fleet = dict(fleet or FLEET)
        self.reset()

    def reset(self):
        self.miss = np.zeros((N, N), bool)
        self.hit = np.zeros((N, N), bool)
        self.sunkcell = np.zeros((N, N), bool)
        self.remaining = sorted(self.fleet.values(), reverse=True)     # panjang kapal yang masih hidup

    def update(self, cell, res):
        r, c = cell
        if res.result == "miss":
            self.miss[r, c] = True
            return
        self.hit[r, c] = True
        if res.result == "sunk":
            for rr, cc in res.cells:
                self.sunkcell[rr, cc] = True
            self.remaining.remove(len(res.cells))

    # ------------------------------------------------------------ inferensi
    @property
    def open_hits(self):
        """Sel kena yang belum dijelaskan oleh kapal tenggelam."""
        return self.hit & ~self.sunkcell

    @property
    def mode(self) -> str:
        return "target" if self.open_hits.any() else "hunt"

    def probability(self):
        blocked = self.miss | self.sunkcell
        open_hits = self.open_hits
        prob = np.zeros((N, N))
        for L in set(self.remaining):
            mult = self.remaining.count(L)
            for c in range(N - L + 1):                            # penempatan horizontal
                ok = blocked[:, c:c + L].sum(1) == 0
                k = open_hits[:, c:c + L].sum(1)
                prob[:, c:c + L] += (np.where(ok, self.BOOST ** k, 0.0) * mult)[:, None]
            for r in range(N - L + 1):                            # penempatan vertikal
                ok = blocked[r:r + L, :].sum(0) == 0
                k = open_hits[r:r + L, :].sum(0)
                prob[r:r + L, :] += (np.where(ok, self.BOOST ** k, 0.0) * mult)[None, :]
        prob[self.miss | self.hit] = 0.0
        return prob

    def placements_through(self, cell):
        """(jumlah penempatan konsisten yang melewati sel, berapa yang menutupi sel kena terbuka)."""
        r0, c0 = cell
        blocked, open_hits = self.miss | self.sunkcell, self.open_hits
        total = covering = 0
        for L in self.remaining:
            segs = [[(r0, c) for c in range(s, s + L)] for s in range(max(0, c0 - L + 1), min(c0, N - L) + 1)]
            segs += [[(r, c0) for r in range(s, s + L)] for s in range(max(0, r0 - L + 1), min(r0, N - L) + 1)]
            for seg in segs:
                if not any(blocked[x] for x in seg):
                    total += 1
                    covering += any(open_hits[x] for x in seg)
        return total, covering

    def choose(self):
        prob = self.probability()
        if prob.max() <= 0:                                       # pengaman
            free = [(r, c) for r in range(N) for c in range(N) if not (self.miss[r, c] or self.hit[r, c])]
            return self.rng.choice(free)
        best = np.argwhere(prob >= prob.max() * (1 - 1e-9))
        r, c = best[self.rng.randrange(len(best))]
        return (int(r), int(c))
