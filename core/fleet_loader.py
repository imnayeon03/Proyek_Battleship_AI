"""core/fleet_loader.py
Memuat susunan armada dari TIGA sumber, lalu memvalidasinya (format hasil sama):
  1. acak      -> random_layout()
  2. manual    -> layout_from_text() / ask_manual_layout()   (Mode 1)
  3. dataset   -> load_dataset()  dari data/layouts.csv       (Mode 2)
"""
import csv
import os
import random
from typing import Callable, Dict, List

from core.state import (COLS, FLEET, N, Cell, FleetLayout, cells_ok, label, orientation,
                        parse_cell, ship_cells)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "data", "layouts.csv")
CUSTOM_PATH = os.path.join(ROOT, "data", "custom_layouts.csv")

DEFAULT_MANUAL_TEXT = """
# NamaKapal  TitikAwal  Orientasi(H/V)
Carrier     A1  H
Battleship  B3  H
Cruiser     D5  V
Submarine   F5  V
Destroyer   H8  H
"""


class FleetError(ValueError):
    pass


# ----------------------------------------------------------------- acak
def random_layout(rng=random) -> FleetLayout:
    occupied, layout = set(), {}
    for name, L in FLEET.items():
        while True:
            cells = ship_cells((rng.randrange(N), rng.randrange(N)), L, rng.choice("HV"))
            if cells_ok(cells, occupied):
                layout[name] = cells
                occupied.update(cells)
                break
    return layout


# ----------------------------------------------------------------- validasi
def validate_layout(layout: FleetLayout) -> List[str]:
    """Mengembalikan daftar pesan error (kosong = susunan valid)."""
    errors: List[str] = []
    missing = [n for n in FLEET if n not in layout]
    if missing:
        errors.append(f"Kapal belum ditempatkan: {missing}")
    seen = set()
    for name, cells in layout.items():
        if name not in FLEET:
            errors.append(f"Kapal '{name}' tidak dikenal.")
            continue
        if len(cells) != FLEET[name]:
            errors.append(f"{name} harus memiliki {FLEET[name]} sel, bukan {len(cells)}.")
            continue
        if any(not (0 <= r < N and 0 <= c < N) for r, c in cells):
            errors.append(f"{name} keluar papan.")
            continue
        if cells != ship_cells(min(cells), len(cells), orientation(cells)):
            errors.append(f"{name} harus lurus (horizontal/vertikal) dan berurutan.")
        if seen & set(cells):
            errors.append(f"{name} bertabrakan dengan kapal lain.")
        seen |= set(cells)
    return errors


# ----------------------------------------------------------------- manual
def layout_from_text(text: str) -> FleetLayout:
    """Baris: 'Carrier A1 H'. Baris kosong dan awalan # diabaikan."""
    layout, occupied = {}, set()
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.replace(",", " ").split()
        if len(parts) != 3:
            raise FleetError(f"Format salah pada '{line}'. Contoh: Carrier A1 H")
        name, start, orient = parts[0].capitalize(), parts[1], parts[2].upper()
        if name not in FLEET:
            raise FleetError(f"Kapal '{name}' tidak dikenal. Pilihan: {list(FLEET)}")
        if orient not in ("H", "V"):
            raise FleetError("Orientasi harus H atau V.")
        if name in layout:
            raise FleetError(f"Kapal {name} ditempatkan dua kali.")
        try:
            cells = ship_cells(parse_cell(start), FLEET[name], orient)
        except ValueError as exc:
            raise FleetError(str(exc))
        if not cells_ok(cells, occupied):
            raise FleetError(f"{name} keluar papan atau bertabrakan dengan kapal lain.")
        layout[name] = cells
        occupied.update(cells)
    missing = [n for n in FLEET if n not in layout]
    if missing:
        raise FleetError(f"Kapal belum ditempatkan: {missing}")
    return layout


def layout_to_text(layout: FleetLayout) -> str:
    return "\n".join(f"{name} {label(min(cells))} {orientation(cells)}" for name, cells in layout.items())


def ask_manual_layout(ask: Callable[[str], str] = input, say: Callable[..., None] = print) -> FleetLayout:
    """Penempatan interaktif lewat prompt (ask/say bisa diganti agar mudah diuji)."""
    layout, occupied = {}, set()
    for name, L in FLEET.items():
        while True:
            raw = ask(f"{name} (panjang {L}) - titik awal & orientasi, mis. 'A1 H': ")
            try:
                start, orient = raw.split()
                orient = orient.upper()
                if orient not in ("H", "V"):
                    raise ValueError("Orientasi harus H atau V.")
                cells = ship_cells(parse_cell(start), L, orient)
                if not cells_ok(cells, occupied):
                    raise ValueError("Keluar papan / bertabrakan.")
                layout[name] = cells
                occupied.update(cells)
                break
            except ValueError as exc:
                say("  [!]", exc)
    return layout


# ----------------------------------------------------------------- dataset CSV
def save_dataset(path: str, layouts: List[FleetLayout]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["layout_id", "ship", "start", "orient"])
        for lid, lay in enumerate(layouts, 1):
            for name, cells in lay.items():
                w.writerow([lid, name, label(min(cells)), orientation(cells)])


def append_layout(path: str, layout: FleetLayout) -> int:
    """Tambahkan satu susunan ke CSV (dibuat jika belum ada). Mengembalikan layout_id barunya."""
    errors = validate_layout(layout)
    if errors:
        raise FleetError("Susunan tidak valid:\n- " + "\n- ".join(errors))
    new = not os.path.exists(path)
    lid = 1 if new else max(load_dataset(path), default=0) + 1
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["layout_id", "ship", "start", "orient"])
        for name, cells in layout.items():
            w.writerow([lid, name, label(min(cells)), orientation(cells)])
    return lid


def load_dataset(path: str = DEFAULT_PATH) -> Dict[int, FleetLayout]:
    groups: Dict[int, List[str]] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            groups.setdefault(int(row["layout_id"]), []).append(f'{row["ship"]} {row["start"]} {row["orient"]}')
    return {lid: layout_from_text("\n".join(lines)) for lid, lines in groups.items()}


def ensure_dataset(path: str = DEFAULT_PATH, n: int = 100, seed: int = 2026) -> None:
    """Buat dataset contoh (n susunan armada) jika berkas belum ada."""
    if not os.path.exists(path):
        rng = random.Random(seed)
        save_dataset(path, [random_layout(rng) for _ in range(n)])


def get_layout(layout_id: int, path: str = DEFAULT_PATH) -> FleetLayout:
    data = load_dataset(path)
    if layout_id not in data:
        raise KeyError(f"Susunan #{layout_id} tidak ditemukan di {path}.")
    return data[layout_id]


# ----------------------------------------------------------------- pilih sumber
SOURCES = ("random", "manual", "dataset", "interactive", "custom")


def pick_layout(mode: str, rng=random, dataset_id: int = 3, path: str = DEFAULT_PATH,
                manual_text: str = DEFAULT_MANUAL_TEXT, ask: Callable[[str], str] = input) -> FleetLayout:
    if mode == "random":
        return random_layout(rng)
    if mode == "manual":
        return layout_from_text(manual_text)
    if mode == "dataset":
        return get_layout(dataset_id, path)
    if mode == "custom":
        return get_layout(dataset_id, CUSTOM_PATH)
    if mode == "interactive":
        return ask_manual_layout(ask)
    raise ValueError(f"Sumber armada tidak dikenal: {mode}. Pilihan: {list(SOURCES)}")
