"""bukti_ai.py - BUKTI bahwa Bayesian AI benar-benar MENGINFERENSI (bukan tembakan yang di-hardcode).
Semua angka berasal dari eksekusi nyata.  Jalankan:  python bukti_ai.py"""
import random

from core.actions import ShotResult
from core.ai_service import make_ai, play_solo, validate_game
from core.bayes_ai import BayesAI
from core.board import Board
from core.fleet_loader import load_dataset, random_layout
from core.state import label


def bukti_berbeda():
    print("=== 1. Bukti berbeda -> tembakan berbeda (probabilitas dihitung ulang) ===")
    ai = BayesAI(random.Random(1))
    print(f"  papan kosong          : mode {ai.mode:<6} tembak {label(ai.choose())}")
    ai.update((4, 4), ShotResult("miss"))
    print(f"  E5 meleset            : mode {ai.mode:<6} tembak {label(ai.choose())}")
    ai.update((0, 0), ShotResult("hit"))
    c = ai.choose()
    print(f"  A1 kena               : mode {ai.mode:<6} tembak {label(c)}  (tetangga A1: {abs(c[0]) + abs(c[1]) == 1})")
    ai.update((0, 1), ShotResult("sunk", "Destroyer", ((0, 0), (0, 1))))
    print(f"  Destroyer (A1-B1) tenggelam: mode {ai.mode:<6} sisa kapal {ai.remaining}")


def invarian(n=300, seed=7):
    print(f"\n=== 2. {n} armada acak: invarian inferensi ===")
    rng = random.Random(seed)
    ok_truth = ok_valid = bayes_menang = 0
    tot_b = tot_r = 0
    for i in range(n):
        lay = random_layout(rng)
        b, ai, benar = Board(lay), BayesAI(random.Random(i)), True
        while not b.all_sunk():
            c = ai.choose(); ai.update(c, b.fire(c))
            if b.all_sunk():
                break
            p = ai.probability()
            for nm, cells in lay.items():
                if nm not in b.sunk and any(p[x] <= 0 for x in cells if x not in b.shots):
                    benar = False
        ok_truth += benar
        rb, rr = play_solo(lay, make_ai("Bayes", i)), play_solo(lay, make_ai("Random", i))
        ok_valid += validate_game(lay, rb.history) and validate_game(lay, rr.history)
        bayes_menang += rb.shots < rr.shots
        tot_b += rb.shots; tot_r += rr.shots
    print(f"  posisi kapal sebenarnya tidak pernah dikesampingkan : {ok_truth}/{n}")
    print(f"  riwayat tembakan valid (diputar ulang)              : {ok_valid}/{n}")
    print(f"  Bayes lebih sedikit tembakan dari Random            : {bayes_menang}/{n}")
    print(f"  rata-rata tembakan  Bayes {tot_b / n:.1f}  vs  Random {tot_r / n:.1f}")


def armada_berbeda():
    print("\n=== 3. Armada berbeda -> jalannya permainan berbeda (AI yang sama) ===")
    for lid, lay in list(load_dataset().items())[:5]:
        r = play_solo(lay, make_ai("Bayes", 1))
        print(f"  susunan #{lid}: {r.shots} tembakan, 6 pertama: " + " ".join(label(e['cell']) for e in r.history[:6]))


if __name__ == "__main__":
    bukti_berbeda(); invarian(); armada_berbeda()
