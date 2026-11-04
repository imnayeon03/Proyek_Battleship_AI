"""Smoke test UI lewat pygame tiruan (menguji alur dan kode kita, bukan rendering asli)."""
import importlib
import sys
import unittest

from tests import fake_pygame


class TestApp(unittest.TestCase):
    def setUp(self):
        mods = ("pygame", "ui.app", "ui.gfx", "ui.sprites")
        self._saved = {k: sys.modules.get(k) for k in mods}
        self.pg = fake_pygame.make()
        sys.modules["pygame"] = self.pg
        for m in mods[1:]:
            sys.modules.pop(m, None)
        self.app = importlib.import_module("ui.app").App(seed=1)

    def tearDown(self):
        for k, v in self._saved.items():
            sys.modules.pop(k, None) if v is None else sys.modules.__setitem__(k, v)

    def click(self, tag):
        self.app.draw()
        for r, t in self.app.g.buttons:
            if t == tag:
                self.app.frame(0.016, [self.pg.Event(self.pg.MOUSEBUTTONDOWN, pos=(r.x + 2, r.y + 2), button=1)])
                return
        raise AssertionError(f"tombol {tag!r} tidak ada: {[t for _, t in self.app.g.buttons]}")

    def key(self, k):
        self.app.frame(0.016, [self.pg.Event(self.pg.KEYDOWN, key=k)])

    def click_cell(self, cell):
        x, y, w, h = self.app.lay.cell_rect("enemy", cell)
        self.app.frame(0.016, [self.pg.Event(self.pg.MOUSEBUTTONDOWN, pos=(x + 5, y + 5), button=1)])

    def frames(self, n, dt=0.1):
        for _ in range(n):
            self.app.frame(dt, [])

    def start(self):
        self.click("play"); self.click("start")
        self.assertEqual(self.app.screen_name, "game")

    def test_menu_setup_dan_semua_sumber_armada(self):
        self.app.draw()
        self.click("play")
        self.assertEqual(self.app.screen_name, "setup")
        for tag in ("manual", "dataset", "dataset", "random"):
            self.click(tag)
            self.app.draw()

    def test_howto_dan_kembali(self):
        self.click("howto"); self.assertEqual(self.app.overlay, "howto")
        self.click("close"); self.assertIsNone(self.app.overlay)

    def test_klik_menembak_dan_ai_membalas(self):
        self.start()
        self.click_cell((0, 0))
        s = self.app.session
        self.assertEqual(len(s.eb.shots), 1)
        self.assertTrue(s.awaiting_ai)
        self.frames(30)
        self.assertFalse(s.awaiting_ai)
        self.assertEqual(len(s.hb.shots), 1)

    def test_tembak_sel_sama_ditolak(self):
        self.start()
        self.click_cell((0, 0)); self.frames(30)
        self.click_cell((0, 0))
        self.assertEqual(len(self.app.session.eb.shots), 1)

    def test_hint_heatmap_analysis(self):
        self.start()
        self.key(self.pg.K_h); self.assertIsNotNone(self.app.hint)
        self.key(self.pg.K_m); self.assertTrue(self.app.show_heat); self.app.draw()
        self.key(self.pg.K_i); self.assertEqual(self.app.overlay, "analysis"); self.app.draw()
        self.key(self.pg.K_ESCAPE); self.assertIsNone(self.app.overlay)

    def test_auto_play_sampai_selesai_dan_main_lagi(self):
        self.start()
        self.key(self.pg.K_t)
        for _ in range(6000):
            self.app.frame(0.1, [])
            if self.app.overlay == "victory":
                break
        self.assertEqual(self.app.overlay, "victory")
        self.assertTrue(self.app.session.finished)
        self.click("restart")
        self.assertFalse(self.app.session.finished)
        self.assertEqual(len(self.app.session.eb.shots), 0)

    def test_esc_ke_menu_dan_keluar(self):
        self.start()
        self.key(self.pg.K_ESCAPE); self.assertEqual(self.app.screen_name, "menu")
        self.key(self.pg.K_ESCAPE); self.assertFalse(self.app.running)

    def test_siang_malam_transisi_halus(self):
        self.app.draw()
        self.assertEqual(self.app.tod, 0.0)
        self.key(self.pg.K_d)
        self.assertEqual(self.app.tod_target, 1.0)
        self.frames(3)
        self.assertTrue(0.0 < self.app.tod < 1.0)          # bergerak bertahap, bukan lompat
        self.frames(30)
        self.assertEqual(self.app.tod, 1.0)
        for screen in ("menu", "setup"):
            self.app.screen_name = screen; self.app.draw()
        self.app.screen_name = "menu"
        self.start(); self.frames(2)                       # game dirender pada mode malam
        self.click("tod")
        self.frames(30)
        self.assertEqual(self.app.tod, 0.0)

    def test_hasil_tembakan_baru_tampil_setelah_peluru_mendarat(self):
        self.start()
        self.click_cell((0, 0))
        self.assertTrue(self.app.busy)
        self.assertIn(("enemy", (0, 0)), self.app.hidden)   # belum ada penanda saat peluru masih terbang
        self.frames(8, dt=0.1)
        self.assertFalse(self.app.busy and ("enemy", (0, 0)) in self.app.hidden)
        self.assertNotIn(("enemy", (0, 0)), self.app.hidden)
        self.assertTrue(self.app.parts or self.app.rings)   # ledakan/percikan terbentuk
        self.assertEqual(self.app.log_view[0][0], "human")

    def test_klik_diabaikan_saat_peluru_terbang(self):
        self.start()
        self.click_cell((0, 0)); self.click_cell((1, 1))
        self.assertEqual(len(self.app.session.eb.shots), 1)

    def test_kapal_tenggelam_memunculkan_banner_dan_asap(self):
        self.start()
        s = self.app.session
        for c in s.eb.layout["Destroyer"]:
            self.app.shoot(c)
            self.frames(40, dt=0.1)
        self.assertIn("Destroyer", s.eb.sunk)
        self.assertEqual(self.app._visible_sunk(s.eb, "enemy"), ["Destroyer"])
        self.frames(20, dt=0.1)
        self.assertTrue(any(p["kind"] == "smoke" for p in self.app.parts))

    def test_guncangan_papan_saat_terkena(self):
        self.start()
        self.app.shake["human"] = 9.0
        self.app.update(0.016)
        self.assertNotEqual(self.app.lay.shift["human"], (0, 0))
        self.frames(30)
        self.assertEqual(self.app.lay.shift["human"], (0, 0))


if __name__ == "__main__":
    unittest.main()
