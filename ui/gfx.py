"""ui/gfx.py - helper gambar Pygame: palet SIANG/MALAM, teks, tombol 3D, kartu, pil, bar."""
import pygame

DAY = dict(sky1=(96, 190, 255), sky2=(196, 234, 255), sea1=(52, 170, 214), sea2=(18, 96, 160),
           crest=(224, 246, 255), panel=(34, 88, 138), edge=(120, 180, 225), pill=(26, 68, 110),
           text=(255, 255, 255), dim=(196, 224, 248), deep=(16, 112, 172), shallow=(76, 204, 224),
           frame=(158, 200, 232), frame_in=(22, 74, 124), wave=(214, 246, 255), ink=(12, 36, 66))
NIGHT = dict(sky1=(6, 10, 36), sky2=(32, 46, 100), sea1=(16, 44, 98), sea2=(5, 12, 38),
             crest=(110, 150, 215), panel=(16, 28, 64), edge=(66, 98, 160), pill=(10, 18, 44),
             text=(240, 248, 255), dim=(140, 166, 212), deep=(6, 24, 62), shallow=(24, 78, 128),
             frame=(122, 136, 178), frame_in=(8, 20, 48), wave=(120, 170, 232), ink=(4, 8, 24))
STATIC = dict(accent=(255, 200, 60), accent2=(255, 140, 40), good=(74, 222, 128), bad=(248, 96, 96),
              warn=(255, 183, 3), hit=(255, 90, 31), hit2=(255, 183, 3), white=(255, 255, 255),
              blue=(60, 130, 230), red=(226, 70, 90), gray=(70, 84, 104))
BTN = {"normal": STATIC["blue"], "primary": (255, 176, 40), "good": (52, 190, 110), "danger": STATIC["red"],
       "off": STATIC["gray"]}


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
        self.buttons = []                    # [(Rect, tag)] dibangun ulang tiap frame
        self.tod = 0.0                       # 0 = siang, 1 = malam (transisi halus)
        self._dim = {}

    def col(self, name):
        if name in STATIC:
            return STATIC[name]
        return mix(DAY[name], NIGHT[name], self.tod)

    # ------------------------------------------------------------ teks
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
            self.screen.blit(self.font(size, bold).render(s, True, shade(color, 0.25)), (px + 2, int(y) + 3))
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

    # ------------------------------------------------------------ bentuk
    def rrect(self, x, y, w, h, color, radius=12, border=None, bw=2):
        r = pygame.Rect(int(x), int(y), int(w), int(h))
        pygame.draw.rect(self.screen, color, r, border_radius=radius)
        if border:
            pygame.draw.rect(self.screen, border, r, bw, border_radius=radius)

    def dim(self, alpha=150):
        """Lapisan gelap transparan untuk latar jendela modal."""
        if alpha not in self._dim:
            s = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            s.fill((0, 0, 0, alpha))
            self._dim[alpha] = s
        self.screen.blit(self._dim[alpha], (0, 0))

    screen_w, screen_h = 1360, 740

    def card(self, x, y, w, h, title=None):
        self.rrect(x, y + 5, w, h, shade(self.col("panel"), 0.55), 18)
        self.rrect(x, y, w, h, self.col("panel"), 18, self.col("edge"), 2)
        if title:
            self.text(title.upper(), 13, self.col("dim"), x + 18, y + 14, True)

    def pill(self, x, y, s, size=14, fill=None, color=None, border=None, h=None, right=False):
        w = self.text_size(s, size, True)[0] + 28
        h = h or size + 14
        if right:
            x -= w
        self.rrect(x, y + 3, w, h, shade(fill or self.col("pill"), 0.6), h // 2)
        self.rrect(x, y, w, h, fill or self.col("pill"), h // 2, border)
        self.text(s, size, color or self.col("text"), x + w / 2, y + (h - size) / 2 - 3, True, True)
        return w

    def bar(self, x, y, w, h, frac, color):
        self.rrect(x, y, w, h, shade(self.col("pill"), 0.8), h // 2)
        fw = max(0, int((w - 4) * max(0.0, min(1.0, frac))))
        if fw > h // 2:
            self.rrect(x + 2, y + 2, fw, h - 4, color, (h - 4) // 2)

    # ------------------------------------------------------------ tombol
    def _hover(self, x, y, w, h):
        mx, my = pygame.mouse.get_pos()
        return x <= mx <= x + w and y <= my <= y + h

    def button(self, x, y, w, h, label, tag, style="normal", enabled=True, size=18):
        base = BTN[style if enabled else "off"]
        over = enabled and self._hover(x, y, w, h)
        face_y = y + (3 if over else 0)
        self.rrect(x, y + 6, w, h, shade(base, 0.55), 16)                   # sisi bawah (efek 3D)
        self.rrect(x, face_y, w, h, mix(base, (255, 255, 255), 0.18) if over else base, 16, shade(base, 0.7), 2)
        self.rrect(x + 6, face_y + 4, w - 12, h // 3, mix(base, (255, 255, 255), 0.25), 10)   # kilap
        c = (255, 255, 255) if enabled else self.col("dim")
        self.text(label, size, c, x + w / 2, face_y + (h - size) / 2 - 3, True, True, shadow=enabled)
        if enabled:
            self.buttons.append((pygame.Rect(int(x), int(y), int(w), int(h + 6)), tag))

    def tool(self, x, y, w, h, title, sub, key, tag, color, active=False, enabled=True):
        """Kartu peralatan bergaya referensi: ikon bulat + judul + keterangan kecil."""
        over = enabled and self._hover(x, y, w, h)
        fill = STATIC["blue"] if active else (mix(self.col("pill"), (255, 255, 255), 0.1) if over else self.col("pill"))
        self.rrect(x, y + 4, w, h, shade(fill, 0.55), 14)
        self.rrect(x, y, w, h, fill, 14, self.col("edge") if not active else (190, 220, 255), 2)
        cx, cy = int(x + 26), int(y + h / 2)
        pygame.draw.circle(self.screen, (255, 255, 255) if enabled else self.col("dim"), (cx, cy), 18)
        pygame.draw.circle(self.screen, color, (cx, cy), 14)
        self.text(key, 15, (255, 255, 255), cx, cy - 10, True, True)
        self.text(title, 15, self.col("text") if enabled else self.col("dim"), x + 52, y + 9, True)
        self.text(sub, 11, self.col("dim"), x + 52, y + 30, True)
        if enabled:
            self.buttons.append((pygame.Rect(int(x), int(y), int(w), int(h)), tag))

    def hit_test(self, pos):
        for rect, tag in reversed(self.buttons):
            if rect.collidepoint(pos):
                return tag
        return None
