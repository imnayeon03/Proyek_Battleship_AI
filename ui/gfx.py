"""ui/gfx.py - Casual cartoon / mobile casual game aesthetic helper.
Theme: Vibrant pastel sky, fluffy clouds, 3D bubbly cartoon text, candy pill buttons,
and capsule progress bars (matching Tile Match / casual mobile pop art style).
"""
import math
import os
import pygame

# Casual Pop / Pastel Sky Palette
DAY = dict(
    sky1=(70, 155, 248),      # Azure / Cerulean top sky
    sky2=(170, 180, 246),     # Dreamy lavender-blue middle sky
    sky3=(245, 220, 238),     # Soft pastel pink/peach near horizon
    sea1=(45, 192, 235),      # Vibrant Caribbean cyan
    sea2=(20, 115, 195),      # Deep cartoon ocean blue
    crest=(245, 252, 255),    # Foam white
    panel=(44, 35, 86),       # Deep rich purple-indigo card
    edge=(145, 130, 228),     # Bright pastel lilac border
    pill=(34, 25, 68),        # Dark capsule container
    text=(255, 255, 255),     # Crisp white
    dim=(205, 198, 238),      # Sweet pastel lavender
    deep=(22, 108, 182),      # Tropical ocean depth
    shallow=(65, 215, 245),   # Bright shallow cyan
    frame=(125, 115, 210),    # Candy purple frame
    frame_in=(18, 42, 92),    # Marine blue
    wave=(225, 250, 255),     # White foam sparkles
    ink=(22, 16, 48),         # Deep outline purple
)

NIGHT = dict(
    sky1=(22, 18, 56),        # Twilight midnight indigo
    sky2=(68, 40, 110),       # Magenta twilight
    sky3=(115, 65, 135),      # Dreamy purple sunset glow
    sea1=(25, 52, 115),       # Moonlit deep blue
    sea2=(12, 22, 58),        # Nocturnal ocean
    crest=(185, 205, 255),    # Soft blue moonlit crest
    panel=(30, 24, 62),       # Dark twilight card
    edge=(120, 95, 195),      # Neon lavender edge
    pill=(22, 15, 46),        # Dark midnight capsule
    text=(245, 248, 255),     # Moonlight white
    dim=(170, 165, 212),      # Dim lavender
    deep=(12, 32, 78),        # Dark depth
    shallow=(36, 95, 160),    # Moonlit surface
    frame=(95, 78, 165),      # Muted purple frame
    frame_in=(8, 18, 48),     # Deep indigo
    wave=(145, 185, 245),     # Moon glow wave
    ink=(8, 6, 22),           # Dark night ink
)

STATIC = dict(
    accent=(255, 238, 165),   # Warm custard / cream (like 'MATCH' text)
    accent2=(255, 168, 32),   # Juicy candy orange
    good=(72, 226, 80),       # Vibrant candy lime neon (like 'Loading...' bar)
    bad=(250, 65, 88),        # Juicy candy strawberry
    warn=(255, 195, 30),      # Sunny gold
    hit=(255, 105, 35),       # Flame orange
    hit2=(255, 215, 60),      # Spark gold
    white=(255, 255, 255),
    blue=(52, 150, 255),      # Royal sky blue
    purple=(152, 88, 242),    # Grape jelly purple
    red=(248, 62, 85),        # Cherry red
    gray=(82, 76, 112),       # Lavender slate
)

# Candy button face colors
BTN = {
    "primary": (255, 172, 28),   # Juicy mango/amber
    "good":    (72, 218, 78),    # Fresh candy lime-green
    "normal":  (52, 150, 255),   # Vibrant sky-blue
    "danger":  (248, 62, 88),    # Strawberry ruby red
    "purple":  (152, 88, 242),   # Grape purple
    "coral":   (235, 62, 48),    # Glossy coral red (matching 'Seviye 12' pill button)
    "off":     (82, 75, 110),    # Soft muted lavender
}

