import os
import unittest
from core.campaign import LEVELS, RookieAI, IslandGunnerAI, SmartBayesAI, CampaignProgress
from core.actions import ShotResult


class TestCampaign(unittest.TestCase):
    def test_level_count(self):
        self.assertEqual(len(LEVELS), 10)
        for i, lvl in enumerate(LEVELS):
            self.assertEqual(lvl["id"], i + 1)
            ai = lvl["ai_factory"](None)
            self.assertTrue(hasattr(ai, "choose"))
            self.assertTrue(hasattr(ai, "update"))
            self.assertTrue(hasattr(ai, "reset"))

    def test_rookie_ai(self):
        ai = RookieAI()
        c = ai.choose()
        self.assertEqual(len(c), 2)
        ai.update(c, ShotResult("miss", None, None))
        ai.reset()

    def test_island_gunner_ai(self):
        ai = IslandGunnerAI()
        c = ai.choose()
        self.assertEqual(len(c), 2)
        ai.update((5, 5), ShotResult("hit", "Destroyer", None))
        next_c = ai.choose()
        # Should be a neighbor of (5, 5)
        self.assertIn(next_c, [(4, 5), (6, 5), (5, 4), (5, 6)])

    def test_smart_bayes_ai(self):
        ai = SmartBayesAI(accuracy=0.8, parity=True)
        c = ai.choose()
        self.assertEqual(len(c), 2)
        ai.update(c, ShotResult("miss", None, None))

    def test_campaign_progress(self):
        tmp_file = "test_progress_tmp.json"
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        try:
            p = CampaignProgress(filepath=tmp_file)
            self.assertEqual(p.unlocked_level, 1)
            self.assertTrue(p.is_unlocked(1))
            self.assertFalse(p.is_unlocked(2))

            # Win level 1 in 35 shots (<= 42 -> 3 stars)
            stars = p.record_victory(1, 35)
            self.assertEqual(stars, 3)
            self.assertEqual(p.get_stars(1), 3)
            self.assertEqual(p.unlocked_level, 2)
            self.assertTrue(p.is_unlocked(2))
            self.assertEqual(p.total_stars(), 3)

            # Reload
            p2 = CampaignProgress(filepath=tmp_file)
            self.assertEqual(p2.unlocked_level, 2)
            self.assertEqual(p2.get_stars(1), 3)
        finally:
            if os.path.exists(tmp_file):
                os.remove(tmp_file)

    def test_campaign_ui_flow(self):
        import tests.fake_pygame as fake_pygame
        import sys
        sys.modules["pygame"] = fake_pygame.make()
        from ui.app import App
        app = App()
        app.draw()
        self.assertEqual(app.screen_name, "menu")

        # Click campaign in menu
        app.on_button("campaign")
        self.assertEqual(app.screen_name, "levels")
        app.draw()
        self.assertEqual(len(app.level_hitboxes), 10)

        # Level 1 is unlocked, open its briefing
        app.campaign_selected_level = 1
        app.level_dialog_open = True
        app.draw()

        # Start level battle
        app.on_button("campaign_battle")
        self.assertEqual(app.screen_name, "game")
        self.assertEqual(app.game_mode, "campaign")
        self.assertIsNotNone(app.session)


if __name__ == "__main__":
    unittest.main()
