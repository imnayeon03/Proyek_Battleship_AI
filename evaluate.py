"""evaluate.py - jalankan Bayesian AI vs Random AI pada semua susunan di data/layouts.csv.
Hasil disimpan ke docs/hasil_evaluasi.csv. Angka berasal dari eksekusi nyata."""
import os

from core.ai_service import evaluate_fleets, format_table, save_csv
from core.fleet_loader import load_dataset


def main():
    rows = evaluate_fleets(load_dataset())
    print(format_table(rows))
    os.makedirs("docs", exist_ok=True)
    save_csv(rows, os.path.join("docs", "hasil_evaluasi.csv"))
    print("\nTersimpan: docs/hasil_evaluasi.csv")


if __name__ == "__main__":
    main()
