"""ui/gfx.py - helper gambar Pygame: palet SIANG/MALAM, teks, tombol 3D metalik, kartu, pil, bar."""
import pygame

DAY = dict(sky1=(96, 190, 255), sky2=(196, 234, 255), sea1=(52, 170, 214), sea2=(18, 96, 160),
           crest=(224, 246, 255), panel=(24, 52, 90), edge=(80, 130, 185), pill=(18, 44, 78),
           text=(230, 240, 255), dim=(160, 192, 224), deep=(16, 112, 172), shallow=(76, 204, 224),
           frame=(100, 150, 200), frame_in=(14, 48, 92), wave=(214, 246, 255), ink=(12, 36, 66))
NIGHT = dict(sky1=(6, 10, 36), sky2=(32, 46, 100), sea1=(16, 44, 98), sea2=(5, 12, 38),
             crest=(110, 150, 215), panel=(10, 18, 46), edge=(44, 72, 130), pill=(6, 12, 32),
             text=(220, 232, 255), dim=(110, 140, 192), deep=(6, 24, 62), shallow=(24, 78, 128),
             frame=(80, 100, 150), frame_in=(4, 10, 32), wave=(120, 170, 232), ink=(4, 8, 24))
STATIC = dict(accent=(255, 200, 60), accent2=(255, 140, 40), good=(60, 210, 110), bad=(240, 80, 80),
              warn=(255, 183, 3), hit=(255, 90, 31), hit2=(255, 183, 3), white=(255, 255, 255),
              blue=(40, 110, 210), red=(210, 55, 75), gray=(55, 68, 88))
BTN = {"normal": (40, 110, 210), "primary": (210, 148, 20), "good": (40, 170, 90),
       "danger": (200, 50, 65), "off": (50, 60, 80)}


def clamp(v):
    return max(0, min(255, int(v)))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, k):
    return tuple(clamp(v * k) for v in c)


