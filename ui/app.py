"""ui/app.py - game WAR BATTLESHIPS (Pygame): menu, penempatan armada, pertempuran Human vs AI.
Tema: laut kartun bergelombang, mode SIANG/MALAM (tekan D), peluru melengkung, ledakan, percikan, asap kapal tenggelam.
Semua logika permainan ada di ui/session.py; file ini hanya menggambar dan menerima input."""
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

TITLE = "WAR BATTLESHIPS"
AI_DELAY, AUTO_DELAY, FLIGHT = 0.4, 0.4, 0.5
HOWTO = [
    "Tujuan: tenggelamkan seluruh kapal lawan sebelum seluruh kapal Anda ditenggelamkan.",
    "Klik sel di RADAR LAWAN (kanan) untuk menembak. AI membalas menembak papan Anda (kiri).",
    "Api = KENA, riak air = MELESET. Kapal lawan baru terlihat ketika tenggelam.",
    "H = saran tembakan Bayesian AI (lengkap dengan alasannya).   A = AI menembak untuk Anda.",
    "T = auto-play.   M = peta probabilitas AI di radar.   I = AI Analysis.",
    "D = ganti mode SIANG / MALAM.   R = acak ulang / mulai ulang.   Esc = kembali.",
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
        self.tod, self.tod_target = 0.0, 0.0          # 0 siang -> 1 malam
        self.screen_name = "menu"
        self.layouts_path = layouts_path or DEFAULT_PATH
        ensure_dataset(self.layouts_path)
        self.dataset_ids = sorted(load_dataset(self.layouts_path))
        self.dataset_idx = self.dataset_ids.index(dataset_id) if dataset_id in self.dataset_ids else 0
        self.fleet_mode = fleet_mode
        self.human_layout = self._make_layout(fleet_mode)
        self.session = None
        self.overlay = None                  # None | howto | victory | analysis
        self.analysis = None
        self._reset_battle()

    def _reset_battle(self):
        self.hint, self.show_heat, self.auto = None, False, False
        self.parts, self.rings, self.projectiles, self.confetti = [], [], [], []
        self.hidden = set()                  # (papan, sel) yang pelurunya belum mendarat
        self.banner = None
        self.msg = "Giliran Anda: klik papan radar untuk menembak."
        self.log_view = []
        self.shake = {"human": 0.0, "enemy": 0.0}
        self._ai_timer = self._auto_timer = self._smoke_timer = 0.0

    # ------------------------------------------------------------ armada
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

    def start_game(self):
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
        {"play": lambda: setattr(self, "screen_name", "setup"),
         "howto": lambda: setattr(self, "overlay", "howto"),
         "quit": lambda: setattr(self, "running", False),
         "menu": lambda: (setattr(self, "screen_name", "menu"), setattr(self, "auto", False), setattr(self, "overlay", None)),
         "random": lambda: self.set_fleet("random"), "manual": lambda: self.set_fleet("manual"),
         "dataset": lambda: self.set_fleet("dataset"), "start": self.start_game, "restart": self.start_game,
         "hint": self.ask_hint, "ai_step": self.ai_step, "auto": self.toggle_auto, "heat": self.toggle_heat,
         "analysis": self.toggle_analysis, "tod": self.toggle_tod,
         "close": lambda: setattr(self, "overlay", None)}[tag]()

    # ------------------------------------------------------------ aksi game
    @property
    def busy(self):
        return bool(self.projectiles)

    def toggle_tod(self):
        self.tod_target = 0.0 if self.tod_target >= 0.5 else 1.0

    def shoot(self, cell):
        s = self.session
        if s is None or s.finished or s.awaiting_ai or self.busy or self.overlay:
            return
        if s.human_fire(cell):
            self.hint = None
            self._launch("human", cell, s.last_human[1], s.log[-1])
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
        else:
            sprites.spawn_explosion(self.fx_rng, self.parts, self.rings, x, y, big=res.is_sunk)
            self.shake[pr["which"]] = 9.0 if res.is_sunk else 6.0
        if res.is_sunk:
            self.banner = [f"{res.ship.upper()} TENGGELAM!", STATIC["good"] if pr["shooter"] == "human" else STATIC["bad"], 0.0]
        self.msg = pr["text"]
        self.log_view = (self.log_view + [(pr["shooter"], pr["text"], res.result)])[-30:]
        if self.session.finished:
            self._on_end()
        elif pr["shooter"] == "human":
            self._ai_timer = AI_DELAY

    def ask_hint(self):
        if self.session and not self.session.finished:
            self.hint = self.session.hint()

    def ai_step(self):
        s = self.session
        if s and not s.finished and not s.awaiting_ai and not self.busy:
            self.shoot(s.helper.choose())

    def toggle_auto(self):
        self.auto = not self.auto

    def toggle_heat(self):
        self.show_heat = not self.show_heat

    def toggle_analysis(self):
        if not self.session:
            return
        if self.overlay == "analysis":
            self.overlay = None
            return
        self.analysis = {"rows": [run_algorithm(self.session.human_layout, a, seed=1) for a in ("Bayes", "Random")],
                         "hint": self.session.hint() if not self.session.finished else None}
        self.overlay = "analysis"

    def _on_end(self):
        self.overlay, self.auto = "victory", False
        if self.session.winner == "ANDA":
            for _ in range(90):
                r = self.fx_rng
                self.confetti.append({"x": r.uniform(0, W), "y": r.uniform(-120, -10), "vx": r.uniform(-30, 30), "vy": r.uniform(70, 190),
                                      "life": r.uniform(3, 5), "max": 5, "grav": 20, "kind": "drop", "size": r.uniform(3, 6),
                                      "color": r.choice([STATIC["accent"], STATIC["good"], STATIC["red"], (110, 200, 255), (255, 255, 255)])})

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
            for which, board in (("human", s.hb), ("enemy", s.eb)):
                for nm in self._visible_sunk(board, which):
                    cx, cy = self.lay.cell_center(which, board.layout[nm][len(board.layout[nm]) // 2])
                    sprites.spawn_smoke(self.fx_rng, self.parts, cx, cy)
        if self.busy:
            return
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

    def frame(self, dt, events):
        for e in events:
            self.handle_event(e)
        self.update(dt)
        self.draw()

    def run(self):
        while self.running:
            self.frame(min(self.clock.tick(60) / 1000.0, 0.05), pygame.event.get())
        pygame.quit()

    # ------------------------------------------------------------ gambar umum
    def draw(self):
        g = self.g
        g.buttons = []
        sprites.draw_sky(g, self.t)
        {"menu": self.draw_menu, "setup": self.draw_setup, "game": self.draw_game}[self.screen_name]()
        if self.overlay:
            g.buttons = []                    # klik tidak boleh tembus ke layar di belakang overlay
            g.dim(150)
            {"howto": self.draw_howto, "victory": self.draw_victory, "analysis": self.draw_analysis}[self.overlay]()
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
        g.pill(x0 + 86, 66, "BAYESIAN AI  ·  V1", 12, fill=STATIC["red"], color=(255, 255, 255), h=24)
        right = 1090
        right = self.pill_button(right, 30, "Menu" if in_game else "Keluar", "menu" if in_game else "quit")
        right = self.pill_button(right, 30, "Aturan main", "howto")
        self.pill_button(right, 30, "MODE " + ("SIANG" if self.tod_target < 0.5 else "MALAM") + "  (D)", "tod")
        if in_game:
            s = self.session
            hits = s.eb.count(HIT)
            acc = int(100 * hits / s.shots) if s.shots else 0
            right = 1090
            g.pill(right - 0, 66, f"Tembakan {s.shots}", 13, right=True)
            g.pill(right - 140, 66, f"Akurasi {acc}%", 13, right=True)

    # ------------------------------------------------------------ menu & setup
    def draw_menu(self):
        g, t = self.g, self.t
        y = 110 + math.sin(t * 2) * 5
        g.text("WAR", 60, STATIC["accent2"], W // 2, y - 20, True, True, shadow=True)
        g.text("BATTLESHIPS", 92, STATIC["accent"], W // 2, y + 40, True, True, shadow=True)
        g.pill(W // 2 - 130, y + 150, "MELAWAN BAYESIAN AI", 15, fill=STATIC["red"], color=(255, 255, 255))
        for i, (lbl, tag, st) in enumerate((("MAIN  (Human vs AI)", "play", "primary"), ("CARA MAIN", "howto", "normal"),
                                            ("KELUAR", "quit", "danger"))):
            g.button(W // 2 - 170, 330 + i * 86, 340, 62, lbl, tag, st, size=22)
        x = (t * 70) % (W + 500) - 250
        sprites.draw_ship_icon(g, x, 640 + math.sin(t * 2.4) * 4, 52, t)
        right = 1300
        self.pill_button(right, 30, "MODE " + ("SIANG" if self.tod_target < 0.5 else "MALAM") + "  (D)", "tod")

    def draw_setup(self):
        g, L = self.g, self.lay
        self.draw_header()
        g.pill(76, 120, "ARMADA ANDA", 14, fill=STATIC["blue"])
        sprites.draw_board_water(g, L, "human", self.t)
        for nm, cells in self.human_layout.items():
            sprites.draw_ship(g, L, "human", nm, cells, self.t)
        px = 508
        g.card(px, 150, 764, 450, "SUSUN ARMADA")
        src = {"random": "Acak", "manual": "Manual (contoh)", "dataset": f"Dataset #{self.dataset_ids[self.dataset_idx]}"}
        g.pill(px + 18, 184, f"Sumber: {src[self.fleet_mode]}", 14, fill=STATIC["good"], color=(10, 40, 20))
        g.button(px + 18, 236, 340, 54, "Acak ulang  (R)", "random", size=18)
        g.button(px + 18, 306, 340, 54, "Manual (contoh)", "manual", size=18)
        g.button(px + 18, 376, 340, 54, "Dataset  (klik = berikutnya)", "dataset", size=18)
        g.text("KAPAL", 13, g.col("dim"), px + 420, 190, True)
        for i, (nm, ln) in enumerate(FLEET.items()):
            yy = 224 + i * 40
            hull = sprites.SHIP_COL[nm][0]
            for k in range(ln):
                g.rrect(px + 420 + k * 26, yy, 22, 24, hull, 6, shade(hull, 0.6), 2)
            g.text(f"{nm} ({ln})", 15, g.col("text"), px + 420 + 5 * 26 + 12, yy + 2, True)
        g.button(px + 18, 500, 340, 66, "MULAI PERTEMPURAN", "start", "primary", size=22)
        g.button(px + 396, 500, 200, 66, "< Menu", "menu", size=18)

    # ------------------------------------------------------------ game
    def view_shots(self, board, which):
        return {c: v for c, v in board.shots.items() if (which, c) not in self.hidden}

    def draw_game(self):
        s, g, L, t = self.session, self.g, self.lay, self.t
        self.draw_header(True)
        g.pill(76, 120, "ARMADA ANDA", 14, fill=STATIC["blue"])
        g.pill(L.origin["enemy"][0] - 12, 120, "RADAR LAWAN", 14, fill=STATIC["red"], color=(255, 255, 255))
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
        txt = ("Pertempuran selesai." if s.finished else "AI sedang membidik..." if (s.awaiting_ai or self.busy)
               else "Klik sel di RADAR LAWAN untuk menembak  ·  H saran AI  ·  T auto-play")
        w = g.text_size(txt, 16, True)[0] + 44
        g.rrect(W / 2 - w / 2, H - 66, w, 38, g.col("pill"), 19, g.col("edge"), 2)
        g.text(txt, 16, g.col("text"), W / 2, H - 58, True, True)
        if self.banner:
            self.draw_banner()

    def draw_banner(self):
        g = self.g
        text, col, age = self.banner
        k = min(1.0, age / 0.25)
        size = int(30 + 26 * (1 - (1 - k) ** 3) + (6 * math.sin(age * 6) if age > 0.25 else 0))
        fade = 1.0 if age < 1.6 else max(0.0, (2.2 - age) / 0.6)
        y = 330 - 20 * (1 - k)
        w = g.text_size(text, size, True)[0] + 60
        g.rrect(W / 2 - w / 2, y - 6, w, size + 28, mix(g.col("pill"), (0, 0, 0), 1 - fade), 24, mix(col, (0, 0, 0), 1 - fade), 4)
        g.text(text, size, mix(col, (0, 0, 0), 1 - fade), W / 2, y + 6, True, True, shadow=True)

    def draw_panel(self):
        s, g = self.session, self.g
        x, _, w, _ = self.lay.panel
        g.card(x, 146, w, 104, "ARMADA")
        for i, (lbl, board, col) in enumerate((("ANDA", s.hb, STATIC["good"]), ("LAWAN", s.eb, STATIC["red"]))):
            total = sum(FLEET.values())
            hits = sum(1 for c in board.owner if c in self.view_shots(board, "human" if board is s.hb else "enemy")
                       and board.shots.get(c) == HIT)
            left = total - hits
            yy = 178 + i * 32
            g.text(lbl, 14, g.col("text"), x + 18, yy, True)
            g.bar(x + 90, yy + 2, w - 90 - 70, 16, left / total, col)
            g.text(f"{left}/{total}", 15, g.col("text"), x + w - 18 - g.text_size(f"{left}/{total}", 15, True)[0], yy, True)
        g.card(x, 262, w, 212, "PERALATAN")
        tw, th = (w - 36 - 12) // 2, 52
        off = s.finished
        tools = (("Saran AI", "tembakan terbaik", "H", "hint", STATIC["accent2"], False),
                 ("AI Tembak", "1 langkah", "A", "ai_step", STATIC["blue"], False),
                 ("Auto-play", "AI main sendiri", "T", "auto", STATIC["good"], self.auto),
                 ("Heatmap", "peta probabilitas", "M", "heat", (170, 90, 230), self.show_heat),
                 ("Analisis", "Bayes vs Random", "I", "analysis", (60, 170, 190), False),
                 ("Ulang", "mulai lagi", "R", "restart", STATIC["red"], False))
        for i, (title, sub, key, tag, col, active) in enumerate(tools):
            g.tool(x + 18 + (i % 2) * (tw + 12), 262 + 36 + (i // 2) * 58, tw, th, title, sub, key, tag, col, active,
                   enabled=not off or tag in ("analysis", "restart"))
        g.card(x, 486, w, 164, "CATATAN PERTEMPURAN")
        if self.hint:
            yy = g.paragraph(f"Saran: {self.hint.text} ({self.hint.percent:.1f}%)", 14, STATIC["warn"], x + 18, 514, w - 36, 2, True)
            g.paragraph(self.hint.why[0] if self.hint.why else "", 12, g.col("dim"), x + 18, yy + 2, w - 36, 2)
        else:
            for i, (who, text, result) in enumerate(self.log_view[-4:]):
                yy = 512 + i * 32
                col = STATIC["good"] if (who == "human") == (result != MISS) else STATIC["bad"] if who == "ai" and result != MISS else g.col("dim")
                g.rrect(x + 16, yy, w - 32, 27, g.col("pill"), 8)
                g.rrect(x + 16, yy, 5, 27, col, 3)
                g.text(text[:46], 12, g.col("text"), x + 30, yy + 6, True)

    def draw_status(self):
        s, g, L = self.session, self.g, self.lay
        for which, board in (("human", s.hb), ("enemy", s.eb)):
            x, y, _, h = L.board_rect(which)
            vs = self.view_shots(board, which)
            kena = sum(1 for v in vs.values() if v == HIT)
            g.text(f"Kena {kena}   ·   Meleset {len(vs) - kena}   ·   Tenggelam {len(self._visible_sunk(board, which))}/{len(FLEET)}",
                   14, g.col("text"), x - 10, y + h + 24, True)
            sunk = self._visible_sunk(board, which)
            for i, nm in enumerate(FLEET):
                alive = nm not in sunk
                cx = x - 4 + i * 82
                pygame.draw.circle(g.screen, sprites.SHIP_COL[nm][0] if alive else (88, 96, 112), (int(cx), int(y + h + 58)), 6)
                g.text(nm, 11, g.col("text") if alive else g.col("dim"), cx + 11, y + h + 51, True)

    # ------------------------------------------------------------ modal
    def _modal(self, title, h):
        g = self.g
        g.card(W // 2 - 460, 130, 920, h)
        g.text(title, 40, STATIC["accent"], W // 2, 146, True, True, shadow=True)

    def draw_howto(self):
        self._modal("CARA MAIN", 470)
        y = 220
        for line in HOWTO:
            y = self.g.paragraph(line, 18, self.g.col("text"), W // 2 - 420, y, 840, 3, True) + 10
        self.g.button(W // 2 - 100, 130 + 470 - 84, 200, 56, "Tutup", "close", "primary")

    def draw_victory(self):
        s, g = self.session, self.g
        win = s.winner == "ANDA"
        self._modal("ANDA MENANG!" if win else "AI MENANG", 340)
        g.text(f"Tembakan Anda: {s.shots}   |   Bantuan AI dipakai: {'ya' if s.used_ai else 'tidak'}",
               20, g.col("text"), W // 2, 230, True, True)
        g.text(s.log[-1][:80], 15, g.col("dim"), W // 2, 275, True, True)
        g.button(W // 2 - 270, 340, 250, 60, "Main Lagi", "restart", "primary", size=20)
        g.button(W // 2 + 20, 340, 250, 60, "Menu", "menu", size=20)

    def draw_analysis(self):
        a, g = self.analysis, self.g
        self._modal("AI ANALYSIS", 470)
        y = 210
        g.text("Bayesian vs Random pada armada ANDA (dijalankan sungguhan):", 16, g.col("dim"), W // 2 - 420, y, True)
        y += 34
        for r in a["rows"]:
            g.text(f"{r['algo']:<8} tembakan: {r['shots']:>3}   waktu: {r['time_ms']:.1f} ms   valid: {r['valid']}",
                   18, g.col("text"), W // 2 - 400, y, True)
            y += 30
        if a["hint"]:
            y += 14
            for line in a["hint"].lines():
                y = g.paragraph(line, 15, STATIC["warn"] if line.startswith("Saran") else g.col("text"), W // 2 - 420, y, 840, 2, True) + 4
            g.text("Top-5: " + ", ".join(f"{n} {p:.1f}%" for n, p in a["hint"].top), 15, g.col("dim"), W // 2 - 420, y + 6, True)
        g.button(W // 2 - 100, 130 + 470 - 84, 200, 56, "Tutup", "close", "primary")
