"""ui/sprites.py - gambar elemen visual: langit siang/malam, laut bergelombang, kapal kartun, api, riak,
proyektil dan partikel. Semua koordinat dikonversi ke int (pygame 2 butuh titik integer)."""
import math
import random

import pygame

from core.state import N
from ui.gfx import STATIC, mix, shade
from ui.layout import HORIZON, W, H

_rng = random.Random(5)
STARS = [(_rng.randrange(0, W), _rng.randrange(8, HORIZON - 30), _rng.random() * 6.28) for _ in range(70)]
CLOUDS = [(120, 70, 1.0, 9), (520, 140, 0.8, 6), (900, 60, 1.2, 11), (1180, 190, 0.9, 7), (300, 250, 0.7, 5)]
CELESTIAL = (1190, 235, 170)          # pusat orbit dan jari-jari matahari/bulan

SHIP_COL = {"Carrier": ((110, 134, 170), (198, 214, 236)), "Battleship": ((200, 66, 70), (244, 176, 156)),
            "Cruiser": ((232, 140, 48), (252, 208, 142)), "Submarine": ((236, 196, 58), (255, 236, 150)),
            "Destroyer": ((62, 168, 118), (170, 232, 204))}


def P(x, y):
    return (int(x), int(y))


def sky_at(g, y):
    return mix(g.col("sky1"), g.col("sky2"), y / HORIZON)


