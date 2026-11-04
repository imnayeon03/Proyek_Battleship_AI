"""run_demo.py - demo Bayesian AI di terminal (tanpa Pygame).
Pemakaian:  python run_demo.py        (armada acak)
            python run_demo.py 3      (susunan #3 dari data/layouts.csv)"""
import random
import sys

from core.ai_service import make_ai, play_solo
from core.explain import explain_move
from core.fleet_loader import get_layout, random_layout
from core.state import label


def main():
    layout = get_layout(int(sys.argv[1])) if len(sys.argv) > 1 else random_layout(random.Random(7))
    res = play_solo(layout, make_ai("Bayes", 1))
    print(f"Bayesian AI menenggelamkan seluruh armada dalam {res.shots} tembakan.\n")
    for i, e in enumerate(res.history, 1):
        extra = f" -> {e['ship']} TENGGELAM" if e["ship"] else ""
        print(f"{i:3d}. {label(e['cell']):<4} {e['result']:<5}{extra}")
    rnd = play_solo(layout, make_ai("Random", 1))
    print(f"\nPembanding Random AI: {rnd.shots} tembakan.")
    print("\nContoh penjelasan langkah pertama:")
    print("\n".join(explain_move(make_ai("Bayes", 1)).lines()))


if __name__ == "__main__":
    main()
