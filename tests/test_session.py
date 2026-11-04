import random
import unittest

from core.bayes_ai import BayesAI
from core.fleet_loader import random_layout
from ui.layout import Layout
from ui.session import GameSession


def make(seed=1):
    rng = random.Random(seed)
    return GameSession(random_layout(rng), random_layout(rng), BayesAI(random.Random(seed)), BayesAI(random.Random(seed)))


class TestSession(unittest.TestCase):
    def test_tembak_dan_balasan_ai(self):
        s = make()
        self.assertTrue(s.fire("A1"))
        self.assertEqual(len(s.eb.shots), 1)
        self.assertEqual(len(s.hb.shots), 1)

    def test_input_salah_tidak_memakai_giliran(self):
        s = make()
        self.assertFalse(s.fire("Z9"))
        self.assertTrue(s.fire("A1"))
        self.assertFalse(s.fire("A1"))
        self.assertEqual((len(s.eb.shots), len(s.hb.shots)), (1, 1))

    def test_human_fire_menunggu_ai(self):
        s = make()
        self.assertTrue(s.human_fire((0, 0)))
        self.assertTrue(s.awaiting_ai)
        self.assertFalse(s.human_fire((0, 1)))
        self.assertTrue(s.ai_reply())
        self.assertFalse(s.awaiting_ai)

    def test_auto_play_sampai_ada_pemenang(self):
        s = make()
        n = s.auto_play()
        self.assertTrue(s.finished)
        self.assertIn(s.winner, ("ANDA", "AI"))
        self.assertTrue(s.used_ai)
        self.assertLessEqual(n, 100)
        self.assertFalse(s.fire("A1"))

    def test_hint_dan_reset(self):
        s = make()
        ex = s.hint()
        self.assertTrue(s.used_ai)
        self.assertEqual(ex.mode, "hunt")
        s.fire("A1"); s.reset()
        self.assertEqual((len(s.eb.shots), s.winner, s.used_ai), (0, None, False))

    def test_pemain_menang_jika_semua_kapal_lawan_tenggelam(self):
        s = make()
        for cells in list(s.eb.layout.values()):
            for c in cells:
                if s.finished:
                    break
                s.human_fire(c); s.ai_reply() if not s.finished else None
        self.assertTrue(s.finished)


class TestLayout(unittest.TestCase):
    def test_klik_ke_sel(self):
        L = Layout()
        for which in ("human", "enemy"):
            for cell in ((0, 0), (9, 9), (4, 7)):
                x, y, w, h = L.cell_rect(which, cell)
                self.assertEqual(L.cell_at(which, (x + w // 2, y + h // 2)), cell)
        self.assertIsNone(L.cell_at("enemy", (0, 0)))

    def test_papan_di_dalam_layar_dan_tidak_tumpang_tindih(self):
        from ui.layout import H, W
        L = Layout()
        (hx, hy, hw, hh), (ex, ey, ew, eh) = L.board_rect("human"), L.board_rect("enemy")
        self.assertLess(hx + hw, L.panel[0])
        self.assertLess(L.panel[0] + L.panel[2], ex)
        self.assertLessEqual(ex + ew, W)
        self.assertLess(ey + eh + 60, H)


if __name__ == "__main__":
    unittest.main()
