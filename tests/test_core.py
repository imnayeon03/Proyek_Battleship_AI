import random
import unittest

import numpy as np

from core.actions import Shot
from core.ai_service import (evaluate_fleets, format_table, make_ai, play_solo, run_algorithm, solve,
                             summarize, validate_game)
from core.bayes_ai import BayesAI
from core.board import Board
from core.explain import explain_move
from core.fleet_loader import (FleetError, layout_from_text, load_dataset, random_layout, validate_layout)
from core.state import FLEET, N, label, parse_cell, ship_cells


class TestState(unittest.TestCase):
    def test_koordinat(self):
        self.assertEqual(parse_cell("e5"), (4, 4))
        self.assertEqual(label((9, 9)), "J10")
        for bad in ("K1", "A0", "A11", "5", "", "Axx"):
            with self.assertRaises(ValueError):
                parse_cell(bad)

    def test_ship_cells(self):
        self.assertEqual(ship_cells((0, 0), 3, "H"), [(0, 0), (0, 1), (0, 2)])
        self.assertEqual(ship_cells((0, 0), 2, "V"), [(0, 0), (1, 0)])


class TestBoard(unittest.TestCase):
    def setUp(self):
        self.b = Board(layout_from_text("Carrier A1 H\nBattleship A3 H\nCruiser A5 H\nSubmarine A7 H\nDestroyer A9 H"))

    def test_miss_hit_sunk(self):
        self.assertEqual(self.b.fire((5, 5)).result, "miss")
        self.assertEqual(Shot((8, 0)).apply(self.b).result, "hit")
        res = Shot((8, 1)).apply(self.b)
        self.assertEqual((res.result, res.ship), ("sunk", "Destroyer"))
        self.assertEqual(self.b.sunk, ["Destroyer"])

    def test_precondition_shot(self):
        self.b.fire((0, 0))
        self.assertFalse(Shot((0, 0)).is_applicable(self.b))
        with self.assertRaises(ValueError):
            Shot((0, 0)).apply(self.b)
        with self.assertRaises(ValueError):
            Shot((10, 0)).apply(self.b)

    def test_all_sunk(self):
        for cells in list(self.b.layout.values()):
            for c in cells:
                self.b.fire(c)
        self.assertTrue(self.b.all_sunk())
        self.assertFalse(Shot((9, 9)).is_applicable(self.b))


class TestFleet(unittest.TestCase):
    def test_random_valid(self):
        rng = random.Random(1)
        for _ in range(50):
            self.assertEqual(validate_layout(random_layout(rng)), [])

    def test_text_errors(self):
        for text in ("Carrier A1 X", "Kapalx A1 H", "Carrier A1", "Carrier A1 H\nCarrier B1 H", "Carrier H1 H"):
            with self.assertRaises(FleetError):
                layout_from_text(text)

    def test_tabrakan(self):
        with self.assertRaises(FleetError):
            layout_from_text("Carrier A1 H\nBattleship A1 V\nCruiser A5 H\nSubmarine A7 H\nDestroyer A9 H")

    def test_dataset_csv_pengguna(self):
        d = load_dataset()
        self.assertEqual(len(d), 100)
        for lay in d.values():
            self.assertEqual(validate_layout(lay), [])


class TestAI(unittest.TestCase):
    def test_bayes_target_setelah_kena(self):
        lay = layout_from_text("Carrier A1 H\nBattleship A3 H\nCruiser A5 H\nSubmarine A7 H\nDestroyer A9 H")
        b, ai = Board(lay), BayesAI(random.Random(1))
        res = b.fire((0, 2)); ai.update((0, 2), res)
        self.assertEqual(ai.mode, "target")
        nxt = ai.choose()
        self.assertEqual(abs(nxt[0] - 0) + abs(nxt[1] - 2), 1)       # menembak tetangga sel kena

    def test_probabilitas_nol_pada_sel_ditembak(self):
        ai, b = BayesAI(random.Random(2)), Board(random_layout(random.Random(2)))
        for _ in range(30):
            c = ai.choose(); ai.update(c, b.fire(c))
        p = ai.probability()
        for c in b.shots:
            self.assertEqual(p[c], 0)
        self.assertGreater(p.sum(), 0)

    def test_kebenaran_tidak_pernah_dikesampingkan(self):
        rng = random.Random(3)
        for _ in range(20):
            lay = random_layout(rng); b = Board(lay); ai = BayesAI(random.Random(5))
            while not b.all_sunk():
                c = ai.choose(); ai.update(c, b.fire(c))
                if b.all_sunk():
                    break
                p = ai.probability()
                for nm, cells in lay.items():
                    if nm in b.sunk:
                        continue
                    for cell in cells:
                        if cell not in b.shots:
                            self.assertGreater(p[cell], 0)

    def test_tidak_ada_sel_berulang_dan_selesai(self):
        for algo in ("Bayes", "Random"):
            res = play_solo(random_layout(random.Random(4)), make_ai(algo, 4))
            cells = [e["cell"] for e in res.history]
            self.assertEqual(len(cells), len(set(cells)))
            self.assertLessEqual(res.shots, N * N)
            self.assertTrue(validate_game(random_layout(random.Random(4)), res.history))

    def test_bayes_lebih_baik_dari_random(self):
        rows = evaluate_fleets({i: l for i, l in list(load_dataset().items())[:15]})
        s = summarize(rows)
        self.assertLess(s["bayes"]["mean"], s["random"]["mean"])
        self.assertIn("Bayesian AI", format_table(rows))

    def test_algoritma_tidak_dikenal(self):
        with self.assertRaises(ValueError):
            make_ai("DFS")

    def test_explain(self):
        ai = BayesAI(random.Random(1))
        ex = explain_move(ai)
        self.assertEqual(ex.mode, "hunt")
        self.assertAlmostEqual(sum(1 for _ in ex.top), 5)
        self.assertEqual(ex.rank, 1)
        lay = layout_from_text("Carrier A1 H\nBattleship A3 H\nCruiser A5 H\nSubmarine A7 H\nDestroyer A9 H")
        ai.update((0, 0), Board(lay).fire((0, 0)))
        self.assertEqual(explain_move(ai).mode, "target")


if __name__ == "__main__":
    unittest.main()
