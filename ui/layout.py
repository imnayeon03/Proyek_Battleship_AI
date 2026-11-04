"""ui/layout.py - tata letak layar (tanpa pygame, sehingga bisa diuji): posisi papan dan konversi klik -> sel."""
from core.state import N

W, H = 1360, 740
CELL = 40
HORIZON = 410                      # garis cakrawala latar laut


class Layout:
    def __init__(self):
        self.cell = CELL
        self.origin = {"human": (88, 190), "enemy": (W - 88 - N * CELL, 190)}
        self.panel = (508, 150, 344, 500)             # kartu tengah (x, y, w, h)
        self.shift = {"human": (0, 0), "enemy": (0, 0)}   # guncangan layar saat terkena tembakan

    def board_rect(self, which):
        x, y = self.origin[which]
        sx, sy = self.shift[which]
        return x + sx, y + sy, N * self.cell, N * self.cell

    def cell_rect(self, which, cell):
        x, y, _, _ = self.board_rect(which)
        r, c = cell
        return x + c * self.cell, y + r * self.cell, self.cell, self.cell

    def cell_center(self, which, cell):
        x, y, w, h = self.cell_rect(which, cell)
        return x + w / 2, y + h / 2

    def cell_at(self, which, pos):
        x, y, w, h = self.board_rect(which)
        if not (x <= pos[0] < x + w and y <= pos[1] < y + h):
            return None
        return (int((pos[1] - y) // self.cell), int((pos[0] - x) // self.cell))