class Gfx:
    FONT = "nunito,baloo2,trebuchetms,verdana,arial"

    def __init__(self, screen):
        self.screen = screen
        self._fonts = {}
        self.buttons = []                    # [(Rect, tag)] rebuilt every frame
        self.tod = 0.0                       # 0 = day, 1 = night (smooth transition)
        self._dim = {}

    def col(self, name):
        if name in STATIC:
            return STATIC[name]
        return mix(DAY[name], NIGHT[name], self.tod)

    # ------------------------------------------------------------ text
    def font(self, size, bold=False):
        k = (size, bold)
        if k not in self._fonts:
            self._fonts[k] = pygame.font.SysFont(self.FONT, size, bold=bold)
        return self._fonts[k]

    def text_size(self, text, size, bold=False):
        return self.font(size, bold).size(text)

    def text(self, s, size, color, x, y, bold=False, center=False, shadow=False):
        w, _ = self.text_size(s, size, bold)
        px = int(x - w / 2) if center else int(x)
        if shadow:
            self.screen.blit(self.font(size, bold).render(s, True, shade(color, 0.22)), (px + 2, int(y) + 3))
        self.screen.blit(self.font(size, bold).render(s, True, color), (px, int(y)))
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
    def rrect(self, x, y, w, h, color, radius=12, border=None, bw=2):
        r = pygame.Rect(int(x), int(y), int(w), int(h))
        pygame.draw.rect(self.screen, color, r, border_radius=radius)
        if border:
            pygame.draw.rect(self.screen, border, r, bw, border_radius=radius)

    def dim(self, alpha=150):
        """Transparent dark overlay for modal backgrounds."""
        if alpha not in self._dim:
            s = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            s.fill((0, 0, 0, alpha))
            self._dim[alpha] = s
        self.screen.blit(self._dim[alpha], (0, 0))

    screen_w, screen_h = 1360, 740

    def card(self, x, y, w, h, title=None):
        # Darker, more metallic-looking card with gradient-ish effect
        self.rrect(x + 2, y + 4, w, h, shade(self.col("panel"), 0.35), 18)
        self.rrect(x, y, w, h, self.col("panel"), 18)
        # Inner top-edge highlight (metallic sheen)
        self.rrect(x + 2, y + 2, w - 4, 3, mix(self.col("edge"), (255, 255, 255), 0.12), 2)
        # Border
        pygame.draw.rect(self.screen, self.col("edge"),
                         pygame.Rect(int(x), int(y), int(w), int(h)), 1, border_radius=18)
        if title:
            # Title bar strip
            self.rrect(x + 1, y + 1, w - 2, 28, shade(self.col("edge"), 0.28), 17)
            self.text(title.upper(), 12, self.col("dim"), x + 16, y + 8, True)

    def pill(self, x, y, s, size=14, fill=None, color=None, border=None, h=None, right=False):
        w = self.text_size(s, size, True)[0] + 28
        h = h or size + 14
        if right:
            x -= w
        self.rrect(x + 1, y + 3, w, h, shade(fill or self.col("pill"), 0.5), h // 2)
        self.rrect(x, y, w, h, fill or self.col("pill"), h // 2, border)
        self.text(s, size, color or self.col("text"), x + w / 2, y + (h - size) / 2 - 3, True, True)
        return w

    def bar(self, x, y, w, h, frac, color):
        self.rrect(x, y, w, h, shade(self.col("pill"), 0.9), h // 2)
        fw = max(0, int((w - 4) * max(0.0, min(1.0, frac))))
        if fw > h // 2:
            self.rrect(x + 2, y + 2, fw, h - 4, color, (h - 4) // 2)
            # Shine strip on bar
            self.rrect(x + 2, y + 2, fw, (h - 4) // 3,
                       mix(color, (255, 255, 255), 0.3), (h - 4) // 2)

    # ------------------------------------------------------------ buttons
    def _hover(self, x, y, w, h):
        mx, my = pygame.mouse.get_pos()
        return x <= mx <= x + w and y <= my <= y + h

    def button(self, x, y, w, h, label, tag, style="normal", enabled=True, size=18):
        base = BTN[style if enabled else "off"]
        over = enabled and self._hover(x, y, w, h)
        pressed_offset = 3 if over else 0
        face_y = y + pressed_offset

        # Drop shadow / 3D side
        self.rrect(x + 1, y + 5, w, h, shade(base, 0.38), 14)
        # Main face
        face_col = mix(base, (255, 255, 255), 0.14) if over else base
        self.rrect(x, face_y, w, h, face_col, 14)
        # Metallic top shine (two-tone gradient simulation)
        self.rrect(x + 4, face_y + 3, w - 8, h // 3, mix(base, (255, 255, 255), 0.30), 10)
        self.rrect(x + 4, face_y + 3 + h // 3, w - 8, h // 6, mix(base, (255, 255, 255), 0.10), 6)
        # Border
        border_col = mix(base, (255, 255, 255), 0.22) if over else shade(base, 0.65)
        pygame.draw.rect(self.screen, border_col,
                         pygame.Rect(int(x), int(face_y), int(w), int(h)), 2, border_radius=14)
        # Label
        c = (255, 255, 255) if enabled else self.col("dim")
        self.text(label, size, c, x + w / 2, face_y + (h - size) / 2 - 3, True, True, shadow=enabled)
        if enabled:
            self.buttons.append((pygame.Rect(int(x), int(y), int(w), int(h + 5)), tag))

    def tool(self, x, y, w, h, title, sub, key, tag, color, active=False, enabled=True):
        """Tool card: round icon + title + subtitle."""
        over = enabled and self._hover(x, y, w, h)
        fill = STATIC["blue"] if active else (mix(self.col("pill"), (255, 255, 255), 0.12) if over else self.col("pill"))
        self.rrect(x + 1, y + 3, w, h, shade(fill, 0.4), 12)
        self.rrect(x, y, w, h, fill, 12)
        # Shine
        self.rrect(x + 2, y + 2, w - 4, h // 3, mix(fill, (255, 255, 255), 0.12), 10)
        border_col = (160, 210, 255) if active else self.col("edge")
        pygame.draw.rect(self.screen, border_col,
                         pygame.Rect(int(x), int(y), int(w), int(h)), 1, border_radius=12)
        cx, cy = int(x + 26), int(y + h / 2)
        # Icon circle
        pygame.draw.circle(self.screen, shade(color, 0.5), (cx, cy + 2), 17)
        pygame.draw.circle(self.screen, (255, 255, 255) if enabled else self.col("dim"), (cx, cy), 18)
        pygame.draw.circle(self.screen, color, (cx, cy), 14)
        self.text(key, 15, (255, 255, 255), cx, cy - 10, True, True)
        self.text(title, 15, self.col("text") if enabled else self.col("dim"), x + 52, y + 9, True)
        self.text(sub, 11, self.col("dim"), x + 52, y + 29, True)
        if enabled:
            self.buttons.append((pygame.Rect(int(x), int(y), int(w), int(h)), tag))

    def hit_test(self, pos):
        for rect, tag in reversed(self.buttons):
            if rect.collidepoint(pos):
                return tag
        return None
