"""ui/sprites.py - Visual sprites and background for Casual Cartoon / Mobile Pop theme.
Theme: Dreamy pastel sky with fluffy cotton-candy clouds, 3D floating tiles (Fire, Cherries, Watermelon, Anchor),
playful cartoon ocean with turquoise water, foamy crests, and vibrant cute warships.
"""
import math
import random

import pygame

from core.state import N
from ui.gfx import STATIC, mix, shade
from ui.layout import HORIZON, W, H

_rng = random.Random(7)
STARS = [(_rng.randrange(0, W), _rng.randrange(8, HORIZON - 30), _rng.random() * 6.28) for _ in range(70)]

# Floating cloud anchors (x, y, scale, speed, phase)
CLOUDS = [
    (100, 75, 1.25, 6, 0.0),
    (480, 130, 0.95, 4, 1.2),
    (880, 70, 1.35, 7, 2.5),
    (1240, 110, 1.10, 5, 3.8),
    (280, 220, 0.85, 3, 4.7),
]

CELESTIAL = (1200, 220, 160)

# Cheerful yacht and luxury boat palettes matching reference
SHIP_COL = {
    "Carrier":    ((245, 248, 255), (245, 210, 50)),   # White Superyacht with Golden Helipad
    "Battleship": ((245, 248, 255), (235, 85, 150)),   # Luxury Cruiser with Pink Sunbeds
    "Cruiser":    ((245, 248, 255), (225, 185, 135)),  # Sport Yacht with Teak Deck & Lifebuoy
    "Submarine":  ((240, 245, 255), (70, 195, 235)),   # Patrol Yacht with Cyan Sunbeds
    "Destroyer":  ((125, 76, 42),   (210, 155, 100)),  # Classic Teak Wooden Rowboat
}

# Tropical sea life (swimming fish beneath clear water)
FISH_SCHOOL = [
    {"x": 80,   "y": 460, "sp": 24, "sz": 16, "ph": 0.0, "col": (50, 175, 235)},
    {"x": 260,  "y": 580, "sp": 32, "sz": 18, "ph": 1.2, "col": (40, 160, 220)},
    {"x": 450,  "y": 510, "sp": 20, "sz": 14, "ph": 2.5, "col": (65, 195, 245)},
    {"x": 680,  "y": 620, "sp": 28, "sz": 20, "ph": 3.7, "col": (55, 180, 230)},
    {"x": 890,  "y": 480, "sp": 22, "sz": 15, "ph": 4.8, "col": (45, 170, 225)},
    {"x": 1100, "y": 560, "sp": 30, "sz": 19, "ph": 5.9, "col": (60, 190, 240)},
    {"x": 1260, "y": 430, "sp": 26, "sz": 17, "ph": 0.8, "col": (50, 175, 235)},
]


def P(x, y):
    return (int(x), int(y))


def sky_at(g, y):
    frac = max(0.0, min(1.0, y / max(1, HORIZON)))
    if frac < 0.6:
        return mix(g.col("sky1"), g.col("sky2"), frac / 0.6)
    return mix(g.col("sky2"), (245, 218, 238), (frac - 0.6) / 0.4)


# ================================================================== FLUFFY CLOUDS
def draw_puffy_cloud(screen, cx, cy, sc, tod=0.0):
    """Draw a puffy, layered cotton-candy cloud matching the reference art.
    Soft pink-lavender bottom shading + pure white fluffy rounded billows."""
    puffs = (
        (-48, 8, 28),
        (-22, -14, 36),
        (18, -18, 42),
        (56, -4, 32),
        (84, 10, 24),
        (10, 12, 34),
        (-26, 14, 28),
    )
    # 1. Soft bottom shadow / lilac-pink tint
    tint_bottom = mix((235, 210, 232), (58, 45, 88), tod)
    for dx, dy, r in puffs:
        pygame.draw.circle(screen, tint_bottom, P(cx + dx * sc, cy + (dy + 5) * sc), int(r * sc))

    # 2. Main white billow face
    tint_face = mix((255, 255, 255), (95, 85, 130), tod)
    for dx, dy, r in puffs:
        pygame.draw.circle(screen, tint_face, P(cx + dx * sc, cy + dy * sc), int(r * sc))

    # 3. Top bright highlight shine
    tint_top = mix((255, 255, 255), (140, 130, 175), tod)
    for dx, dy, r in puffs[:4]:
        pygame.draw.circle(screen, tint_top, P(cx + dx * sc, cy + (dy - 3) * sc), int((r - 4) * sc))


