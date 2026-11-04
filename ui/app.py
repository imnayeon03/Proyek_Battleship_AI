"""ui/app.py - game WAR BATTLESHIPS (Pygame): menu, fleet placement, battle (Human vs AI & Player vs Player).
Theme: cartoon ocean waves, DAY/NIGHT mode (press D), curved projectiles, explosions, splashes, sinking smoke.
Game logic lives in ui/session.py and ui/pvp_session.py; this file handles drawing and input.
"""
import math
import random

import pygame

from core.ai_service import run_algorithm
from core.fleet_loader import (DEFAULT_MANUAL_TEXT, DEFAULT_PATH, ensure_dataset, get_layout, layout_from_text,
                               load_dataset, random_layout)
from core.state import FLEET, HIT, MISS
from ui import sprites
from ui.gfx import Gfx, STATIC, mix, shade
from ui.layout import H, W, Layout
from ui.session import GameSession
from ui.pvp_session import PvPSession

TITLE = "WAR BATTLESHIPS"
AI_DELAY, AUTO_DELAY, FLIGHT = 0.4, 0.4, 0.5

HOWTO = [
    "Goal: Sink all enemy ships before all your ships are sunk.",
    "Click a cell on ENEMY RADAR (right board) to fire. AI replies by firing on your board (left).",
    "Fire = HIT, water ripple = MISS. Enemy ships only appear when fully sunk.",
    "H = AI shot suggestion (with full reasoning).   A = AI fires for you.",
    "T = auto-play.   M = AI probability heatmap on radar.   I = AI Analysis.",
    "D = toggle DAY / NIGHT mode.   R = randomize / restart.   Esc = back.",
]

HOWTO_PVP = [
    "Goal: Sink all of your opponent's ships before they sink yours.",
    "Players take turns. When it is your turn, click a cell on ENEMY RADAR to fire.",
    "After each shot the game shows a PASS screen - hand the device to the other player.",
    "Fire = HIT, water ripple = MISS. Enemy ships only appear when fully sunk.",
    "D = toggle DAY / NIGHT mode.   R = restart.   Esc = back to menu.",
]


