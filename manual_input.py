"""manual_input.py - Mode 1: input susunan armada MANUAL lewat terminal.
Susunan divalidasi, diuji dengan Bayesian AI, lalu disimpan ke data/custom_layouts.csv.
Jalankan:  python manual_input.py"""
import sys

from core.ai_service import make_ai, solve
from core.fleet_loader import CUSTOM_PATH, FleetError, append_layout, ask_manual_layout, layout_to_text


def main():
    print("=== INPUT ARMADA MANUAL (Battleship AI) ===")
    print("Format tiap kapal: titik-awal orientasi, contoh 'A1 H' (H=horizontal, V=vertikal)\n")
    layout = ask_manual_layout()
    try:
        lid = append_layout(CUSTOM_PATH, layout)
    except FleetError as exc:
        print("\nSUSUNAN TIDAK VALID:\n", exc)
        sys.exit(1)
    print("\nSusunan Anda:\n" + layout_to_text(layout))
    print(f"\nBayesian AI menenggelamkan armada ini dalam {solve(layout, make_ai('Bayes', 1))} tembakan.")
    print(f"Disimpan sebagai susunan #{lid} di {CUSTOM_PATH}.")


if __name__ == "__main__":
    main()
