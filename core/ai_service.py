"""core/ai_service.py
Penghubung antara core AI dan UI/skrip: membuat AI, memainkan game solo, validasi, evaluasi.
"""
import csv
import random
import time
from dataclasses import dataclass, field
from statistics import mean, median
from typing import Dict, List

from core.actions import Shot
from core.bayes_ai import BayesAI
from core.board import Board
from core.random_ai import RandomAI

ALGORITHMS = {"Bayes": BayesAI, "Random": RandomAI}


def make_ai(algo: str, seed=None):
    if algo not in ALGORITHMS:
        raise ValueError(f"Algoritma tidak dikenal: {algo}")
    return ALGORITHMS[algo](random.Random(seed))


@dataclass
class GameResult:
    algorithm: str
    shots: int = 0
    history: List[Dict] = field(default_factory=list)      # {"cell","result","ship"}
    elapsed_sec: float = 0.0


def play_solo(layout, ai) -> GameResult:
    """AI memburu satu armada tersembunyi sampai semua kapal tenggelam."""
    t0 = time.perf_counter()
    board, hist = Board(layout), []
    ai.reset()
    while not board.all_sunk():
        cell = ai.choose()
        res = Shot(cell, ai.name).apply(board)
        ai.update(cell, res)
        hist.append({"cell": cell, "result": res.result, "ship": res.ship})
    return GameResult(ai.name, len(hist), hist, time.perf_counter() - t0)


def solve(layout, ai) -> int:
    return play_solo(layout, ai).shots


def validate_game(layout, history) -> bool:
    """Putar ulang tembakan pada papan baru: hasil harus sama, tak ada sel berulang, semua kapal tenggelam."""
    board = Board(layout)
    for e in history:
        if not Shot(e["cell"]).is_applicable(board):
            return False
        if board.fire(e["cell"]).result != e["result"]:
            return False
    return board.all_sunk()


def run_algorithm(layout, algo: str, seed=None, repeats: int = 1) -> Dict:
    times, res = [], None
    for _ in range(max(1, repeats)):
        res = play_solo(layout, make_ai(algo, seed))
        times.append(res.elapsed_sec)
    return {"algo": algo, "shots": res.shots, "time_ms": 1000 * sum(times) / len(times),
            "valid": validate_game(layout, res.history)}


def evaluate_fleets(dataset: Dict[int, dict], repeats: int = 1) -> List[Dict]:
    rows = []
    for lid in sorted(dataset):
        rows.append({"layout_id": lid, "bayes": run_algorithm(dataset[lid], "Bayes", lid, repeats),
                     "random": run_algorithm(dataset[lid], "Random", lid, repeats)})
    return rows


def summarize(rows: List[Dict]) -> Dict:
    out = {}
    for key in ("bayes", "random"):
        v = [r[key]["shots"] for r in rows]
        out[key] = {"mean": mean(v), "median": median(v), "min": min(v), "max": max(v)}
    out["saving"] = out["random"]["mean"] - out["bayes"]["mean"]
    out["percent"] = (1 - out["bayes"]["mean"] / out["random"]["mean"]) * 100
    return out


def format_table(rows: List[Dict]) -> str:
    s = summarize(rows)
    lines = [f"{'AI':<14}{'rata-rata':>10}{'median':>9}{'terbaik':>9}{'terburuk':>10}"]
    for nm, k in (("Bayesian AI", "bayes"), ("Random AI", "random")):
        d = s[k]
        lines.append(f"{nm:<14}{d['mean']:>10.1f}{d['median']:>9.0f}{d['min']:>9}{d['max']:>10}")
    lines.append(f"\nBayesian AI lebih hemat ~ {s['saving']:.1f} tembakan per game ({s['percent']:.0f}% lebih efisien).")
    return "\n".join(lines)


def save_csv(rows: List[Dict], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["layout_id", "bayes_shots", "bayes_ms", "random_shots", "random_ms", "valid"])
        for r in rows:
            b, a = r["bayes"], r["random"]
            w.writerow([r["layout_id"], b["shots"], f"{b['time_ms']:.3f}", a["shots"], f"{a['time_ms']:.3f}",
                        b["valid"] and a["valid"]])