# Dark 3D bevel base colors for candy buttons
BTN_BEVEL = {
    "primary": (195, 102, 12),
    "good":    (38, 148, 46),
    "normal":  (24, 94, 195),
    "danger":  (175, 28, 54),
    "purple":  (102, 45, 175),
    "coral":   (168, 26, 18),
    "off":     (48, 42, 68),
}


def clamp(v):
    return max(0, min(255, int(v)))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, k):
    return tuple(clamp(v * k) for v in c)


class Gfx:
    FONT_FILE = os.path.join(os.path.dirname(__file__), "..", "assets", "LilitaOne.ttf")
    FALLBACK_FONTS = "arialrounded,cooperblack,bauhaus93,comicsansms,trebuchetms,arial"

    def __init__(self, screen):
        self.screen = screen
        self._fonts = {}
        self.buttons = []                    # [(Rect, tag)] rebuilt each frame
        self.tod = 0.0                       # 0 = day, 1 = night
        self._dim = {}

    def col(self, name):
        if name in STATIC:
            return STATIC[name]
        return mix(DAY[name], NIGHT[name], self.tod)

    # ------------------------------------------------------------ text
    def font(self, size, bold=False):
        k = (size, bold)
        if k not in self._fonts:
            loaded = None
            if os.path.exists(self.FONT_FILE) and hasattr(pygame.font, "Font"):
                try:
                    loaded = pygame.font.Font(self.FONT_FILE, size)
                except Exception:
                    loaded = None
            if loaded is None:
                if hasattr(pygame.font, "SysFont"):
                    loaded = pygame.font.SysFont(self.FALLBACK_FONTS, size, bold=bold)
                else:
                    loaded = pygame.font.Font(None, size)
            self._fonts[k] = loaded
        return self._fonts[k]

    def text_size(self, text, size, bold=False):
        return self.font(size, bold).size(text)

    def text(self, s, size, color, x, y, bold=False, center=False, shadow=False):
        w, _ = self.text_size(s, size, bold)
        px = int(x - w / 2) if center else int(x)
        if shadow:
            # Dark cartoon outline / shadow
            outline_col = (26, 18, 54)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (0, 2), (2, 2)):
                self.screen.blit(self.font(size, bold).render(s, True, outline_col), (px + dx, int(y) + dy))
        self.screen.blit(self.font(size, bold).render(s, True, color), (px, int(y)))
        return w

    def bubble_text(self, s, size, face_color, outline_color, x, y, bold=True, center=True, extrude=7):
        """Render 3D bubbly cartoon title text matching the 'Tile Match' logo style.
        Features thick dark outline, 3D bottom bevel extrusion, and top glossy highlight."""
        f = self.font(size, bold)
        w, h = f.size(s)
        px = int(x - w / 2) if center else int(x)
        py = int(y)

        # 1. 3D extrusion downward
        for dy in range(1, extrude + 1):
            for dx in (-3, -2, -1, 0, 1, 2, 3):
                self.screen.blit(f.render(s, True, outline_color), (px + dx, py + dy))

        # 2. Thick rounded cartoon stroke around the letters
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                if dx * dx + dy * dy <= 17:
                    self.screen.blit(f.render(s, True, outline_color), (px + dx, py + dy))

        # 3. Main face
        face_surf = f.render(s, True, face_color)
        self.screen.blit(face_surf, (px, py))

        # 4. Top subtle glossy highlight shine
        shine_col = mix(face_color, (255, 255, 255), 0.45)
        self.screen.blit(f.render(s, True, shine_col), (px, py - 1))
        self.screen.blit(face_surf, (px, py))
        return w

    def wrap(self, s, size, width, bold=False):
        lines, cur = [], ""
        for word in s.split():
            t = (cur + " " + word).strip()
            if self.text_size(t, size, bold)[0] <= width or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = word
        return lines + ([cur] if cur else [])

    def paragraph(self, s, size, color, x, y, width, gap=3, bold=False):
        for line in self.wrap(s, size, width, bold):
            self.text(line, size, color, x, y, bold)
            y += self.text_size(line, size, bold)[1] + gap
        return y

    # ------------------------------------------------------------ shapes
    def rrect(self, x, y, w, h, color, radius=16, border=None, bw=2):
        r = pygame.Rect(int(x), int(y), int(w), int(h))
        pygame.draw.rect(self.screen, color, r, border_radius=radius)
        if border:
            pygame.draw.rect(self.screen, border, r, bw, border_radius=radius)

    def dim(self, alpha=150):
        """Translucent dark overlay for modal dialogs."""
        if alpha not in self._dim:
            s = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            s.fill((16, 12, 38, alpha))
            self._dim[alpha] = s
        self.screen.blit(self._dim[alpha], (0, 0))

    screen_w, screen_h = 1360, 740

    def card(self, x, y, w, h, title=None):
        """Casual rounded card with soft purple-indigo fill and sweet lilac border."""
        # Drop shadow
        self.rrect(x + 2, y + 6, w, h, (18, 14, 42), 22)
        # Main body
        self.rrect(x, y, w, h, self.col("panel"), 22, self.col("edge"), 2)
        # Inner soft top highlight rim
        self.rrect(x + 4, y + 3, w - 8, 4, mix(self.col("edge"), (255, 255, 255), 0.25), 3)
        if title:
            # Cute pill title bar
            tw, th = self.text_size(title.upper(), 13, True)[0] + 32, 28
            self.rrect(x + 14, y + 10, tw, th, (30, 22, 62), 14, self.col("edge"), 1)
            self.text(title.upper(), 12, STATIC["accent"], x + 14 + tw / 2, y + 16, True, center=True)

    def pill(self, x, y, s, size=14, fill=None, color=None, border=None, h=None, right=False, center=False):
        """Casual rounded pill capsule badge."""
        w = self.text_size(s, size, True)[0] + 28
        h = h or size + 16
        if center:
            x -= w // 2
        elif right:
            x -= w
        # 3D shadow
        self.rrect(x + 1, y + 4, w, h, (18, 12, 38), h // 2)
        # Body
        body_col = fill or self.col("pill")
        self.rrect(x, y, w, h, body_col, h // 2, border or (self.col("edge") if not fill else shade(body_col, 0.7)), 2)
        # Top shine
        self.rrect(x + 3, y + 2, w - 6, max(3, h // 3), mix(body_col, (255, 255, 255), 0.25), (h // 3) // 2)
        self.text(s, size, color or self.col("text"), x + w / 2, y + (h - size) / 2 - 2, True, True, shadow=True)
        return w

    def bar(self, x, y, w, h, frac, color):
        """Capsule health bar matching the 'Loading...' bar style from Tile Match:
        Deep purple capsule with glowing neon-green rounded fill."""
        # Outer dark purple container capsule
        self.rrect(x, y + 2, w, h, (18, 12, 36), h // 2)
        self.rrect(x, y, w, h, (32, 22, 60), h // 2, (52, 40, 88), 2)

        fw = max(0, int((w - 4) * max(0.0, min(1.0, frac))))
        if fw > h // 2:
            # Glowing neon candy bar
            bar_col = color if color in ((72, 226, 80), (250, 65, 88), (255, 195, 30)) else STATIC["good"]
            self.rrect(x + 2, y + 2, fw, h - 4, bar_col, (h - 4) // 2)
            # Top glossy shine on the bar
            self.rrect(x + 4, y + 3, max(4, fw - 8), max(3, (h - 4) // 3),
                       mix(bar_col, (255, 255, 255), 0.45), (h - 4) // 4)

    # ------------------------------------------------------------ candy buttons
    def _hover(self, x, y, w, h):
        mx, my = pygame.mouse.get_pos()
        return x <= mx <= x + w and y <= my <= y + h

    def button(self, x, y, w, h, label, tag, style="normal", enabled=True, size=18):
        """Juicy 3D candy pill button with deep bevel, glossy curved reflection,
        and bubbly pop styling."""
        face_base = BTN.get(style if enabled else "off", BTN["normal"])
        bevel_base = BTN_BEVEL.get(style if enabled else "off", BTN_BEVEL["normal"])
        over = enabled and self._hover(x, y, w, h)
        pressed = 4 if over else 0

        rad = min(24, h // 2)
        # 1. Dark drop shadow
        self.rrect(x + 1, y + 7, w, h, (16, 10, 36), rad)

        # 2. 3D bottom bevel base
        self.rrect(x, y + 4, w, h, bevel_base, rad)

        # 3. Main button face (shifts down slightly on hover for bouncy feel)
        face_y = y + pressed
        face_col = mix(face_base, (255, 255, 255), 0.16) if over else face_base
        self.rrect(x, face_y, w, h, face_col, rad)

        # 4. Top curved glossy pill shine (signature mobile casual game look)
        shine_h = max(5, int(h * 0.38))
        self.rrect(x + 5, face_y + 3, w - 10, shine_h, mix(face_col, (255, 255, 255), 0.38), rad - 4)

        # 5. Crisp cartoon outline
        outline_col = (24, 16, 52)
        if style == "coral":
            # Outer white/cream thick capsule border (matching 'Seviye 12' pill button)
            pygame.draw.rect(self.screen, (255, 252, 240), pygame.Rect(int(x), int(face_y), int(w), int(h)), 4, border_radius=rad)
            # Cute corner ribbon tag
            tag_w, tag_h = 34, 24
            tx, ty = int(x + w - tag_w - 6), int(face_y - 8)
            self.rrect(tx, ty, tag_w, tag_h, (255, 175, 25), 8, (255, 255, 255), 2)
            self.text("x2", 12, (255, 255, 255), tx + tag_w / 2, ty + 3, True, True, shadow=True)
        else:
            pygame.draw.rect(self.screen, outline_col, pygame.Rect(int(x), int(face_y), int(w), int(h)), 2, border_radius=rad)

        # 6. Button label with clean 3D text
        txt_col = (255, 255, 255) if enabled else self.col("dim")
        self.text(label, size, txt_col, x + w / 2, face_y + (h - size) / 2 - 2, True, True, shadow=enabled)

        if enabled:
            self.buttons.append((pygame.Rect(int(x), int(y), int(w), int(h + 7)), tag))

    def tool(self, x, y, w, h, title, sub, key, tag, color, active=False, enabled=True):
        """Tool card with candy styling, bright circle badge, and clean text."""
        over = enabled and self._hover(x, y, w, h)
        fill = STATIC["purple"] if active else (mix(self.col("panel"), (255, 255, 255), 0.14) if over else self.col("panel"))
        self.rrect(x + 1, y + 4, w, h, (16, 12, 36), 14)
        self.rrect(x, y, w, h, fill, 14, (255, 235, 140) if active else self.col("edge"), 2)
        # Top shine
        self.rrect(x + 3, y + 2, w - 6, h // 3, mix(fill, (255, 255, 255), 0.15), 10)

        cx, cy = int(x + 28), int(y + h / 2)
        # Icon badge with candy 3D look
        pygame.draw.circle(self.screen, (20, 14, 44), (cx, cy + 2), 16)
        pygame.draw.circle(self.screen, color, (cx, cy), 15)
        pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), 15, 2)
        self.text(key, 15, (255, 255, 255), cx, cy - 10, True, True, shadow=True)

        self.text(title, 14, (255, 255, 255) if enabled else self.col("dim"), x + 54, y + 9, True)
        self.text(sub, 11, self.col("dim"), x + 54, y + 29, True)
        if enabled:
            self.buttons.append((pygame.Rect(int(x), int(y), int(w), int(h)), tag))

    def hit_test(self, pos):
        for rect, tag in reversed(self.buttons):
            if rect.collidepoint(pos):
                return tag
        return None