# ================================================================== latar
def draw_sky(g, t):
    bands = 28
    for i in range(bands):
        y0 = i * HORIZON // bands
        pygame.draw.rect(g.screen, mix(g.col("sky1"), g.col("sky2"), i / bands),
                         pygame.Rect(0, y0, W, HORIZON // bands + 2))
    # bintang (malam)
    for x, y, ph in STARS:
        b = g.tod * (0.55 + 0.45 * math.sin(t * 2 + ph))
        if b > 0.12:
            c = mix(sky_at(g, y), (255, 255, 255), b)
            pygame.draw.circle(g.screen, c, P(x, y), 2 if b > 0.6 else 1)
    # awan (siang)
    for cx, cy, sc, sp in CLOUDS:
        x = (cx + t * sp) % (W + 300) - 150
        c = mix((255, 255, 255), (70, 82, 128), g.tod)
        c = mix(c, sky_at(g, cy), 0.25 + 0.4 * g.tod)
        for dx, dy, r in ((0, 0, 26), (30, -10, 32), (62, 0, 26), (30, 8, 28)):
            pygame.draw.circle(g.screen, c, P(x + dx * sc, cy + dy * sc), int(r * sc))
    draw_celestials(g, t)
    draw_sea(g, t)


def draw_celestials(g, t):
    cx, cy, r = CELESTIAL
    a = g.tod * math.pi
    sx, sy = cx + r * math.sin(a), cy - r * math.cos(a)               # matahari
    mx, my = cx + r * math.sin(a + math.pi), cy - r * math.cos(a + math.pi)   # bulan
    sky = sky_at(g, min(sy, HORIZON))
    for rad, k in ((70, .12), (56, .22), (44, .4)):
        pygame.draw.circle(g.screen, mix(sky, (255, 214, 90), k), P(sx, sy), rad)
    for i in range(12):
        ang = t * 0.4 + i * math.pi / 6
        pygame.draw.line(g.screen, (255, 214, 90), P(sx + 36 * math.cos(ang), sy + 36 * math.sin(ang)),
                         P(sx + 52 * math.cos(ang), sy + 52 * math.sin(ang)), 3)
    pygame.draw.circle(g.screen, (255, 232, 120), P(sx, sy), 32)
    pygame.draw.circle(g.screen, (255, 248, 190), P(sx, sy), 24)
    sky = sky_at(g, min(max(my, 0), HORIZON))
    for rad, k in ((66, .1), (52, .2), (42, .35)):
        pygame.draw.circle(g.screen, mix(sky, (190, 205, 255), k), P(mx, my), rad)
    pygame.draw.circle(g.screen, (244, 246, 255), P(mx, my), 30)
    for dx, dy, rr in ((-9, -7, 6), (8, 5, 8), (-4, 12, 4)):
        pygame.draw.circle(g.screen, (214, 220, 238), P(mx + dx, my + dy), rr)


def wave_points(x0, x1, base, amp, length, speed, t, step=24):
    pts = []
    x = x0
    while x <= x1:
        pts.append((x, base + amp * math.sin(x / length + t * speed)))
        x += step
    pts.append((x1, base + amp * math.sin(x1 / length + t * speed)))
    return pts


def draw_sea(g, t):
    bands = 14
    for i in range(bands):
        y0 = HORIZON + i * (H - HORIZON) // bands
        pygame.draw.rect(g.screen, mix(g.col("sea1"), g.col("sea2"), i / bands),
                         pygame.Rect(0, y0, W, (H - HORIZON) // bands + 2))
    # perahu layar kecil di cakrawala
    bx = (t * 22) % (W + 200) - 100
    by = HORIZON + 4 + math.sin(t * 2) * 1.5
    pygame.draw.polygon(g.screen, shade(g.col("ink"), 1.4), [P(bx - 14, by), P(bx + 14, by), P(bx + 9, by + 6), P(bx - 9, by + 6)])
    pygame.draw.polygon(g.screen, mix((255, 255, 255), (150, 160, 200), g.tod), [P(bx, by - 2), P(bx, by - 22), P(bx + 12, by - 2)])
    for i in range(4):
        base = HORIZON + 30 + i * 75
        pts = wave_points(0, W, base, 7 + i * 2, 70 + i * 25, 1.1 + i * 0.25, t + i * 2)
        poly = pts + [(W, H), (0, H)]
        col = mix(g.col("sea1"), g.col("sea2"), 0.25 + i * 0.22)
        pygame.draw.polygon(g.screen, col, [P(x, y) for x, y in poly])
        pygame.draw.lines(g.screen, mix(col, g.col("crest"), 0.45), False, [P(x, y) for x, y in pts], 3)


def draw_sea_surface(g, rect, t, phase=0.0):
    """Permukaan laut di dalam papan: gradien kedalaman + gelombang bergerak + kilau."""
    x0, y0, w, h = rect
    rows = 20
    for i in range(rows):
        pygame.draw.rect(g.screen, mix(g.col("shallow"), g.col("deep"), i / (rows - 1)),
                         pygame.Rect(int(x0), int(y0 + i * h / rows), int(w), int(h / rows) + 1))
    for i in range(7):
        base = y0 + (i + 0.5) * h / 7
        pts = wave_points(x0, x0 + w, base, 4.5, 26 + i * 3, 1.6 + i * 0.1, t + phase + i, step=14)
        pts = [(x, min(max(y, y0 + 2), y0 + h - 2)) for x, y in pts]
        col = mix(g.col("deep"), g.col("wave"), 0.22 + 0.04 * (i % 3))
        pygame.draw.lines(g.screen, col, False, [P(x, y) for x, y in pts], 2)
    for i in range(14):                                               # kilau cahaya di permukaan
        sx = x0 + (i * 53 + t * 18 * (1 + i % 3)) % w
        sy = y0 + (i * 37) % h
        if math.sin(t * 3 + i) > 0.35:
            pygame.draw.line(g.screen, g.col("wave"), P(sx, sy), P(sx + 6, sy), 2)


def draw_frame(g, rect):
    """Bingkai tebal papan (gaya referensi): sisi bawah gelap, tepi terang, bagian dalam gelap."""
    x, y, w, h = rect
    g.rrect(x - 26, y - 22, w + 38, h + 44, shade(g.col("frame"), 0.55), 26)
    g.rrect(x - 26, y - 28, w + 38, h + 44, g.col("frame"), 26)
    g.rrect(x - 14, y - 16, w + 14, h + 20, g.col("frame_in"), 18)


def draw_grid(g, lay, which):
    x0, y0, w, h = lay.board_rect(which)
    c = mix(g.col("deep"), g.col("wave"), 0.3)
    for i in range(N + 1):
        pygame.draw.line(g.screen, c, P(x0 + i * lay.cell, y0), P(x0 + i * lay.cell, y0 + h), 1)
        pygame.draw.line(g.screen, c, P(x0, y0 + i * lay.cell), P(x0 + w, y0 + i * lay.cell), 1)
    for i in range(N):
        g.text("ABCDEFGHIJ"[i], 14, g.col("text"), x0 + i * lay.cell + lay.cell / 2, y0 - 25, True, True)
        g.text(str(i + 1), 14, g.col("text"), x0 - 14, y0 + i * lay.cell + lay.cell / 2 - 9, True, True)


def draw_board_water(g, lay, which, t):
    rect = lay.board_rect(which)
    draw_frame(g, rect)
    draw_sea_surface(g, rect, t, 0.0 if which == "human" else 1.7)
    draw_grid(g, lay, which)


# ================================================================== kapal
def draw_ship(g, lay, which, name, cells, t, sunk=False):
    s = lay.cell
    rs = [lay.cell_rect(which, c) for c in cells]
    x0, y0 = min(r[0] for r in rs), min(r[1] for r in rs)
    L = len(cells)
    horiz = len({c[0] for c in cells}) == 1
    ph = sum(cells[0]) * 0.7
    bob = (2.2 if not sunk else 0.8) * math.sin(t * 2.2 + ph) + (4 if sunk else 0)

    def m(u, v):
        return P(x0 + u * s, y0 + v * s + bob) if horiz else P(x0 + v * s, y0 + u * s + bob)

    def poly(pts, col, w=0):
        pygame.draw.polygon(g.screen, col, [m(u, v) for u, v in pts], w)

    hull, deck = SHIP_COL.get(name, ((150, 150, 160), (210, 210, 220)))
    cabin = (245, 245, 250)
    if sunk:
        hull, deck, cabin = (64, 44, 56), (96, 68, 78), (110, 100, 112)
    else:                                                             # buih haluan/buritan
        for k, v in enumerate((0.34, 0.66)):
            wob = 0.06 * math.sin(t * 5 + k)
            pygame.draw.line(g.screen, g.col("crest"), m(0.05, v), m(-0.28 + wob, v + (0.04 if k else -0.04)), 3)
    poly([(0.08, 0.2), (L - 0.5, 0.2), (L - 0.06, 0.5), (L - 0.5, 0.8), (0.08, 0.8)], shade(hull, 0.62))   # bayangan lambung
    poly([(0.08, 0.16), (L - 0.5, 0.16), (L - 0.06, 0.46), (L - 0.5, 0.76), (0.08, 0.76)], hull)
    poly([(0.2, 0.28), (L - 0.58, 0.28), (L - 0.28, 0.46), (L - 0.58, 0.64), (0.2, 0.64)], deck)
    cu = max(0.5, L * 0.28)
    poly([(cu, 0.3), (cu + 0.7, 0.3), (cu + 0.7, 0.62), (cu, 0.62)], cabin)
    pygame.draw.circle(g.screen, shade(hull, 0.5), m(cu + 0.35, 0.46), max(2, int(s * 0.09)))
    if L >= 4:
        poly([(cu + 1.0, 0.33), (cu + 1.5, 0.33), (cu + 1.5, 0.59), (cu + 1.0, 0.59)], cabin)
    fx = m(0.45, 0.46)
    pygame.draw.circle(g.screen, shade(hull, 0.45), fx, max(3, int(s * 0.15)))
    pygame.draw.circle(g.screen, (255, 255, 255) if not sunk else (120, 120, 130), m(L - 0.85, 0.46), max(2, int(s * 0.08)))


def draw_ship_icon(g, cx, cy, sc, t, hull=(226, 70, 90), bob=True):
    """Kapal kartun besar (menu, lencana judul)."""
    cy += math.sin(t * 2) * sc * 0.08 if bob else 0

    def pl(pts, col):
        pygame.draw.polygon(g.screen, col, [P(cx + u * sc, cy + v * sc) for u, v in pts])
    pl([(-1.05, 0.0), (1.2, 0.0), (0.88, 0.55), (-0.82, 0.55)], shade(hull, 0.7))
    pl([(-1.05, -0.05), (1.2, -0.05), (0.88, 0.5), (-0.82, 0.5)], hull)
    pl([(-0.95, -0.05), (1.2, -0.05), (1.16, 0.06), (-0.92, 0.06)], (255, 220, 120))
    pl([(-0.5, -0.5), (0.4, -0.5), (0.4, -0.05), (-0.5, -0.05)], (248, 248, 252))
    pl([(-0.15, -0.95), (0.1, -0.95), (0.1, -0.5), (-0.15, -0.5)], (60, 70, 96))
    for k in range(3):
        pygame.draw.circle(g.screen, (96, 170, 230), P(cx + (-0.35 + k * 0.28) * sc, cy - 0.28 * sc), max(2, int(sc * 0.07)))
    for k in range(3):
        pygame.draw.circle(g.screen, (255, 255, 255), P(cx + (0.0 - k * 0.2) * sc, cy - (1.05 + k * 0.3 + math.sin(t * 2 + k) * 0.05) * sc),
                           max(2, int(sc * (0.16 + k * 0.04))))


# ================================================================== penanda tembakan
def draw_flame(g, cx, cy, t, ph):
    f = 1 + 0.2 * math.sin(t * 9 + ph)
    pygame.draw.circle(g.screen, mix(g.col("deep"), STATIC["hit"], 0.3), P(cx, cy), int(17 * f))
    pygame.draw.polygon(g.screen, STATIC["hit"], [P(cx - 10, cy + 10), P(cx - 7, cy - 2), P(cx - 3, cy + 1), P(cx, cy - 15 * f),
                                                  P(cx + 3, cy - 1), P(cx + 8, cy - 4), P(cx + 10, cy + 10)])
    pygame.draw.polygon(g.screen, STATIC["hit2"], [P(cx - 5, cy + 10), P(cx - 1, cy - 6 * f), P(cx + 1, cy - 6 * f), P(cx + 5, cy + 10)])
    pygame.draw.circle(g.screen, (255, 246, 200), P(cx, cy + 6), 3)


def draw_ripple(g, cx, cy, t, ph):
    col = g.col("wave")
    for k in range(2):
        age = ((t * 0.9 + ph + k * 0.5) % 1.0)
        r = 4 + age * 13
        c = mix(col, g.col("deep"), age)
        pygame.draw.circle(g.screen, c, P(cx, cy), int(r), 2)
    pygame.draw.circle(g.screen, col, P(cx, cy), 3)


def draw_marks(g, lay, which, shots, t, hidden=()):
    for cell, v in shots.items():
        if (which, cell) in hidden:
            continue
        cx, cy = lay.cell_center(which, cell)
        ph = cell[0] * 1.3 + cell[1] * 0.7
        if v == "hit":
            draw_flame(g, cx, cy, t, ph)
        else:
            draw_ripple(g, cx, cy, t, ph)


def draw_hover(g, lay, which, cell, t):
    x, y, w, h = lay.cell_rect(which, cell)
    pulse = 2 * math.sin(t * 6)
    g.rrect(x + 2 - pulse / 2, y + 2 - pulse / 2, w - 4 + pulse, h - 4 + pulse, mix(g.col("shallow"), (255, 255, 255), 0.35), 8,
            STATIC["accent"], 2)
    cx, cy = int(x + w / 2), int(y + h / 2)
    pygame.draw.line(g.screen, STATIC["accent"], (cx - 9, cy), (cx + 9, cy), 2)
    pygame.draw.line(g.screen, STATIC["accent"], (cx, cy - 9), (cx, cy + 9), 2)
    pygame.draw.circle(g.screen, STATIC["accent"], (cx, cy), 7, 2)


def draw_heat(g, lay, which, prob):
    top = prob.max()
    if top <= 0:
        return
    tot = prob.sum()
    for r in range(N):
        for c in range(N):
            v = prob[r, c] / top
            if v <= 0:
                continue
            x, y, w, h = lay.cell_rect(which, (r, c))
            g.rrect(x + 2, y + 2, w - 4, h - 4, mix(g.col("deep"), (255, 150, 30), min(1.0, v)), 8)
            g.text(f"{prob[r, c] / tot * 100:.0f}", 11, (255, 255, 255) if v < .6 else (20, 20, 20), x + w / 2, y + h / 2 - 7, True, True)


def draw_ring(g, lay, which, cell, t):
    x, y, w, h = lay.cell_rect(which, cell)
    rad = int(w / 2 - 2 + 3 * math.sin(t * 5))
    pygame.draw.circle(g.screen, STATIC["accent"], P(x + w / 2, y + h / 2), rad, 4)
    pygame.draw.circle(g.screen, (255, 255, 255), P(x + w / 2, y + h / 2), max(2, rad - 5), 1)


# ================================================================== efek (partikel, cincin, proyektil)
def spawn_explosion(rng, parts, rings, x, y, big=False):
    for _ in range(36 if big else 22):
        a, sp = rng.random() * 6.283, rng.uniform(50, 230 if big else 170)
        col = rng.choice([STATIC["hit"], STATIC["hit2"], (255, 246, 200), (255, 120, 40)])
        parts.append({"x": x, "y": y, "vx": math.cos(a) * sp, "vy": math.sin(a) * sp - 40, "life": rng.uniform(.4, .9),
                      "max": .9, "color": col, "size": rng.uniform(3, 6.5 if big else 5), "grav": 260, "kind": "spark"})
    rings.append([x, y, 0.0, (255, 220, 140), 46 if big else 34])


def spawn_splash(rng, parts, rings, x, y):
    for _ in range(14):
        a = -math.pi / 2 + rng.uniform(-0.8, 0.8)
        sp = rng.uniform(80, 190)
        parts.append({"x": x, "y": y, "vx": math.cos(a) * sp, "vy": math.sin(a) * sp, "life": rng.uniform(.4, .8), "max": .8,
                      "color": (210, 240, 255), "size": rng.uniform(2, 4), "grav": 420, "kind": "drop"})
    rings.append([x, y, 0.0, (224, 246, 255), 30])
    rings.append([x, y, -0.15, (224, 246, 255), 22])


def spawn_smoke(rng, parts, x, y):
    parts.append({"x": x + rng.uniform(-8, 8), "y": y, "vx": rng.uniform(-8, 8), "vy": rng.uniform(-34, -20), "life": 1.4, "max": 1.4,
                  "color": (90, 90, 104), "size": rng.uniform(4, 7), "grav": 0, "kind": "smoke"})


def update_effects(parts, rings, dt):
    for p in parts:
        p["life"] -= dt
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        p["vy"] += p["grav"] * dt
    parts[:] = [p for p in parts if p["life"] > 0][-500:]
    for r in rings:
        r[2] += dt * 2.4
    rings[:] = [r for r in rings if r[2] < 1]


def draw_effects(g, parts, rings):
    for x, y, age, col, mr in rings:
        if age < 0:
            continue
        pygame.draw.circle(g.screen, col, P(x, y), int(6 + mr * age), max(1, int(4 * (1 - age))))
    for p in parts:
        k = max(0.0, p["life"] / p["max"])
        if p["kind"] == "smoke":
            r = p["size"] * (1.6 - k)
            pygame.draw.circle(g.screen, mix(p["color"], (170, 176, 196), 1 - k), P(p["x"], p["y"]), max(1, int(r)))
        else:
            pygame.draw.circle(g.screen, p["color"], P(p["x"], p["y"]), max(1, int(p["size"] * (0.4 + 0.6 * k))))


def projectile_pos(pr, now):
    p = max(0.0, min(1.0, (now - pr["t0"]) / pr["dur"]))
    x = pr["sx"] + (pr["ex"] - pr["sx"]) * p
    y = pr["sy"] + (pr["ey"] - pr["sy"]) * p - 130 * math.sin(math.pi * p)
    return x, y, p


def draw_projectile(g, pr, now):
    for k in range(6, 0, -1):                                          # jejak asap
        x, y, _ = projectile_pos(dict(pr, t0=pr["t0"] + 0.035 * k), now)
        pygame.draw.circle(g.screen, mix((255, 190, 80), g.col("wave"), k / 7), P(x, y), max(1, 7 - k))
    x, y, p = projectile_pos(pr, now)
    pygame.draw.circle(g.screen, (255, 200, 90), P(x, y), 9)
    pygame.draw.circle(g.screen, (40, 44, 60), P(x, y), 6)
    pygame.draw.circle(g.screen, (190, 196, 214), P(x - 2, y - 2), 2)
