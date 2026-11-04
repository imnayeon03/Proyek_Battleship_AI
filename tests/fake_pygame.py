"""Pygame tiruan minimal untuk smoke test tanpa jendela. Memvalidasi tipe argumen gambar
agar kesalahan kode (None, string, NaN, float pada titik lingkaran) tertangkap."""
import math
import types

NUM = (int, float)


def _chk(*vals):
    for v in vals:
        if not isinstance(v, NUM) or isinstance(v, bool) or math.isnan(v):
            raise TypeError(f"bukan angka valid: {v!r}")


class Rect:
    def __init__(self, x, y, w, h):
        _chk(x, y, w, h)
        self.x, self.y, self.w, self.h = x, y, w, h

    def collidepoint(self, p):
        return self.x <= p[0] <= self.x + self.w and self.y <= p[1] <= self.y + self.h


class Surface:
    def __init__(self, size=(1, 1), flags=0):
        self.size = size

    def fill(self, color):
        assert len(color) in (3, 4)

    def blit(self, src, dest):
        _chk(dest[0], dest[1])


class Font:
    def __init__(self, size): self.px = size
    def size(self, text): return (int(len(text) * self.px * 0.55), int(self.px * 1.2))

    def render(self, text, aa, color):
        assert isinstance(text, str) and len(color) in (3, 4)
        return Surface()


def _color(c):
    assert len(c) in (3, 4) and all(isinstance(v, int) and 0 <= v <= 255 for v in c), c


def _rect(r):
    if not isinstance(r, Rect):
        assert len(r) == 4
        _chk(*r)


class Event:
    def __init__(self, type, **kw):
        self.type = type
        self.__dict__.update(kw)


class _Screen(Surface):
    def fill(self, color): _color(color)


def make():
    m = types.ModuleType("pygame")
    m.QUIT, m.MOUSEBUTTONDOWN, m.KEYDOWN, m.SRCALPHA = 256, 1025, 768, 65536
    for i, n in enumerate("K_ESCAPE K_RETURN K_h K_a K_t K_m K_i K_r K_d".split()):
        setattr(m, n, 1000 + i)
    m.Rect, m.Surface, m.Event = Rect, Surface, Event
    m.init = lambda: None
    m.quit = lambda: None
    m.display = types.SimpleNamespace(set_mode=lambda size: _Screen(), set_caption=lambda t: None, flip=lambda: None)
    m.time = types.SimpleNamespace(Clock=lambda: types.SimpleNamespace(tick=lambda fps: 16))
    m.font = types.SimpleNamespace(SysFont=lambda name, size, bold=False: Font(size))

    def rect(s, c, r, width=0, border_radius=0): _color(c); _rect(r); _chk(width, border_radius)
    def circle(s, c, ctr, rad, width=0):
        _color(c); _chk(ctr[0], ctr[1], rad, width)
        assert isinstance(ctr[0], int) and isinstance(ctr[1], int), "titik lingkaran harus integer"
    def line(s, c, a, b, width=1): _color(c); _chk(a[0], a[1], b[0], b[1], width)
    def polygon(s, c, pts, width=0):
        _color(c); assert len(pts) >= 3
        for p in pts:
            _chk(p[0], p[1])
            assert isinstance(p[0], int) and isinstance(p[1], int), "titik poligon harus integer"
    def lines(s, c, closed, pts, width=1):
        _color(c); assert len(pts) >= 2
        for p in pts:
            _chk(p[0], p[1])
    m.draw = types.SimpleNamespace(rect=rect, circle=circle, line=line, polygon=polygon, lines=lines)
    m.event = types.SimpleNamespace(get=lambda: [])
    m.mouse = types.SimpleNamespace(get_pos=lambda: (0, 0))
    return m
