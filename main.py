"""main.py - titik masuk game WAR BATTLESHIPS (Pygame).
Jalankan:  python main.py
Opsional:  python main.py --fleet dataset --dataset-id 3 --seed 7
"""
import argparse

from core.fleet_loader import DEFAULT_PATH
from ui.app import App


def main():
    ap = argparse.ArgumentParser(description="War Battleships - Bayesian AI vs Manusia")
    ap.add_argument("--fleet", choices=["random", "manual", "dataset"], default="random", help="sumber armada Anda")
    ap.add_argument("--dataset-id", type=int, default=1, help="nomor susunan di CSV (untuk --fleet dataset)")
    ap.add_argument("--layouts", default=DEFAULT_PATH, help="berkas CSV susunan armada")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    App(fleet_mode=args.fleet, dataset_id=args.dataset_id, layouts_path=args.layouts, seed=args.seed).run()


if __name__ == "__main__":
    main()