class App:
    def __init__(self, screen=None, fleet_mode="random", dataset_id=1, layouts_path=None, seed=None):
        pygame.init()
        self.screen = screen or pygame.display.set_mode((W, H))
        pygame.display.set_caption("War Battleships")
        self.clock = pygame.time.Clock()
        self.g, self.lay = Gfx(self.screen), Layout()
        self.rng = random.Random(seed)
        self.fx_rng = random.Random()
        self.t, self.running = 0.0, True
        self.tod, self.tod_target = 0.0, 0.0          # 0 day -> 1 night
        self.screen_name = "menu"
        self.layouts_path = layouts_path or DEFAULT_PATH
        ensure_dataset(self.layouts_path)
        self.dataset_ids = sorted(load_dataset(self.layouts_path))
        self.dataset_idx = self.dataset_ids.index(dataset_id) if dataset_id in self.dataset_ids else 0
        self.fleet_mode = fleet_mode
        self.human_layout = self._make_layout(fleet_mode)
        self.session = None
        self.overlay = None                  # None | howto | victory | analysis | pvp_pass
        self.analysis = None
        self.game_mode = "hvai"              # "hvai" = Human vs AI,  "pvp" = Player vs Player
        self._init_sounds()
        self._reset_battle()

    # ------------------------------------------------------------ sound
    def _init_sounds(self):
        """Initialize pygame mixer and generate procedural sound effects."""
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self.snd_shoot = self._gen_shoot()
            self.snd_hit = self._gen_hit()
            self.snd_splash = self._gen_splash()
            self.snd_sunk = self._gen_sunk()
            self._sound_ok = True
        except Exception:
            self._sound_ok = False

    @staticmethod
    def _make_wave(arr, volume=0.9):
        """Clip and convert float array to int16 Sound."""
        import numpy as np
        arr = arr * volume
        arr = arr / max(abs(arr).max(), 1e-6)
        wave = (arr * 32767).clip(-32767, 32767).astype(np.int16)
        return pygame.sndarray.make_sound(wave)

    def _gen_shoot(self):
        import numpy as np
        sr = 44100; dur = 0.28
        t = np.linspace(0, dur, int(sr * dur), False)
        boom = np.sin(2 * np.pi * 85 * t) * np.exp(-t * 20)
        noise = np.random.default_rng(1).uniform(-1, 1, len(t)) * np.exp(-t * 35) * 0.45
        wave = boom + noise
        return self._make_wave(wave, 0.70)

    def _gen_hit(self):
        import numpy as np
        sr = 44100; dur = 0.42
        t = np.linspace(0, dur, int(sr * dur), False)
        boom = np.sin(2 * np.pi * 58 * t) * np.exp(-t * 9)
        crackle = np.random.default_rng(2).uniform(-1, 1, len(t)) * np.exp(-t * 7) * 0.5
        mid = np.sin(2 * np.pi * 290 * t) * np.exp(-t * 22) * 0.3
        return self._make_wave(boom + crackle + mid, 0.78)

    def _gen_splash(self):
        import numpy as np
        sr = 44100; dur = 0.38
        t = np.linspace(0, dur, int(sr * dur), False)
        env = np.exp(-t * 7) * (1 - np.exp(-t * 60))
        noise = np.random.default_rng(3).uniform(-1, 1, len(t)) * env
        bubble = np.sin(2 * np.pi * 750 * t) * env * 0.25
        return self._make_wave(noise + bubble, 0.55)

    def _gen_sunk(self):
        import numpy as np
        sr = 44100; dur = 0.65
        t = np.linspace(0, dur, int(sr * dur), False)
        boom = np.sin(2 * np.pi * 48 * t) * np.exp(-t * 5.5)
        boom2 = np.sin(2 * np.pi * 115 * t) * np.exp(-t * 9) * 0.5
        noise = np.random.default_rng(4).uniform(-1, 1, len(t)) * np.exp(-t * 4.5) * 0.65
        return self._make_wave(boom + boom2 + noise, 0.88)

    def play_sound(self, name):
        if not self._sound_ok:
            return
        snd = {"shoot": self.snd_shoot, "hit": self.snd_hit,
               "splash": self.snd_splash, "sunk": self.snd_sunk}.get(name)
        if snd:
            snd.play()

    # ------------------------------------------------------------ fleet
    def _reset_battle(self):
        self.hint, self.show_heat, self.auto = None, False, False
        self.parts, self.rings, self.projectiles, self.confetti = [], [], [], []
        self.hidden = set()                  # (board, cell) whose projectile hasn't landed yet
        self.banner = None
        self.msg = "Your turn: click on Enemy Radar to fire."
        self.log_view = []
        self.shake = {"human": 0.0, "enemy": 0.0}
        self._ai_timer = self._auto_timer = self._smoke_timer = 0.0
        self.pvp_pass_timer = 0.0

    def _make_layout(self, mode):
        if mode == "manual":
            return layout_from_text(DEFAULT_MANUAL_TEXT)
        if mode == "dataset":
            return get_layout(self.dataset_ids[self.dataset_idx], self.layouts_path)
        return random_layout(self.rng)

    def set_fleet(self, mode):
        if mode == "dataset" and self.fleet_mode == "dataset":
            self.dataset_idx = (self.dataset_idx + 1) % len(self.dataset_ids)
        self.fleet_mode = mode
        self.human_layout = self._make_layout(mode)

    def start_game(self, mode=None):
        if mode:
            self.game_mode = mode
        if self.game_mode == "pvp":
            self.session = PvPSession(self.human_layout, random_layout(self.rng))
        else:
            self.session = GameSession(self.human_layout, random_layout(self.rng))
        self._reset_battle()
        self.overlay, self.analysis = None, None
        self.screen_name = "game"

    # ------------------------------------------------------------ input
    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
        elif e.type == pygame.KEYDOWN:
            self.on_key(e.key)
        elif e.type == pygame.MOUSEBUTTONDOWN and getattr(e, "button", 1) == 1:
            tag = self.g.hit_test(e.pos)
            if tag:
                self.on_button(tag)
            elif self.screen_name == "game" and not self.overlay:
                s = self.session
                if isinstance(s, PvPSession):
                    # PvP: current player shoots at opposite board
                    which_target = "enemy" if s.current_player == 1 else "human"
                    cell = self.lay.cell_at(which_target, e.pos)
                    if cell:
                        self.shoot_pvp(cell)
                else:
                    cell = self.lay.cell_at("enemy", e.pos)
                    if cell:
                        self.shoot(cell)

    def on_key(self, k):
        n = self.screen_name
        if k == pygame.K_d:
            self.toggle_tod()
        elif k == pygame.K_ESCAPE:
            if self.overlay:
                self.overlay = None
            elif n != "menu":
                self.screen_name, self.auto = "menu", False
            else:
                self.running = False
        elif n == "setup" and k == pygame.K_r:
            self.set_fleet("random")
        elif n == "setup" and k == pygame.K_RETURN:
            self.start_game()
        elif n == "game":
            {pygame.K_h: self.ask_hint, pygame.K_a: self.ai_step, pygame.K_t: self.toggle_auto,
             pygame.K_m: self.toggle_heat, pygame.K_i: self.toggle_analysis,
             pygame.K_r: self.start_game}.get(k, lambda: None)()

    def on_button(self, tag):
        actions = {
            "play":     lambda: (setattr(self, "game_mode", "hvai"), setattr(self, "screen_name", "setup")),
            "play_pvp": lambda: (setattr(self, "game_mode", "pvp"),  setattr(self, "screen_name", "setup")),
            "howto":    lambda: setattr(self, "overlay", "howto"),
            "quit":     lambda: setattr(self, "running", False),
            "menu":     lambda: (setattr(self, "screen_name", "menu"),
                                 setattr(self, "auto", False),
                                 setattr(self, "overlay", None)),
            "random":   lambda: self.set_fleet("random"),
            "manual":   lambda: self.set_fleet("manual"),
            "dataset":  lambda: self.set_fleet("dataset"),
            "start":    self.start_game,
            "restart":  self.start_game,
            "hint":     self.ask_hint,
            "ai_step":  self.ai_step,
            "auto":     self.toggle_auto,
            "heat":     self.toggle_heat,
            "analysis": self.toggle_analysis,
            "tod":      self.toggle_tod,
            "close":    lambda: setattr(self, "overlay", None),
            "pass_ok":  lambda: setattr(self, "overlay", None),
        }
        if tag in actions:
            actions[tag]()

    # ------------------------------------------------------------ game actions
    @property
    def busy(self):
        return bool(self.projectiles)

    def toggle_tod(self):
        self.tod_target = 0.0 if self.tod_target >= 0.5 else 1.0

    def shoot(self, cell):
        """Human vs AI shot."""
        s = self.session
        if s is None or s.finished or s.awaiting_ai or self.busy or self.overlay:
            return
        if s.human_fire(cell):
            self.play_sound("shoot")
            self.hint = None
            self._launch("human", cell, s.last_human[1], s.log[-1])
        else:
            self.msg = s.message

    def shoot_pvp(self, cell):
        """Player vs Player shot."""
        s = self.session
        if s is None or s.finished or self.busy or self.overlay:
            return
        prev_player = s.current_player
        if s.fire(cell):
            self.play_sound("shoot")
            self.hint = None
            # Determine which visual board to target
            which = "enemy" if prev_player == 1 else "human"
            hx, hy, hw, hh = self.lay.board_rect("human")
            ex, ey, _, _ = self.lay.board_rect("enemy")
            sx, sy = (hx + hw + 30, hy + hh / 2) if prev_player == 1 else (ex - 30, ey + hh / 2)
            tx, ty = self.lay.cell_center(which, cell)
            res = s.last_shot[1]
            self.projectiles.append({
                "t0": self.t, "dur": FLIGHT, "sx": sx, "sy": sy,
                "ex": tx, "ey": ty, "which": which,
                "cell": cell, "res": res, "text": s.log[-1], "shooter": f"p{prev_player}",
            })
            self.hidden.add((which, cell))
            self.msg = s.message
            if not s.finished:
                self.pvp_pass_timer = 1.4   # show pass screen after projectile lands
        else:
            self.msg = s.message

    def _launch(self, shooter, cell, res, text):
        which = "enemy" if shooter == "human" else "human"
        hx, hy, hw, hh = self.lay.board_rect("human")
        ex, ey, _, _ = self.lay.board_rect("enemy")
        sx, sy = (hx + hw + 30, hy + hh / 2) if shooter == "human" else (ex - 30, ey + hh / 2)
        tx, ty = self.lay.cell_center(which, cell)
        self.projectiles.append({"t0": self.t, "dur": FLIGHT, "sx": sx, "sy": sy, "ex": tx, "ey": ty, "which": which,
                                 "cell": cell, "res": res, "text": text, "shooter": shooter})
        self.hidden.add((which, cell))

    def _land(self, pr):
        self.hidden.discard((pr["which"], pr["cell"]))
        x, y = self.lay.cell_center(pr["which"], pr["cell"])
        res = pr["res"]
        if res.result == MISS:
            sprites.spawn_splash(self.fx_rng, self.parts, self.rings, x, y)
            self.play_sound("splash")
        else:
            sprites.spawn_explosion(self.fx_rng, self.parts, self.rings, x, y, big=res.is_sunk)
            self.shake[pr["which"]] = 9.0 if res.is_sunk else 6.0
            if res.is_sunk:
                self.play_sound("sunk")
            else:
                self.play_sound("hit")
        if res.is_sunk:
            shooter = pr["shooter"]
            is_good = (shooter == "human") or (shooter.startswith("p"))
            self.banner = [f"{res.ship.upper()} SUNK!", STATIC["good"] if is_good else STATIC["bad"], 0.0]
        self.msg = pr["text"]
        self.log_view = (self.log_view + [(pr["shooter"], pr["text"], res.result)])[-30:]
        if self.session.finished:
            self._on_end()
        elif pr["shooter"] == "human":
            self._ai_timer = AI_DELAY

    def ask_hint(self):
        if self.session and not isinstance(self.session, PvPSession) and not self.session.finished:
            self.hint = self.session.hint()

    def ai_step(self):
        s = self.session
        if s and not isinstance(s, PvPSession) and not s.finished and not s.awaiting_ai and not self.busy:
            self.shoot(s.helper.choose())

    def toggle_auto(self):
        self.auto = not self.auto

    def toggle_heat(self):
        self.show_heat = not self.show_heat

    def toggle_analysis(self):
        s = self.session
        if not s or isinstance(s, PvPSession):
            return
        if self.overlay == "analysis":
            self.overlay = None
            return
        self.analysis = {"rows": [run_algorithm(s.human_layout, a, seed=1) for a in ("Bayes", "Random")],
                         "hint": s.hint() if not s.finished else None}
        self.overlay = "analysis"

    def _on_end(self):
        self.overlay, self.auto = "victory", False
        s = self.session
        is_win = (not isinstance(s, PvPSession) and s.winner == "ANDA") or \
                 (isinstance(s, PvPSession))
        if is_win:
            for _ in range(90):
                r = self.fx_rng
                self.confetti.append({"x": r.uniform(0, W), "y": r.uniform(-120, -10),
                                      "vx": r.uniform(-30, 30), "vy": r.uniform(70, 190),
                                      "life": r.uniform(3, 5), "max": 5, "grav": 20, "kind": "drop",
                                      "size": r.uniform(3, 6),
                                      "color": r.choice([STATIC["accent"], STATIC["good"], STATIC["red"],
                                                         (110, 200, 255), (255, 255, 255)])})

    # ------------------------------------------------------------ update
    def _visible_sunk(self, board, which):
        return [nm for nm in board.sunk if not any((which, c) in self.hidden for c in board.layout[nm])]

    def update(self, dt):
        self.t += dt
        step = dt / 1.4
        self.tod = min(self.tod_target, self.tod + step) if self.tod < self.tod_target else max(self.tod_target, self.tod - step)
        self.g.tod = self.tod
        sprites.update_effects(self.parts, self.rings, dt)
        sprites.update_effects(self.confetti, [], dt)
        if self.banner:
            self.banner[2] += dt
            if self.banner[2] > 2.2:
                self.banner = None
        for w in self.shake:
            self.shake[w] = max(0.0, self.shake[w] - dt * 28)
            a = self.shake[w]
            self.lay.shift[w] = (int(a * math.sin(self.t * 70)), int(a * math.cos(self.t * 83)))
        s = self.session
        if self.screen_name != "game" or not s:
            return
        for pr in list(self.projectiles):
            if self.t - pr["t0"] >= pr["dur"]:
                self.projectiles.remove(pr)
                self._land(pr)
        self._smoke_timer -= dt
        if self._smoke_timer <= 0:
            self._smoke_timer = 0.14
            if isinstance(s, PvPSession):
                pairs = [("human", s.b1 if s.current_player == 1 else s.b2),
                         ("enemy", s.b2 if s.current_player == 1 else s.b1)]
            else:
                pairs = [("human", s.hb), ("enemy", s.eb)]
            for which, board in pairs:
                for nm in self._visible_sunk(board, which):
                    cx, cy = self.lay.cell_center(which, board.layout[nm][len(board.layout[nm]) // 2])
                    sprites.spawn_smoke(self.fx_rng, self.parts, cx, cy)
        if self.busy:
            return
        # HvAI only: AI reply / auto-play
        if not isinstance(s, PvPSession):
            if s.awaiting_ai:
                self._ai_timer -= dt
                if self._ai_timer <= 0:
                    s.ai_reply()
                    cell, res = s.last_ai
                    self._launch("ai", cell, res, s.log[-1])
            elif self.auto and not s.finished and not self.overlay:
                self._auto_timer -= dt
                if self._auto_timer <= 0:
                    self._auto_timer = AUTO_DELAY
                    self.ai_step()
        # PvP: show pass-the-device screen after shot lands
        if isinstance(s, PvPSession) and not s.finished and self.pvp_pass_timer > 0:
            self.pvp_pass_timer -= dt
            if self.pvp_pass_timer <= 0:
                self.pvp_pass_timer = 0.0
                self.overlay = "pvp_pass"

    def frame(self, dt, events):
        for e in events:
            self.handle_event(e)
        self.update(dt)
        self.draw()

    def run(self):
        while self.running:
            self.frame(min(self.clock.tick(60) / 1000.0, 0.05), pygame.event.get())
        pygame.quit()

    # ------------------------------------------------------------ drawing
    def draw(self):
        g = self.g
        g.buttons = []
        sprites.draw_sky(g, self.t)
        {"menu": self.draw_menu, "setup": self.draw_setup, "game": self.draw_game}[self.screen_name]()
        if self.overlay:
            g.buttons = []           # clicks should not bleed through to the screen behind
            g.dim(160)
            {"howto": self.draw_howto, "victory": self.draw_victory,
             "analysis": self.draw_analysis, "pvp_pass": self.draw_pvp_pass}[self.overlay]()
        sprites.draw_effects(g, [], [])
        for p in self.confetti:
            k = max(0.0, p["life"] / p["max"])
            pygame.draw.circle(g.screen, p["color"], (int(p["x"]), int(p["y"])), max(1, int(p["size"] * (0.5 + 0.5 * k))))
        pygame.display.flip()

    def pill_button(self, right, y, text, tag, fill=None):
        g = self.g
        w = g.pill(right, y, text, 14, fill=fill, right=True)
        g.buttons.append((pygame.Rect(int(right - w), int(y), int(w), 30), tag))
        return right - w - 12

    def draw_header(self, in_game=False):
        g, t = self.g, self.t
        x0 = 88
        g.rrect(x0, 28, 66, 66, shade(STATIC["accent"], 0.55), 18)
        g.rrect(x0, 22, 66, 66, STATIC["accent"], 18, shade(STATIC["accent"], 0.75), 3)
        sprites.draw_ship_icon(g, x0 + 33, 52, 17, t, bob=False)
        g.text(TITLE, 40, STATIC["accent"], x0 + 84, 14, True, shadow=True)
        mode_label = "PLAYER vs PLAYER" if self.game_mode == "pvp" else "BAYESIAN AI  ★  V1"
        g.pill(x0 + 86, 66, mode_label, 12, fill=STATIC["red"], color=(255, 255, 255), h=24)
        right = 1090
        right = self.pill_button(right, 30, "Menu" if in_game else "Quit", "menu" if in_game else "quit")
        right = self.pill_button(right, 30, "How to Play", "howto")
        self.pill_button(right, 30, ("DAY" if self.tod_target < 0.5 else "NIGHT") + " MODE  (D)", "tod")
        if in_game:
            s = self.session
            if isinstance(s, PvPSession):
                right2 = 1090
                g.pill(right2, 66, f"P{s.current_player}'s Turn", 13,
                       fill=STATIC["blue"] if s.current_player == 1 else STATIC["accent2"],
                       color=(255, 255, 255), right=True)
            else:
                hits = s.eb.count(HIT)
                acc = int(100 * hits / s.shots) if s.shots else 0
                right2 = 1090
                g.pill(right2 - 0, 66, f"Shots {s.shots}", 13, right=True)
                g.pill(right2 - 140, 66, f"Accuracy {acc}%", 13, right=True)

    # ------------------------------------------------------------ menu & setup
    def draw_menu(self):
        g, t = self.g, self.t
        y = 100 + math.sin(t * 2) * 5
        g.text("WAR", 60, STATIC["accent2"], W // 2, y - 20, True, True, shadow=True)
        g.text("BATTLESHIPS", 92, STATIC["accent"], W // 2, y + 40, True, True, shadow=True)
        # Four buttons: 2 play modes + howto + quit
        btn_w, btn_h = 360, 62
        bx = W // 2 - btn_w // 2
        g.button(bx, 294, btn_w, btn_h, "PLAY  (Human vs AI)", "play", "primary", size=20)
        g.button(bx, 370, btn_w, btn_h, "PLAYER vs PLAYER", "play_pvp", "good", size=20)
        g.button(bx, 446, btn_w, btn_h, "HOW TO PLAY", "howto", "normal", size=20)
        g.button(bx, 522, btn_w, btn_h, "QUIT", "quit", "danger", size=20)
        x = (t * 70) % (W + 500) - 250
        sprites.draw_ship_icon(g, x, 640 + math.sin(t * 2.4) * 4, 52, t)
        right = 1300
        self.pill_button(right, 30, ("DAY" if self.tod_target < 0.5 else "NIGHT") + " MODE  (D)", "tod")

    def draw_setup(self):
        g, L = self.g, self.lay
        self.draw_header()
        fleet_label = "YOUR FLEET" if self.game_mode == "hvai" else "PLAYER 1 FLEET"
        g.pill(76, 120, fleet_label, 14, fill=STATIC["blue"])
        sprites.draw_board_water(g, L, "human", self.t)
        for nm, cells in self.human_layout.items():
            sprites.draw_ship(g, L, "human", nm, cells, self.t)
        px = 508
        g.card(px, 150, 764, 450, "FLEET ARRANGEMENT")
        src = {"random": "Random", "manual": "Manual (example)", "dataset": f"Dataset #{self.dataset_ids[self.dataset_idx]}"}
        g.pill(px + 18, 184, f"Source: {src[self.fleet_mode]}", 14, fill=STATIC["good"], color=(10, 40, 20))
        g.button(px + 18, 236, 340, 54, "Randomize  (R)", "random", size=18)
        g.button(px + 18, 306, 340, 54, "Manual (example)", "manual", size=18)
        g.button(px + 18, 376, 340, 54, "Dataset  (click = next)", "dataset", size=18)
        g.text("SHIPS", 13, g.col("dim"), px + 420, 190, True)
        for i, (nm, ln) in enumerate(FLEET.items()):
            yy = 224 + i * 40
            hull = sprites.SHIP_COL[nm][0]
            for k in range(ln):
                g.rrect(px + 420 + k * 26, yy, 22, 24, hull, 6, shade(hull, 0.6), 2)
            g.text(f"{nm} ({ln})", 15, g.col("text"), px + 420 + 5 * 26 + 12, yy + 2, True)
        start_lbl = "START BATTLE" if self.game_mode == "hvai" else "START  P1 vs P2"
        g.button(px + 18, 500, 340, 66, start_lbl, "start", "primary", size=22)
        g.button(px + 396, 500, 200, 66, "< Menu", "menu", size=18)

    # ------------------------------------------------------------ game
    def view_shots(self, board, which):
        return {c: v for c, v in board.shots.items() if (which, c) not in self.hidden}

    def draw_game(self):
        s, g, L, t = self.session, self.g, self.lay, self.t
        is_pvp = isinstance(s, PvPSession)
        self.draw_header(True)

        if is_pvp:
            cp = s.current_player
            own_board   = s.b1 if cp == 1 else s.b2
            target_board = s.b2 if cp == 1 else s.b1
            g.pill(76, 120, f"PLAYER {cp}  FLEET", 14, fill=STATIC["blue"])
            g.pill(L.origin["enemy"][0] - 12, 120,
                   f"PLAYER {3 - cp}  RADAR", 14, fill=STATIC["red"], color=(255, 255, 255))
            # Left board = current player's own fleet
            sprites.draw_board_water(g, L, "human", t)
            for nm, cells in own_board.layout.items():
                sprites.draw_ship(g, L, "human", nm, cells, t, nm in own_board.sunk)
            sprites.draw_marks(g, L, "human", own_board.shots, t, self.hidden)
            # Right board = opponent's fleet (only sunk ships shown)
            sprites.draw_board_water(g, L, "enemy", t)
            vs_sunk = self._visible_sunk(target_board, "enemy")
            for nm, cells in target_board.layout.items():
                if nm in vs_sunk:
                    sprites.draw_ship(g, L, "enemy", nm, cells, t, True)
            sprites.draw_marks(g, L, "enemy", target_board.shots, t, self.hidden)
            # Hover on enemy board
            mx, my = pygame.mouse.get_pos()
            hover_cell = L.cell_at("enemy", (mx, my))
            if hover_cell and not self.busy and not s.finished and not self.overlay \
                    and hover_cell not in target_board.shots:
                sprites.draw_hover(g, L, "enemy", hover_cell, t)
        else:
            g.pill(76, 120, "YOUR FLEET", 14, fill=STATIC["blue"])
            g.pill(L.origin["enemy"][0] - 12, 120, "ENEMY RADAR", 14, fill=STATIC["red"], color=(255, 255, 255))
            for which, board in (("human", s.hb), ("enemy", s.eb)):
                sprites.draw_board_water(g, L, which, t)
                vs = self._visible_sunk(board, which)
                for nm, cells in board.layout.items():
                    if which == "human" or nm in vs:
                        sprites.draw_ship(g, L, which, nm, cells, t, nm in vs)
            if self.show_heat:
                sprites.draw_heat(g, L, "enemy", s.helper.probability())
            for which, board in (("human", s.hb), ("enemy", s.eb)):
                sprites.draw_marks(g, L, which, board.shots, t, self.hidden)
            mx, my = pygame.mouse.get_pos()
            cell = L.cell_at("enemy", (mx, my))
            if cell and not self.busy and not s.awaiting_ai and not s.finished and not self.overlay \
                    and cell not in s.eb.shots:
                sprites.draw_hover(g, L, "enemy", cell, t)
            if self.hint:
                sprites.draw_ring(g, L, "enemy", self.hint.cell, t)

        self.draw_panel()
        self.draw_status()
        for pr in self.projectiles:
            sprites.draw_projectile(g, pr, t)
        sprites.draw_effects(g, self.parts, self.rings)

        if is_pvp:
            if s.finished:
                txt = "Battle over."
            else:
                txt = f"Player {s.current_player}'s turn — click ENEMY RADAR to fire"
        else:
            if s.finished:
                txt = "Battle over."
            elif s.awaiting_ai or self.busy:
                txt = "AI is aiming..."
            else:
                txt = "Click a cell on ENEMY RADAR to fire  •  H AI hint  •  T auto-play"

        tw = g.text_size(txt, 16, True)[0] + 44
        g.rrect(W / 2 - tw / 2, H - 66, tw, 38, g.col("pill"), 19, g.col("edge"), 2)
        g.text(txt, 16, g.col("text"), W / 2, H - 58, True, True)
        if self.banner:
            self.draw_banner()

    def draw_banner(self):
        text, col, age = self.banner
        g = self.g
        alpha = min(1.0, (2.2 - age) / 0.4) if age > 1.8 else min(1.0, age / 0.3)
        bw = g.text_size(text, 36, True)[0] + 60
        bx, by = W // 2 - bw // 2, 280
        surf = pygame.Surface((int(bw), 56), pygame.SRCALPHA)
        pygame.draw.rect(surf, (*shade(col, 0.6), int(220 * alpha)), surf.get_rect(), border_radius=14)
        g.screen.blit(surf, (bx, by))
        pygame.draw.rect(g.screen, (*col, int(255 * alpha)),
                         pygame.Rect(int(bx), int(by), int(bw), 56), 3, border_radius=14)
        g.text(text, 36, (255, 255, 255), W // 2, by + 8, True, True, shadow=True)

    def draw_panel(self):
        s, g, L = self.session, self.g, self.lay
        is_pvp = isinstance(s, PvPSession)
        x, y, w, h = L.panel

        # ---- Fleet health card
        g.card(x, y, w, 100, "FLEET STATUS")
        for i, (nm, total) in enumerate(FLEET.items()):
            yy = y + 36 + i * 32
            if is_pvp:
                board = s.b1 if s.current_player == 1 else s.b2
            else:
                board = s.hb
            left = total - sum(1 for c in board.layout.get(nm, []) if board.shots.get(c) == HIT)
            col = STATIC["good"] if left == total else STATIC["warn"] if left > 0 else STATIC["bad"]
            g.text(nm[:10], 14, g.col("text"), x + 18, yy, True)
            g.bar(x + 90, yy + 2, w - 90 - 70, 16, left / total, col)
            g.text(f"{left}/{total}", 15, g.col("text"),
                   x + w - 18 - g.text_size(f"{left}/{total}", 15, True)[0], yy, True)

        # ---- Tools card (HvAI only)
        if not is_pvp:
            g.card(x, 262, w, 212, "TOOLS")
            tw2, th = (w - 36 - 12) // 2, 52
            off = s.finished
            tools = (("AI Hint",    "best shot",        "H", "hint",     STATIC["accent2"],    False),
                     ("AI Fire",    "1 step",           "A", "ai_step",  STATIC["blue"],       False),
                     ("Auto-play",  "AI plays for you", "T", "auto",     STATIC["good"],       self.auto),
                     ("Heatmap",    "probability map",  "M", "heat",     (170, 90, 230),       self.show_heat),
                     ("Analysis",   "Bayes vs Random",  "I", "analysis", (60, 170, 190),       False),
                     ("Restart",    "start over",       "R", "restart",  STATIC["red"],        False))
            for i, (title, sub, key, tag, col, active) in enumerate(tools):
                g.tool(x + 18 + (i % 2) * (tw2 + 12), 262 + 36 + (i // 2) * 58,
                       tw2, th, title, sub, key, tag, col, active,
                       enabled=not off or tag in ("analysis", "restart"))
        else:
            g.card(x, 262, w, 86, "TOOLS")
            g.tool(x + 18, 298, w - 36, 46, "Restart", "start over", "R", "restart", STATIC["red"])

        # ---- Battle log card
        g.card(x, 486, w, 164, "BATTLE LOG")
        if not is_pvp and self.hint:
            yy = g.paragraph(f"Hint: {self.hint.text} ({self.hint.percent:.1f}%)", 14,
                              STATIC["warn"], x + 18, 514, w - 36, 2, True)
            g.paragraph(self.hint.why[0] if self.hint.why else "", 12, g.col("dim"),
                        x + 18, yy + 2, w - 36, 2)
        else:
            for i, (who, text, result) in enumerate(self.log_view[-4:]):
                yy = 512 + i * 32
                col = STATIC["good"] if result != MISS else g.col("dim")
                g.rrect(x + 16, yy, w - 32, 27, g.col("pill"), 8)
                g.rrect(x + 16, yy, 5, 27, col, 3)
                g.text(text[:46], 12, g.col("text"), x + 30, yy + 6, True)

    def draw_status(self):
        s, g, L = self.session, self.g, self.lay
        is_pvp = isinstance(s, PvPSession)
        if is_pvp:
            cp = s.current_player
            pairs = [("human", s.b1 if cp == 1 else s.b2),
                     ("enemy", s.b2 if cp == 1 else s.b1)]
        else:
            pairs = [("human", s.hb), ("enemy", s.eb)]

        for which, board in pairs:
            x, y, _, h = L.board_rect(which)
            vs = self.view_shots(board, which)
            kena = sum(1 for v in vs.values() if v == HIT)
            g.text(f"Hit {kena}  •  Miss {len(vs) - kena}  •  Sunk {len(self._visible_sunk(board, which))}/{len(FLEET)}",
                   14, g.col("text"), x - 10, y + h + 24, True)
            sunk = self._visible_sunk(board, which)
            for i, nm in enumerate(FLEET):
                alive = nm not in sunk
                cx = x - 4 + i * 82
                pygame.draw.circle(g.screen, sprites.SHIP_COL[nm][0] if alive else (88, 96, 112),
                                   (int(cx), int(y + h + 58)), 6)
                g.text(nm, 11, g.col("text") if alive else g.col("dim"), cx + 11, y + h + 51, True)

    # ------------------------------------------------------------ modals
    def _modal(self, title, h):
        g = self.g
        g.card(W // 2 - 460, 130, 920, h)
        g.text(title, 40, STATIC["accent"], W // 2, 146, True, True, shadow=True)

    def draw_howto(self):
        self._modal("HOW TO PLAY", 470)
        y = 220
        lines = HOWTO_PVP if self.game_mode == "pvp" else HOWTO
        for line in lines:
            y = self.g.paragraph(line, 18, self.g.col("text"), W // 2 - 420, y, 840, 3, True) + 10
        self.g.button(W // 2 - 100, 130 + 470 - 84, 200, 56, "Close", "close", "primary")

    def draw_pvp_pass(self):
        """Pass-the-device screen shown between PvP turns."""
        s, g = self.session, self.g
        cp = s.current_player   # player who is NEXT to play
        g.card(W // 2 - 320, H // 2 - 170, 640, 340)
        g.text("*** PASS THE DEVICE ***", 30, STATIC["accent"], W // 2, H // 2 - 150, True, True, shadow=True)
        g.text(f"Player {cp}'s Turn", 34, STATIC["accent2"], W // 2, H // 2 - 96, True, True)
        g.text(f"Hand the device to Player {cp}.", 20, g.col("text"), W // 2, H // 2 - 42, True, True)
        g.text("(Boards are hidden — do not peek!)", 15, g.col("dim"), W // 2, H // 2 - 10, True, True)
        g.button(W // 2 - 150, H // 2 + 50, 300, 60, f"I'm Player {cp}  — Ready!", "pass_ok", "primary", size=19)

    def draw_victory(self):
        s, g = self.session, self.g
        is_pvp = isinstance(s, PvPSession)
        if is_pvp:
            title = f"PLAYER {s.winner} WINS!"
        else:
            title = "YOU WIN!" if s.winner == "ANDA" else "AI WINS!"
        self._modal(title, 340)
        if is_pvp:
            g.text(f"Player 1 shots: {s.shots_p1}   |   Player 2 shots: {s.shots_p2}",
                   20, g.col("text"), W // 2, 230, True, True)
        else:
            g.text(f"Your shots: {s.shots}   |   AI assistance used: {'yes' if s.used_ai else 'no'}",
                   20, g.col("text"), W // 2, 230, True, True)
        g.text(s.log[-1][:80], 15, g.col("dim"), W // 2, 275, True, True)
        g.button(W // 2 - 270, 340, 250, 60, "Play Again", "restart", "primary", size=20)
        g.button(W // 2 + 20, 340, 250, 60, "Menu", "menu", size=20)

    def draw_analysis(self):
        a, g = self.analysis, self.g
        self._modal("AI ANALYSIS", 470)
        y = 210
        g.text("Bayesian vs Random on YOUR fleet (actually executed):", 16, g.col("dim"), W // 2 - 420, y, True)
        y += 34
        for r in a["rows"]:
            g.text(f"{r['algo']:<8} shots: {r['shots']:>3}   time: {r['time_ms']:.1f} ms   valid: {r['valid']}",
                   18, g.col("text"), W // 2 - 400, y, True)
            y += 30
        if a["hint"]:
            y += 14
            for line in a["hint"].lines():
                y = g.paragraph(line, 15,
                                 STATIC["warn"] if line.startswith("Saran") else g.col("text"),
                                 W // 2 - 420, y, 840, 2, True) + 4
            g.text("Top-5: " + ", ".join(f"{n} {p:.1f}%" for n, p in a["hint"].top),
                   15, g.col("dim"), W // 2 - 420, y + 6, True)
        g.button(W // 2 - 100, 130 + 470 - 84, 200, 56, "Close", "close", "primary")