# ================================================================== BACKGROUND (SKY & SEA)
def draw_sky(g, t):
    """Draw vertical pastel gradient sky + stars/sun/moon + fluffy floating clouds."""
    bands = 32
    for i in range(bands):
        y0 = i * HORIZON // bands
        y1 = (i + 1) * HORIZON // bands
        c = sky_at(g, (y0 + y1) // 2)
        pygame.draw.rect(g.screen, c, pygame.Rect(0, y0, W, y1 - y0 + 2))

    # Night stars
    for x, y, ph in STARS:
        b = g.tod * (0.55 + 0.45 * math.sin(t * 2 + ph))
        if b > 0.12:
            c = mix(sky_at(g, y), (255, 255, 255), b)
            pygame.draw.circle(g.screen, c, P(x, y), 2 if b > 0.6 else 1)

    # Celestial (sun / moon)
    draw_celestials(g, t)

    # Floating puffy clouds (daytime / twilight)
    for i, (cx, cy, sc, sp, ph) in enumerate(CLOUDS):
        x = (cx + t * sp * 3) % (W + 360) - 180
        y = cy + math.sin(t * 0.8 + ph) * 6
        draw_puffy_cloud(g.screen, x, y, sc, g.tod)

    # Giant billowing cloud puffs framing top corners & horizon
    draw_puffy_cloud(g.screen, 20, 20, 1.45, g.tod)
    draw_puffy_cloud(g.screen, W - 60, 30, 1.55, g.tod)
    draw_puffy_cloud(g.screen, 220, HORIZON - 10, 1.6, g.tod)
    draw_puffy_cloud(g.screen, W - 280, HORIZON - 15, 1.7, g.tod)

    # Cheerful cartoon ocean
    draw_sea(g, t)


def draw_celestials(g, t):
    cx, cy, r = CELESTIAL
    a = g.tod * math.pi
    sx, sy = cx + r * math.sin(a), cy - r * math.cos(a)               # sun
    mx, my = cx + r * math.sin(a + math.pi), cy - r * math.cos(a + math.pi)   # moon

    # Sun
    sky = sky_at(g, min(sy, HORIZON))
    for rad, k in ((76, .12), (60, .22), (46, .4)):
        pygame.draw.circle(g.screen, mix(sky, (255, 218, 95), k), P(sx, sy), rad)
    for i in range(12):
        ang = t * 0.35 + i * math.pi / 6
        p1 = P(sx + 38 * math.cos(ang), sy + 38 * math.sin(ang))
        p2 = P(sx + 56 * math.cos(ang), sy + 56 * math.sin(ang))
        pygame.draw.line(g.screen, (255, 220, 105), p1, p2, 4)
    pygame.draw.circle(g.screen, (255, 235, 125), P(sx, sy), 34)
    pygame.draw.circle(g.screen, (255, 252, 200), P(sx, sy), 26)

    # Moon
    sky = sky_at(g, min(max(my, 0), HORIZON))
    for rad, k in ((70, .1), (54, .2), (44, .35)):
        pygame.draw.circle(g.screen, mix(sky, (200, 215, 255), k), P(mx, my), rad)
    pygame.draw.circle(g.screen, (246, 248, 255), P(mx, my), 32)
    for dx, dy, rr in ((-9, -7, 6), (8, 5, 8), (-4, 12, 4)):
        pygame.draw.circle(g.screen, (218, 224, 242), P(mx + dx, my + dy), rr)


def wave_points(x0, x1, base, amp, length, speed, t, step=22):
    pts = []
    x = x0
    while x <= x1:
        pts.append((x, base + amp * math.sin(x / length + t * speed)))
        x += step
    pts.append((x1, base + amp * math.sin(x1 / length + t * speed)))
    return pts


def draw_puffy_wave_crest(screen, pts, t, sc=1.0, step=12):
    """Draw cloud-like puffy white wave foam crests along wave points, matching reference image."""
    # 1. Soft mint-aqua bottom shadow billows
    for i in range(0, len(pts), step):
        px, py = pts[i]
        r = int((13 + 4 * math.sin(i * 0.4 + t * 3)) * sc)
        pygame.draw.circle(screen, (185, 230, 245), P(px, py + 4 * sc), r)
    # 2. Main brilliant white foam billows
    for i in range(0, len(pts), step):
        px, py = pts[i]
        r = int((12 + 4 * math.sin(i * 0.4 + t * 3)) * sc)
        pygame.draw.circle(screen, (255, 255, 255), P(px, py), r)
    # 3. Bright top highlight puffs
    for i in range(0, len(pts), step * 2):
        px, py = pts[i]
        r = int((7 + 3 * math.sin(i * 0.8 + t * 4)) * sc)
        pygame.draw.circle(screen, (255, 255, 255), P(px, py - 3 * sc), r)


def draw_seafoam_swirls(screen, x0, x1, y_base, t, phase=0.0):
    """Draw curved seafoam lace ribbons across the wave surface, matching reference image."""
    swirl_col = (235, 252, 255)
    width = x1 - x0
    count = max(2, int(width // 160))
    for s_i in range(count):
        sx = x0 + ((s_i * 180 + t * 25 + phase * 60) % max(1, width))
        sy = y_base + math.sin(t * 2 + s_i + phase) * 12
        pts = [
            P(sx, sy),
            P(sx + 35, sy - 8),
            P(sx + 75, sy + 6),
            P(sx + 115, sy - 4),
            P(sx + 145, sy + 2)
        ]
        pygame.draw.lines(screen, swirl_col, False, pts, 2)
        pygame.draw.circle(screen, (255, 255, 255), P(sx + 40, sy - 14), 2)
        pygame.draw.circle(screen, (255, 255, 255), P(sx + 90, sy + 12), 2)


def draw_adventure_sailboat(g, cx, cy, sc=1.0, t=0.0, bob=True):
    """Draw the wooden expedition boat from the reference image:
    - Caramel-oak wooden hull with golden trim rim
    - Striped billowing sail (coral red and cream-white vertical stripes)
    - Masthead red pennant flag
    - Crashing puffy white sea-foam splashes curling around the hull
    - Cat captain with brass telescope!
    """
    screen = g.screen
    bob_y = math.sin(t * 2.8) * 8 * sc if bob else 0
    pitch = math.sin(t * 2.4) * 0.08 if bob else 0
    cy += bob_y

    def rot(dx, dy):
        rx = dx * math.cos(pitch) - dy * math.sin(pitch)
        ry = dx * math.sin(pitch) + dy * math.cos(pitch)
        return P(cx + rx * sc, cy + ry * sc)

    # 1. Wooden Mast
    pygame.draw.line(screen, (130, 80, 42), rot(0, 10), rot(0, -120), max(3, int(7 * sc)))
    # Cross spars
    pygame.draw.line(screen, (150, 95, 50), rot(-45, -112), rot(45, -112), max(2, int(4 * sc)))
    pygame.draw.line(screen, (150, 95, 50), rot(-55, -25), rot(55, -25), max(2, int(4 * sc)))

    # 2. Billowing Striped Sail (Red & Cream Stripes)
    sail_top_y, sail_bot_y = -110, -28
    sail_w = 48
    stripes = 5
    for st in range(stripes):
        frac1 = st / stripes
        frac2 = (st + 1) / stripes
        dx1 = -sail_w + frac1 * (sail_w * 2)
        dx2 = -sail_w + frac2 * (sail_w * 2)
        col = (235, 68, 62) if (st % 2 == 1) else (252, 248, 238)
        belly1 = math.sin(frac1 * math.pi) * 12
        belly2 = math.sin(frac2 * math.pi) * 12
        pts = [
            rot(dx1, sail_top_y),
            rot(dx2, sail_top_y),
            rot(dx2 + belly2, sail_bot_y),
            rot(dx1 + belly1, sail_bot_y)
        ]
        pygame.draw.polygon(screen, col, pts)
    pygame.draw.polygon(screen, (160, 50, 45), [
        rot(-sail_w, sail_top_y), rot(sail_w, sail_top_y),
        rot(sail_w, sail_bot_y), rot(-sail_w, sail_bot_y)
    ], 2)

    # 3. Masthead Red Pennant Flag
    flag_wave = math.sin(t * 8) * 6
    flag_pts = [
        rot(0, -122),
        rot(-34, -130 + flag_wave),
        rot(-30, -114 + flag_wave)
    ]
    pygame.draw.polygon(screen, (245, 45, 65), flag_pts)

    # 4. Cat Captain with Brass Telescope
    cat_center = rot(-16, -14)
    pygame.draw.circle(screen, (240, 165, 75), cat_center, int(13 * sc))
    draw_ellipse(screen, (255, 215, 60), pygame.Rect(cat_center[0] - 14 * sc, cat_center[1] - 16 * sc, 28 * sc, 12 * sc))
    tele_start = rot(-8, -12)
    tele_end = rot(28, -26)
    pygame.draw.line(screen, (255, 200, 45), tele_start, tele_end, max(3, int(6 * sc)))
    pygame.draw.circle(screen, (255, 235, 120), tele_end, max(2, int(4 * sc)))

    # 5. Wooden Hull (Caramel Oak Planks with Golden Rim)
    hull_pts = [
        rot(-62, -2), rot(68, -2), rot(82, -18), rot(72, 22), rot(30, 42), rot(-45, 42), rot(-68, 20)
    ]
    pygame.draw.polygon(screen, (215, 145, 75), hull_pts)
    line_y_offsets = [10, 22, 34]
    for ly in line_y_offsets:
        pygame.draw.line(screen, (160, 95, 45), rot(-55, ly), rot(55, ly), max(1, int(2 * sc)))
    pygame.draw.lines(screen, (250, 195, 80), False, [rot(-64, -2), rot(68, -2), rot(84, -18)], max(3, int(6 * sc)))
    pygame.draw.polygon(screen, (115, 62, 28), hull_pts, 2)

    # 6. Big Puffy Bow Wave Foam Splashes (Curling foam plumes)
    splash_pts = [(45, 16), (62, 10), (78, 14), (92, 26), (82, 38), (60, 42),
                  (-35, 22), (-52, 18), (-68, 24), (-78, 36), (-60, 44)]
    for dx, dy in splash_pts:
        sp_r = int((14 + 4 * math.sin(dx + t * 6)) * sc)
        pygame.draw.circle(screen, (185, 232, 248), rot(dx, dy + 4), sp_r)
    for dx, dy in splash_pts:
        sp_r = int((13 + 4 * math.sin(dx + t * 6)) * sc)
        pygame.draw.circle(screen, (255, 255, 255), rot(dx, dy), sp_r)


def draw_sea(g, t):
    """Stylized cartoon ocean with dramatic volumetric puffy foam waves,
    swirling seafoam lace, and adventure sailboat matching the user's reference image."""
    screen = g.screen

    # 1. Base Ocean Gradient (Cerulean horizon -> Deep Royal Ocean)
    bands = 28
    for i in range(bands):
        y0 = HORIZON + i * (H - HORIZON) // bands
        frac = i / bands
        c = mix((28, 175, 230), (10, 80, 160), frac)
        pygame.draw.rect(screen, mix(c, (14, 28, 65), g.tod * 0.7),
                         pygame.Rect(0, y0, W, (H - HORIZON) // bands + 2))

    # 2. Distant Tropical Cliff & Fairytale Tower on Right Horizon (matching reference!)
    cliff_x = W - 220
    cliff_y = HORIZON + 15
    cliff_pts = [
        P(cliff_x, cliff_y + 80), P(cliff_x + 40, cliff_y - 20),
        P(cliff_x + 110, cliff_y - 35), P(cliff_x + 180, cliff_y - 15),
        P(W, cliff_y + 10), P(W, cliff_y + 90), P(cliff_x, cliff_y + 90)
    ]
    pygame.draw.polygon(screen, (160, 125, 95), cliff_pts)
    pygame.draw.polygon(screen, (75, 195, 85), [
        P(cliff_x + 35, cliff_y - 20), P(cliff_x + 110, cliff_y - 35),
        P(cliff_x + 180, cliff_y - 15), P(cliff_x + 175, cliff_y - 5),
        P(cliff_x + 105, cliff_y - 22), P(cliff_x + 40, cliff_y - 12)
    ])
    tow_x, tow_y = cliff_x + 115, cliff_y - 35
    pygame.draw.rect(screen, (245, 235, 220), pygame.Rect(tow_x - 12, tow_y - 38, 24, 38), border_radius=4)
    pygame.draw.polygon(screen, (225, 65, 80), [
        P(tow_x - 16, tow_y - 38), P(tow_x + 16, tow_y - 38), P(tow_x, tow_y - 62)
    ])

    # 3. Swimming tropical fish
    for f in FISH_SCHOOL:
        fx = (f["x"] + t * f["sp"]) % (W + 120) - 60
        fy = f["y"] + math.sin(t * 2.5 + f["ph"]) * 10
        fcol = mix(f["col"], (20, 50, 95), g.tod * 0.6)
        pygame.draw.polygon(screen, fcol, [
            P(fx + f["sz"], fy), P(fx, fy - f["sz"] * 0.45),
            P(fx - f["sz"] * 0.7, fy), P(fx, fy + f["sz"] * 0.45)
        ])

    # 4. Multi-Layer Rolling Oceanic Waves with Volumetric Puffy Foam Crests
    wave_layers = [
        (HORIZON + 35, 7.0, 75, 1.2, (25, 155, 220), 0.7, 18),
        (HORIZON + 95, 10.0, 85, 1.4, (20, 140, 208), 0.9, 16),
        (HORIZON + 175, 14.0, 95, 1.6, (16, 120, 192), 1.15, 14),
        (HORIZON + 265, 18.0, 110, 1.9, (12, 100, 175), 1.35, 12),
    ]

    for base_y, amp, period, speed, wave_col, foam_sc, step in wave_layers:
        pts = wave_points(0, W, base_y, amp, period, speed, t, step=12)
        poly = pts + [(W, H), (0, H)]
        pygame.draw.polygon(screen, mix(wave_col, g.col("sea2"), g.tod * 0.7), [P(x, y) for x, y in poly])
        draw_seafoam_swirls(screen, 0, W, base_y + 18, t, phase=base_y * 0.05)
        draw_puffy_wave_crest(screen, pts, t + base_y * 0.1, sc=foam_sc, step=step)

    # 5. Adventure Sailboat riding the waves
    boat_x = (t * 36) % (W + 400) - 200
    boat_y = HORIZON + 155 + math.sin(t * 2.2) * 14
    draw_adventure_sailboat(g, boat_x, boat_y, sc=1.1, t=t, bob=True)


def draw_sea_surface(g, rect, t, phase=0.0):
    """Playful cartoon sea surface inside game board: tropical turquoise depth + puffy waves + seafoam swirls."""
    x0, y0, w, h = rect
    screen = g.screen
    rows = 18
    for i in range(rows):
        frac = i / (rows - 1)
        c = mix((42, 195, 238), (14, 90, 168), frac)
        pygame.draw.rect(screen, mix(c, g.col("deep"), g.tod * 0.6),
                         pygame.Rect(int(x0), int(y0 + i * h / rows), int(w), int(h / rows) + 1))

    # Swirling seafoam lace ribbons inside board
    draw_seafoam_swirls(screen, x0, x0 + w, y0 + h * 0.35, t, phase=phase)
    draw_seafoam_swirls(screen, x0, x0 + w, y0 + h * 0.70, t, phase=phase + 1.5)

    # Puffy wave crest lines inside board
    for i in range(4):
        base = y0 + (i + 0.6) * h / 4.2
        pts = wave_points(x0, x0 + w, base, 3.2, 32 + i * 6, 1.6 + i * 0.15, t + phase + i, step=10)
        pts = [(x, min(max(y, y0 + 2), y0 + h - 2)) for x, y in pts]
        draw_puffy_wave_crest(screen, pts, t + i, sc=0.45, step=10)

    # Sparkles
    for i in range(12):
        sx = x0 + (i * 49 + t * 20 * (1 + i % 3)) % w
        sy = y0 + (i * 35) % h
        if math.sin(t * 3.5 + i) > 0.4:
            pygame.draw.circle(screen, (255, 255, 255), P(sx, sy), 2)


def draw_frame(g, rect):
    """Bubbly cartoon frame around game board."""
    x, y, w, h = rect
    # 3D drop shadow
    g.rrect(x - 24, y - 18, w + 36, h + 42, (18, 12, 38), 24)
    # Outer candy purple frame
    g.rrect(x - 24, y - 24, w + 36, h + 42, g.col("frame"), 24)
    # Inner rim
    g.rrect(x - 12, y - 14, w + 12, h + 18, g.col("frame_in"), 16)


def draw_grid(g, lay, which):
    x0, y0, w, h = lay.board_rect(which)
    c = mix(g.col("deep"), g.col("wave"), 0.32)
    for i in range(N + 1):
        pygame.draw.line(g.screen, c, P(x0 + i * lay.cell, y0), P(x0 + i * lay.cell, y0 + h), 1)
        pygame.draw.line(g.screen, c, P(x0, y0 + i * lay.cell), P(x0 + w, y0 + i * lay.cell), 1)
    for i in range(N):
        g.text("ABCDEFGHIJ"[i], 14, (255, 255, 255), x0 + i * lay.cell + lay.cell / 2, y0 - 24, True, True, shadow=True)
        g.text(str(i + 1), 14, (255, 255, 255), x0 - 14, y0 + i * lay.cell + lay.cell / 2 - 9, True, True, shadow=True)


def draw_board_water(g, lay, which, t):
    rect = lay.board_rect(which)
    draw_frame(g, rect)
    draw_sea_surface(g, rect, t, 0.0 if which == "human" else 1.7)
    draw_grid(g, lay, which)


# ================================================================== 3D FLOATING TILES (TILE MATCH STYLE)
def draw_game_tile(g, cx, cy, w, h, icon, t=0.0, bob_phase=0.0):
    """Draw a 3D porcelain rounded tile with drop shadow and cartoon icon
    (matching the Fire, Cherry, and Watermelon tiles in the reference image)."""
    bob = math.sin(t * 2.4 + bob_phase) * 5
    px, py = int(cx - w / 2), int(cy - h / 2 + bob)

    # 1. Soft dark drop shadow
    g.rrect(px + 2, py + 8, w, h, (18, 12, 38), 16)

    # 2. 3D bottom bevel (soft purple-gray)
    g.rrect(px, py + 4, w, h, (200, 205, 225), 16)

    # 3. Main porcelain white face
    g.rrect(px, py, w, h, (255, 255, 255), 16, (170, 175, 210), 2)

    # 4. Top gentle gloss
    g.rrect(px + 4, py + 3, w - 8, max(4, h // 4), (255, 255, 255), 8)

    # 5. Icon inside tile
    icx, icy = px + w // 2, py + h // 2
    if icon == "fire":
        # Cartoon Flame icon (yellow center, juicy red/orange outline)
        pygame.draw.circle(g.screen, (255, 105, 35), (icx, icy + 4), 14)
        pygame.draw.polygon(g.screen, (245, 62, 45), [
            (icx - 12, icy + 12), (icx - 8, icy - 2), (icx - 2, icy + 4),
            (icx + 2, icy - 14), (icx + 6, icy - 4), (icx + 12, icy + 12)
        ])
        pygame.draw.polygon(g.screen, (255, 215, 60), [
            (icx - 6, icy + 12), (icx - 2, icy + 2), (icx + 1, icy - 6),
            (icx + 3, icy + 2), (icx + 6, icy + 12)
        ])
    elif icon == "cherry":
        # Twin red cherries with green stem
        c1 = (icx - 7, icy + 6)
        c2 = (icx + 7, icy + 4)
        # Stems
        pygame.draw.line(g.screen, (52, 160, 48), c1, (icx - 1, icy - 10), 3)
        pygame.draw.line(g.screen, (52, 160, 48), c2, (icx - 1, icy - 10), 3)
        pygame.draw.circle(g.screen, (75, 195, 65), (icx + 5, icy - 9), 5)
        # Cherries
        pygame.draw.circle(g.screen, (220, 25, 45), c1, 8)
        pygame.draw.circle(g.screen, (255, 80, 100), (c1[0] - 2, c1[1] - 2), 3)
        pygame.draw.circle(g.screen, (220, 25, 45), c2, 8)
        pygame.draw.circle(g.screen, (255, 80, 100), (c2[0] - 2, c2[1] - 2), 3)
    elif icon == "watermelon":
        # Watermelon slice (green rind, red inside, dark seeds)
        pygame.draw.polygon(g.screen, (52, 185, 68), [
            (icx - 14, icy - 6), (icx + 14, icy - 6), (icx, icy + 12)
        ])
        pygame.draw.polygon(g.screen, (245, 52, 75), [
            (icx - 11, icy - 6), (icx + 11, icy - 6), (icx, icy + 9)
        ])
        # Seeds
        pygame.draw.circle(g.screen, (28, 18, 38), (icx - 4, icy - 1), 2)
        pygame.draw.circle(g.screen, (28, 18, 38), (icx + 4, icy - 1), 2)
        pygame.draw.circle(g.screen, (28, 18, 38), (icx, icy + 4), 2)
    elif icon == "anchor":
        # Golden nautical anchor
        pygame.draw.circle(g.screen, (255, 195, 30), (icx, icy - 8), 5, 2)
        pygame.draw.line(g.screen, (255, 195, 30), (icx, icy - 5), (icx, icy + 10), 3)
        pygame.draw.line(g.screen, (255, 195, 30), (icx - 7, icy - 1), (icx + 7, icy - 1), 3)
        pygame.draw.arc(g.screen, (255, 195, 30), pygame.Rect(icx - 10, icy + 2, 20, 12), math.pi, 2 * math.pi, 3)


# ================================================================== TOP-DOWN LUXURY BOATS (YACHTS & DINGHY)
def draw_ship(g, lay, which, name, cells, t, sunk=False):
    """Draw top-down luxury yachts and wooden rowboat matching the reference art:
    - Carrier (5 cells): Mega Superyacht with golden Helipad 'H', yellow sunbeds, plunge pool.
    - Battleship (4 cells): Luxury Cruiser with foredeck jacuzzi pool, black/white curved arches, pink loungers.
    - Cruiser (3 cells): Sport Yacht with teak deck, red/white lifebuoy, dark windshield, cooler box.
    - Submarine (3 cells): Patrol Yacht with aerodynamic cabin, radar dome, lifebuoy ring.
    - Destroyer (2 cells): Classic Wooden Dinghy with teak planks, thwart bench, and fish bucket.
    """
    s = lay.cell
    rs = [lay.cell_rect(which, c) for c in cells]
    x0, y0 = min(r[0] for r in rs), min(r[1] for r in rs)
    L = len(cells)
    horiz = len({c[0] for c in cells}) == 1
    ph = sum(cells[0]) * 0.7
    bob = (1.8 if not sunk else 0.5) * math.sin(t * 2.2 + ph) + (3 if sunk else 0)

    # u: 0.0 (stern) -> 1.0 (bow) along ship length (L * s)
    # v: -0.5 (port) -> +0.5 (starboard) across ship beam (s)
    def uv(u, v):
        if horiz:
            return P(x0 + u * (L * s), y0 + (0.5 + v) * s + bob)
        else:
            return P(x0 + (0.5 + v) * s, y0 + u * (L * s) + bob)

    def poly(pts, col, border=None, bw=1):
        pts_px = [uv(u, v) for u, v in pts]
        pygame.draw.polygon(g.screen, col, pts_px)
        if border:
            pygame.draw.polygon(g.screen, border, pts_px, bw)

    def circle(u, v, rad, col, border=None, bw=1):
        c_px = uv(u, v)
        pygame.draw.circle(g.screen, col, c_px, max(1, int(rad)))
        if border:
            pygame.draw.circle(g.screen, border, c_px, max(1, int(rad)), bw)

    def line(u1, v1, u2, v2, col, w=2):
        pygame.draw.line(g.screen, col, uv(u1, v1), uv(u2, v2), max(1, int(w)))

    # Colors
    white_hull = (248, 250, 255) if not sunk else (75, 78, 88)
    teak_deck  = (225, 192, 145) if not sunk else (95, 82, 70)
    shadow_col = (18, 14, 38)
    hull_border = (185, 195, 215) if not sunk else (45, 45, 55)

    # 1. Trailing foam wake (if alive)
    if not sunk:
        wob = 0.05 * math.sin(t * 6 + ph)
        line(0.04, -0.44, -0.16 + wob, -0.48, g.col("crest"), 3)
        line(0.04, 0.44, -0.16 + wob, 0.48, g.col("crest"), 3)

    # 2. Hull drop shadow
    poly([(0.04, -0.44), (0.76, -0.44), (0.98, 0.0), (0.76, 0.44), (0.04, 0.44)], shadow_col)

    # 3. Model Specific Boat Art
    if name == "Carrier" or L >= 5:
        # === MEGA SUPERYACHT (Helipad 'H' + Plunge Pool + Yellow Sunbeds) ===
        # Outer fiberglass hull
        poly([(0.04, -0.42), (0.76, -0.42), (0.98, 0.0), (0.76, 0.42), (0.04, 0.42)], white_hull, hull_border, 2)
        # Teak foredeck
        poly([(0.74, -0.36), (0.95, 0.0), (0.74, 0.36)], teak_deck)
        # Round plunge pool on foredeck
        circle(0.85, 0.0, s * 0.18, (255, 255, 255) if not sunk else (60, 60, 70))
        circle(0.85, 0.0, s * 0.14, (60, 215, 240) if not sunk else (40, 50, 60))
        # Aerodynamic winglets
        poly([(0.56, -0.52), (0.64, -0.52), (0.66, -0.40), (0.54, -0.40)], white_hull, hull_border)
        poly([(0.56, 0.52), (0.64, 0.52), (0.66, 0.40), (0.54, 0.40)], white_hull, hull_border)
        # Curved navigation bridge with tinted glass
        poly([(0.50, -0.34), (0.66, -0.34), (0.68, 0.0), (0.66, 0.34), (0.50, 0.34)],
             (35, 75, 115) if not sunk else (50, 55, 65))
        # Yellow sunbeds
        bed_col = (255, 210, 40) if not sunk else (85, 80, 55)
        poly([(0.40, -0.35), (0.47, -0.35), (0.47, -0.21), (0.40, -0.21)], bed_col)
        poly([(0.40, 0.21), (0.47, 0.21), (0.47, 0.35), (0.40, 0.35)], bed_col)
        # Aft HELIPAD (Dark circle with golden ring and bold 'H')
        circle(0.24, 0.0, s * 0.33, (45, 48, 56) if not sunk else (40, 40, 45), (240, 200, 50), 2)
        circle(0.24, 0.0, s * 0.25, (45, 48, 56), (240, 200, 50), 1)
        # 'H' letter on helipad
        h_col = (255, 215, 40) if not sunk else (120, 110, 70)
        line(0.20, -0.10, 0.28, -0.10, h_col, 3)
        line(0.20, 0.10, 0.28, 0.10, h_col, 3)
        line(0.24, -0.10, 0.24, 0.10, h_col, 3)
        # Stern swim platform
        poly([(0.04, -0.38), (0.12, -0.38), (0.12, 0.38), (0.04, 0.38)], teak_deck)

    elif name == "Battleship" or L == 4:
        # === LUXURY CRUISER (Round Jacuzzi + Black/White Arches + Pink Sun Loungers) ===
        poly([(0.05, -0.42), (0.72, -0.42), (0.98, 0.0), (0.72, 0.42), (0.05, 0.42)], white_hull, hull_border, 2)
        # Teak foredeck
        poly([(0.70, -0.36), (0.95, 0.0), (0.70, 0.36)], teak_deck)
        # Round Jacuzzi Plunge Pool on foredeck
        circle(0.82, 0.0, s * 0.22, (255, 255, 255) if not sunk else (60, 60, 70))
        circle(0.82, 0.0, s * 0.17, (50, 210, 235) if not sunk else (40, 50, 60))
        circle(0.80, -0.04, s * 0.04, (255, 255, 255))
        # Triple curved black & white aerodynamic arches across the canopy
        band_col = (28, 32, 42) if not sunk else (40, 42, 48)
        poly([(0.54, -0.34), (0.66, -0.34), (0.68, 0.0), (0.66, 0.34), (0.54, 0.34)], band_col)
        line(0.58, -0.30, 0.62, 0.0, (255, 255, 255), 2)
        line(0.58, 0.30, 0.62, 0.0, (255, 255, 255), 2)
        # Aft Teak Sundeck with TWO PINK/MAGENTA SUN LOUNGERS
        poly([(0.15, -0.36), (0.46, -0.36), (0.46, 0.36), (0.15, 0.36)], teak_deck)
        pink_col = (235, 85, 150) if not sunk else (85, 50, 65)
        # Port Lounger
        poly([(0.20, -0.28), (0.38, -0.28), (0.38, -0.08), (0.20, -0.08)], pink_col)
        poly([(0.33, -0.28), (0.38, -0.28), (0.38, -0.08), (0.33, -0.08)], (255, 255, 255))
        # Starboard Lounger
        poly([(0.20, 0.08), (0.38, 0.08), (0.38, 0.28), (0.20, 0.28)], pink_col)
        poly([(0.33, 0.08), (0.38, 0.08), (0.38, 0.28), (0.33, 0.28)], (255, 255, 255))
        # Stern swim platform
        poly([(0.05, -0.38), (0.13, -0.38), (0.13, 0.38), (0.05, 0.38)], (190, 195, 205))

    elif name == "Cruiser" or (L == 3 and which == "human"):
        # === SPORT FISHING YACHT (Red/White Lifebuoy + Orange Seat + Cooler Box) ===
        poly([(0.06, -0.42), (0.68, -0.42), (0.98, 0.0), (0.68, 0.42), (0.06, 0.42)], white_hull, hull_border, 2)
        poly([(0.66, -0.36), (0.95, 0.0), (0.66, 0.36)], teak_deck)
        # Circular Red & White Lifebuoy (Life Ring) on foredeck
        circle(0.80, 0.0, s * 0.17, (225, 45, 45) if not sunk else (75, 40, 40))
        circle(0.80, 0.0, s * 0.13, (255, 255, 255) if not sunk else (85, 85, 90))
        circle(0.80, 0.0, s * 0.07, teak_deck)
        # Cockpit curved tinted windshield
        poly([(0.50, -0.32), (0.64, -0.32), (0.66, 0.0), (0.64, 0.32), (0.50, 0.32)],
             (30, 65, 98) if not sunk else (45, 52, 60))
        # White cabin roof
        poly([(0.22, -0.30), (0.48, -0.30), (0.48, 0.30), (0.22, 0.30)], white_hull)
        # Orange passenger seat cushion
        poly([(0.38, -0.24), (0.46, -0.24), (0.46, -0.04), (0.38, -0.04)], (255, 140, 40) if not sunk else (85, 60, 40))
        # White/Cyan cooler box
        poly([(0.24, -0.24), (0.34, -0.24), (0.34, -0.04), (0.24, -0.04)], (255, 255, 255))
        poly([(0.25, -0.22), (0.33, -0.22), (0.33, -0.06), (0.25, -0.06)], (65, 185, 235))
        # Stern rod mounts
        line(0.06, -0.34, -0.04, -0.44, (215, 130, 45), 2)
        line(0.06, 0.34, -0.04, 0.44, (215, 130, 45), 2)

    elif name == "Submarine" or L == 3:
        # === PATROL YACHT (High-Tech Sport Boat with Cyan Loungers & Radar) ===
        poly([(0.06, -0.42), (0.68, -0.42), (0.98, 0.0), (0.68, 0.42), (0.06, 0.42)], white_hull, hull_border, 2)
        poly([(0.66, -0.36), (0.95, 0.0), (0.66, 0.36)], teak_deck)
        circle(0.80, 0.0, s * 0.15, (255, 255, 255) if not sunk else (75, 75, 80), (70, 195, 235), 2)
        # Curved aerodynamic bridge
        poly([(0.48, -0.32), (0.64, -0.32), (0.66, 0.0), (0.64, 0.32), (0.48, 0.32)],
             (26, 45, 70) if not sunk else (40, 45, 52))
        # White radar dome
        circle(0.55, 0.0, s * 0.10, (255, 255, 255))
        # Cyan sunbed loungers
        cyan_col = (70, 195, 235) if not sunk else (45, 70, 80)
        poly([(0.24, -0.24), (0.42, -0.24), (0.42, -0.04), (0.24, -0.04)], cyan_col)
        poly([(0.24, 0.04), (0.42, 0.04), (0.42, 0.24), (0.24, 0.24)], cyan_col)
        # Stern vents
        line(0.08, -0.22, 0.08, 0.22, (180, 185, 195), 2)

    else:
        # === DESTROYER: CLASSIC WOODEN DINGHY / ROWBOAT (Size 2) ===
        wood_dark  = (115, 68, 38) if not sunk else (55, 42, 32)
        wood_light = (215, 160, 105) if not sunk else (85, 68, 52)
        thwart_col = (135, 80, 44) if not sunk else (62, 45, 34)
        # Outer dark wood rim / gunwale
        poly([(0.06, -0.45), (0.66, -0.45), (0.96, 0.0), (0.66, 0.45), (0.06, 0.45)], wood_dark)
        # Inner warm oak planked floor
        poly([(0.09, -0.38), (0.64, -0.38), (0.92, 0.0), (0.64, 0.38), (0.09, 0.38)], wood_light)
        # Horizontal plank lines
        line(0.25, -0.36, 0.25, 0.36, (165, 115, 72), 1)
        line(0.45, -0.36, 0.45, 0.36, (165, 115, 72), 1)
        line(0.68, -0.34, 0.68, 0.34, (165, 115, 72), 1)
        # Center wooden thwart bench
        poly([(0.46, -0.38), (0.54, -0.38), (0.54, 0.38), (0.46, 0.38)], thwart_col)
        # Round metal fish bucket with water and caught fish inside
        circle(0.28, 0.0, s * 0.18, (170, 190, 205) if not sunk else (60, 65, 72))
        circle(0.28, 0.0, s * 0.14, (65, 140, 205) if not sunk else (40, 50, 62))
        circle(0.28, 0.02, s * 0.06, (120, 160, 190) if not sunk else (55, 60, 70))
        # Stern transom board
        poly([(0.06, -0.42), (0.12, -0.42), (0.12, 0.42), (0.06, 0.42)], wood_dark)

    # 4. Sunk visual overlay (charred smoke and dark water)
    if sunk:
        poly([(0.04, -0.42), (0.76, -0.42), (0.98, 0.0), (0.76, 0.42), (0.04, 0.42)], (20, 25, 40), None)
        circle(0.5, 0.0, s * 0.4, (15, 20, 35))


def draw_ship_icon(g, cx, cy, sc, t, hull=None, bob=True):
    """Icon badge showing the iconic adventure sailboat."""
    draw_adventure_sailboat(g, cx, cy, sc=sc * 0.45, t=t, bob=bob)


# ================================================================== MARKS & HOVER
def draw_flame(g, cx, cy, t, ph):
    f = 1 + 0.2 * math.sin(t * 9 + ph)
    pygame.draw.circle(g.screen, mix(g.col("deep"), STATIC["hit"], 0.3), P(cx, cy), int(17 * f))
    pygame.draw.polygon(g.screen, STATIC["hit"], [
        P(cx - 10, cy + 10), P(cx - 7, cy - 2), P(cx - 3, cy + 1), P(cx, cy - 15 * f),
        P(cx + 3, cy - 1), P(cx + 8, cy - 4), P(cx + 10, cy + 10)
    ])
    pygame.draw.polygon(g.screen, STATIC["hit2"], [
        P(cx - 5, cy + 10), P(cx - 1, cy - 6 * f), P(cx + 1, cy - 6 * f), P(cx + 5, cy + 10)
    ])
    pygame.draw.circle(g.screen, (255, 250, 205), P(cx, cy + 6), 3)


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
    g.rrect(x + 2 - pulse / 2, y + 2 - pulse / 2, w - 4 + pulse, h - 4 + pulse,
            mix(g.col("shallow"), (255, 255, 255), 0.35), 10,
            STATIC["accent2"], 2)
    cx, cy = int(x + w / 2), int(y + h / 2)
    pygame.draw.line(g.screen, STATIC["accent2"], (cx - 9, cy), (cx + 9, cy), 2)
    pygame.draw.line(g.screen, STATIC["accent2"], (cx, cy - 9), (cx, cy + 9), 2)
    pygame.draw.circle(g.screen, STATIC["accent2"], (cx, cy), 7, 2)


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
            g.text(f"{prob[r, c] / tot * 100:.0f}", 11, (255, 255, 255) if v < .6 else (20, 20, 20),
                   x + w / 2, y + h / 2 - 7, True, True)


def draw_ring(g, lay, which, cell, t):
    x, y, w, h = lay.cell_rect(which, cell)
    rad = int(w / 2 - 2 + 3 * math.sin(t * 5))
    pygame.draw.circle(g.screen, STATIC["accent2"], P(x + w / 2, y + h / 2), rad, 4)
    pygame.draw.circle(g.screen, (255, 255, 255), P(x + w / 2, y + h / 2), max(2, rad - 5), 1)


# ================================================================== EFFECTS
def spawn_explosion(rng, parts, rings, x, y, big=False):
    for _ in range(36 if big else 22):
        a, sp = rng.random() * 6.283, rng.uniform(50, 230 if big else 170)
        col = rng.choice([STATIC["hit"], STATIC["hit2"], (255, 246, 200), (255, 120, 40)])
        parts.append({"x": x, "y": y, "vx": math.cos(a) * sp, "vy": math.sin(a) * sp - 40,
                      "life": rng.uniform(.4, .9), "max": .9, "color": col,
                      "size": rng.uniform(3, 6.5 if big else 5), "grav": 260, "kind": "spark"})
    rings.append([x, y, 0.0, (255, 220, 140), 46 if big else 34])


def spawn_splash(rng, parts, rings, x, y):
    for _ in range(14):
        a = -math.pi / 2 + rng.uniform(-0.8, 0.8)
        sp = rng.uniform(80, 190)
        parts.append({"x": x, "y": y, "vx": math.cos(a) * sp, "vy": math.sin(a) * sp,
                      "life": rng.uniform(.4, .8), "max": .8, "color": (210, 240, 255),
                      "size": rng.uniform(2, 4), "grav": 420, "kind": "drop"})
    rings.append([x, y, 0.0, (224, 246, 255), 30])
    rings.append([x, y, -0.15, (224, 246, 255), 22])


def spawn_smoke(rng, parts, x, y):
    parts.append({"x": x + rng.uniform(-8, 8), "y": y, "vx": rng.uniform(-8, 8),
                  "vy": rng.uniform(-34, -20), "life": 1.4, "max": 1.4,
                  "color": (95, 88, 115), "size": rng.uniform(4, 7), "grav": 0, "kind": "smoke"})


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
            pygame.draw.circle(g.screen, mix(p["color"], (175, 180, 210), 1 - k), P(p["x"], p["y"]), max(1, int(r)))
        else:
            pygame.draw.circle(g.screen, p["color"], P(p["x"], p["y"]), max(1, int(p["size"] * (0.4 + 0.6 * k))))


def projectile_pos(pr, now):
    p = max(0.0, min(1.0, (now - pr["t0"]) / pr["dur"]))
    x = pr["sx"] + (pr["ex"] - pr["sx"]) * p
    y = pr["sy"] + (pr["ey"] - pr["sy"]) * p - 130 * math.sin(math.pi * p)
    return x, y, p


def draw_projectile(g, pr, now):
    for k in range(6, 0, -1):
        x, y, _ = projectile_pos(dict(pr, t0=pr["t0"] + 0.035 * k), now)
        pygame.draw.circle(g.screen, mix((255, 190, 80), g.col("wave"), k / 7), P(x, y), max(1, 7 - k))
    x, y, p = projectile_pos(pr, now)
    pygame.draw.circle(g.screen, (255, 205, 95), P(x, y), 9)
    pygame.draw.circle(g.screen, (38, 32, 60), P(x, y), 6)
    pygame.draw.circle(g.screen, (200, 210, 235), P(x - 2, y - 2), 2)


# ================================================================== ISLAND SAGA / LEVEL MAP (MATCHING REFERENCE)
# 10 Level Node Positions along the winding turquoise channel
LEVEL_MAP_NODES = [
    (1,  160, 610),
    (2,  270, 510),
    (3,  390, 420),
    (4,  520, 490),
    (5,  650, 570),
    (6,  760, 460),
    (7,  860, 350),
    (8,  970, 260),
    (9,  1090, 340),
    (10, 1220, 450),
]


def draw_ellipse(screen, col, rect, width=0):
    if hasattr(pygame.draw, "ellipse"):
        pygame.draw.ellipse(screen, col, rect, width)
    else:
        rad = min(getattr(rect, "w", 20), getattr(rect, "h", 20)) // 2
        pygame.draw.rect(screen, col, rect, width, border_radius=rad)


def draw_palm_tree(screen, cx, cy, sc=1.0, sway=0.0):
    """Draw a cute cartoon coconut palm tree."""
    # Curved trunk
    trunk_pts = [
        P(cx, cy),
        P(cx + 6 * sc + sway * 4, cy - 25 * sc),
        P(cx + 12 * sc + sway * 8, cy - 50 * sc),
        P(cx + 6 * sc + sway * 10, cy - 70 * sc),
    ]
    pygame.draw.lines(screen, (135, 88, 48), False, trunk_pts, max(3, int(8 * sc)))
    top = trunk_pts[-1]
    # Green Palm Fronds
    frond_offsets = [
        (-38, -12), (38, -10), (-26, -30), (28, -28), (-4, -36), (42, 6), (-40, 4)
    ]
    for dx, dy in frond_offsets:
        fx, fy = top[0] + dx * sc + sway * 5, top[1] + dy * sc
        pygame.draw.circle(screen, (58, 185, 72), P(fx, fy), max(4, int(14 * sc)))
        pygame.draw.line(screen, (36, 140, 50), top, P(fx, fy), max(2, int(4 * sc)))
    # Brown coconuts
    for cdx, cdy in [(-4, 3), (4, 3), (0, 7)]:
        pygame.draw.circle(screen, (110, 70, 36), P(top[0] + cdx * sc, top[1] + cdy * sc), max(2, int(4.5 * sc)))


def draw_island_saga_map(g, progress, t, mx=0, my=0):
    """Draw full tropical archipelago level saga map (matching user reference).
    Returns list of (Rect, level_id) hitboxes for mouse clicks."""
    screen = g.screen
    # 1. Fullscreen Tropical Turquoise Ocean
    bands = 30
    for i in range(bands):
        y0 = i * H // bands
        frac = i / bands
        c = mix((52, 210, 238), (12, 95, 175), frac)
        pygame.draw.rect(screen, mix(c, (14, 28, 65), g.tod * 0.7),
                         pygame.Rect(0, y0, W, H // bands + 2))

    # Swimming fish in clear channel
    for f in FISH_SCHOOL:
        fx = (f["x"] + t * f["sp"]) % (W + 120) - 60
        fy = f["y"] + math.sin(t * 2.5 + f["ph"]) * 10
        fcol = mix(f["col"], (20, 50, 95), g.tod * 0.6)
        pygame.draw.polygon(screen, fcol, [
            P(fx + f["sz"], fy), P(fx, fy - f["sz"] * 0.45),
            P(fx - f["sz"] * 0.7, fy), P(fx, fy + f["sz"] * 0.45)
        ])

    # Glistening sunlight caustics
    for k in range(8):
        base_y = 60 + k * 85
        pts = wave_points(0, W, base_y, 4.0, 42 + k * 6, 1.3 + k * 0.15, t * 1.3 + k * 1.2, step=15)
        pygame.draw.lines(screen, (225, 250, 255), False, [P(x, y) for x, y in pts], 2)

    # 2. Four Tropical Sandy Islands with Features
    # --- ISLAND 1 (Bottom Left Shore): Sand beach + pirate ship + palms
    sand_col = (252, 222, 160)
    wet_sand = (220, 185, 125)
    surf_col = (250, 254, 255)
    # Wet sand rim & surf
    draw_ellipse(screen, surf_col, pygame.Rect(10, 470, 390, 320))
    draw_ellipse(screen, wet_sand, pygame.Rect(20, 480, 370, 300))
    draw_ellipse(screen, sand_col, pygame.Rect(30, 490, 350, 280))
    draw_palm_tree(screen, 90, 560, 1.1, math.sin(t * 1.8) * 0.6)
    draw_palm_tree(screen, 60, 680, 1.2, math.sin(t * 1.8 + 1) * 0.6)
    # Cartoon Pirate Ship on shore
    sh_x, sh_y = 200, 685
    pygame.draw.polygon(screen, (165, 95, 52), [
        P(sh_x - 45, sh_y), P(sh_x + 45, sh_y), P(sh_x + 35, sh_y + 24), P(sh_x - 35, sh_y + 24)
    ])
    pygame.draw.polygon(screen, (215, 60, 80), [
        P(sh_x - 20, sh_y - 20), P(sh_x + 20, sh_y - 20), P(sh_x + 20, sh_y), P(sh_x - 20, sh_y)
    ])
    pygame.draw.line(screen, (110, 65, 35), P(sh_x, sh_y - 20), P(sh_x, sh_y - 48), 3)
    pygame.draw.polygon(screen, (235, 45, 75), [
        P(sh_x, sh_y - 48), P(sh_x + 24, sh_y - 40), P(sh_x, sh_y - 32)
    ])

    # --- ISLAND 2 (Center Sandbar): Giant seashell with pink pearl + wooden dinghy
    draw_ellipse(screen, surf_col, pygame.Rect(580, 520, 190, 170))
    draw_ellipse(screen, wet_sand, pygame.Rect(590, 528, 170, 154))
    draw_ellipse(screen, sand_col, pygame.Rect(600, 536, 150, 138))
    # Open giant pink seashell & pearl
    sx, sy = 675, 580
    draw_ellipse(screen, (235, 140, 195), pygame.Rect(sx - 26, sy - 18, 52, 36))
    draw_ellipse(screen, (255, 185, 225), pygame.Rect(sx - 22, sy - 14, 44, 28))
    # Glowing shiny pink pearl
    pygame.draw.circle(screen, (255, 235, 245), P(sx, sy - 2), 11)
    pygame.draw.circle(screen, (255, 255, 255), P(sx - 3, sy - 5), 4)
    # Nearby moored wooden rowboat in water
    rb_x, rb_y = 530, 420
    pygame.draw.polygon(screen, (135, 80, 44), [
        P(rb_x - 24, rb_y), P(rb_x + 24, rb_y), P(rb_x + 18, rb_y + 14), P(rb_x - 18, rb_y + 14)
    ])
    pygame.draw.line(screen, (185, 130, 80), P(rb_x - 10, rb_y + 7), P(rb_x + 10, rb_y + 7), 3)

    # --- ISLAND 3 (Right Shore): Lush Headland with Pirate Lighthouse
    draw_ellipse(screen, surf_col, pygame.Rect(870, 140, 490, 440))
    draw_ellipse(screen, wet_sand, pygame.Rect(885, 152, 460, 416))
    draw_ellipse(screen, sand_col, pygame.Rect(900, 165, 430, 390))
    draw_ellipse(screen, (76, 205, 92), pygame.Rect(930, 190, 370, 340))
    draw_palm_tree(screen, 940, 300, 1.15, math.sin(t * 1.8 + 2) * 0.6)
    draw_palm_tree(screen, 1260, 330, 1.25, math.sin(t * 1.8 + 3) * 0.6)
    # Pirate Lighthouse with telescope and purple conical roof
    lh_x, lh_y = 1040, 200
    pygame.draw.rect(screen, (245, 238, 225), pygame.Rect(lh_x - 22, lh_y - 75, 44, 75), border_radius=6)
    pygame.draw.rect(screen, (215, 60, 80), pygame.Rect(lh_x - 22, lh_y - 50, 44, 14))
    # Roof (purple cone)
    pygame.draw.polygon(screen, (160, 68, 220), [
        P(lh_x - 28, lh_y - 75), P(lh_x + 28, lh_y - 75), P(lh_x, lh_y - 120)
    ])
    # Pirate skull flag
    pygame.draw.line(screen, (110, 65, 35), P(lh_x, lh_y - 120), P(lh_x, lh_y - 142), 3)
    pygame.draw.polygon(screen, (225, 45, 75), [
        P(lh_x, lh_y - 142), P(lh_x + 26, lh_y - 134), P(lh_x, lh_y - 126)
    ])
    # Telescope
    pygame.draw.line(screen, (255, 195, 45), P(lh_x - 10, lh_y - 82), P(lh_x - 38, lh_y - 94), 6)

    # --- ISLAND 4 (Top Left Cove): Cottage with Friendly Pink Octopus
    draw_ellipse(screen, surf_col, pygame.Rect(40, 30, 400, 270))
    draw_ellipse(screen, wet_sand, pygame.Rect(55, 42, 370, 246))
    draw_ellipse(screen, sand_col, pygame.Rect(70, 54, 340, 222))
    draw_palm_tree(screen, 320, 140, 1.1, math.sin(t * 1.8 + 4) * 0.6)
    # Pirate cottage
    cot_x, cot_y = 190, 160
    pygame.draw.rect(screen, (245, 215, 175), pygame.Rect(cot_x - 45, cot_y - 35, 90, 55), border_radius=8)
    pygame.draw.polygon(screen, (225, 115, 52), [
        P(cot_x - 55, cot_y - 35), P(cot_x + 55, cot_y - 35), P(cot_x, cot_y - 75)
    ])
    # Pink Octopus on roof
    oct_x, oct_y = cot_x, cot_y - 72
    pygame.draw.circle(screen, (255, 105, 155), P(oct_x, oct_y), 24)
    # Pirate hat
    pygame.draw.polygon(screen, (180, 75, 230), [
        P(oct_x - 28, oct_y - 14), P(oct_x + 28, oct_y - 14), P(oct_x, oct_y - 36)
    ])
    # Eyepatch
    pygame.draw.circle(screen, (25, 20, 35), P(oct_x - 8, oct_y - 2), 6)
    pygame.draw.circle(screen, (255, 255, 255), P(oct_x + 8, oct_y - 2), 6)
    pygame.draw.circle(screen, (25, 20, 35), P(oct_x + 8, oct_y - 2), 3)

    # 3. Winding Dotted Bubble Trail between Nodes
    for idx in range(len(LEVEL_MAP_NODES) - 1):
        _, x1, y1 = LEVEL_MAP_NODES[idx]
        _, x2, y2 = LEVEL_MAP_NODES[idx + 1]
        steps = 7
        for s_idx in range(1, steps):
            frac = s_idx / steps
            bx = x1 + (x2 - x1) * frac + math.sin(frac * math.pi) * 8
            by = y1 + (y2 - y1) * frac
            # Translucent bubble
            pygame.draw.circle(screen, (255, 255, 255), P(bx, by), 4)
            pygame.draw.circle(screen, (80, 215, 255), P(bx, by), 6, 2)

    # 4. Render the 10 Level Nodes (3D Candy Cylinders)
    hitboxes = []
    rad = 32
    for lvl_id, nx, ny in LEVEL_MAP_NODES:
        unlocked = progress.is_unlocked(lvl_id)
        stars = progress.get_stars(lvl_id)
        is_cur = (lvl_id == progress.unlocked_level)
        over = (mx - nx) ** 2 + (my - ny) ** 2 <= rad ** 2

        # 3D Drop Shadow
        g.rrect(nx - rad, ny - rad + 8, rad * 2, rad * 2, (15, 25, 55), rad)

        # Node styling based on status
        if stars > 0:
            # Completed: Golden / Amber candy cylinder
            base_col = (195, 110, 15)
            face_col = (255, 215, 55) if not over else (255, 235, 110)
            rim_col  = (255, 245, 185)
            num_col  = (38, 22, 10)
        elif is_cur:
            # Active Next: Juicy Magenta / Pink candy with glowing ring
            base_col = (175, 25, 95)
            face_col = (255, 75, 165) if not over else (255, 115, 195)
            rim_col  = (255, 255, 255)
            num_col  = (255, 255, 255)
            # Pulsating Golden Glow Halo
            halo_r = int(rad + 8 + 4 * math.sin(t * 5))
            pygame.draw.circle(screen, (255, 230, 80), P(nx, ny), halo_r, 3)
            pygame.draw.circle(screen, (255, 255, 255), P(nx, ny), halo_r - 2, 1)
        else:
            # Locked: Slate purple
            base_col = (68, 62, 95)
            face_col = (115, 110, 145) if not over else (135, 130, 168)
            rim_col  = (165, 160, 195)
            num_col  = (205, 200, 228)

        # 3D Bevel base
        pygame.draw.circle(screen, base_col, P(nx, ny + 6), rad)
        # Main Face
        pygame.draw.circle(screen, face_col, P(nx, ny), rad)
        pygame.draw.circle(screen, rim_col, P(nx, ny), rad, 3)
        # Top shine gloss
        draw_ellipse(screen, (255, 255, 255), pygame.Rect(nx - rad + 8, ny - rad + 5, rad * 2 - 16, rad - 6))
        pygame.draw.circle(screen, face_col, P(nx, ny + 2), rad - 6)

        # Number text: "01", "02", ... "10"
        num_str = f"{lvl_id:02d}"
        g.text(num_str, 20, num_col, nx, ny - 11, bold=True, center=True, shadow=True)

        # Golden Stars under completed nodes (⭐⭐⭐)
        if stars > 0:
            star_w = 16
            start_x = nx - (stars * star_w) // 2 + star_w // 2
            for s_i in range(stars):
                st_x = start_x + s_i * star_w
                st_y = ny + rad + 8
                # Cute 5-point star
                pygame.draw.circle(screen, (255, 215, 45), P(st_x, st_y), 6)
                pygame.draw.circle(screen, (255, 255, 255), P(st_x - 1, st_y - 1), 2)

        hitboxes.append((pygame.Rect(nx - rad, ny - rad, rad * 2, rad * 2), lvl_id))

    return hitboxes
