"""ui/session.py
Logika sesi Human vs AI (TANPA pygame, sehingga bisa diuji).
Pemain menembak papan AI; AI (BayesAI) membalas menembak papan pemain. Semua tembakan memakai Shot.apply().
Cara bermain: MANUAL (human_fire) atau dibantu AI (hint / auto_step / auto_play).
"""
from typing import List

from core.actions import Shot
from core.bayes_ai import BayesAI
from core.board import Board
from core.explain import Explanation, explain_move
from core.state import label, parse_cell
from ui.textutil import word


class GameSession:
    def __init__(self, human_layout, ai_layout, ai=None, helper=None):
        self.human_layout, self.ai_layout = human_layout, ai_layout
        self.ai = ai or BayesAI()           # lawan: menembak armada pemain
        self.helper = helper or BayesAI()   # pembantu: mengamati tembakan pemain, memberi saran
        self.reset()

    def reset(self):
        self.ai.reset()
        self.helper.reset()
        self.hb, self.eb = Board(self.human_layout), Board(self.ai_layout)   # hb = armada Anda, eb = armada AI
        self.winner = None
        self.awaiting_ai = False
        self.used_ai = False
        self.last_human = self.last_ai = None          # (sel, ShotResult)
        self.log: List[str] = []
        self.message = "Giliran Anda: klik papan radar atau ketik koordinat."

    @property
    def finished(self) -> bool:
        return self.winner is not None

    @property
    def shots(self) -> int:
        return len(self.eb.shots)

    def _say(self, text):
        self.message = text
        self.log.append(text)

    # ------------------------------------------------------------ giliran pemain
    def human_fire(self, cell) -> bool:
        if self.finished or self.awaiting_ai:
            return False
        if cell in self.eb.shots:
            self.message = "Sel itu sudah pernah Anda tembak."
            return False
        res = Shot(cell, "Anda").apply(self.eb)
        self.helper.update(cell, res)
        self.last_human = (cell, res)
        self._say(f"Anda -> {label(cell)}: {word(res)}")
        if self.eb.all_sunk():
            self.winner = "ANDA"
            self._say(self.message + "   |   PEMENANG: ANDA")
        else:
            self.awaiting_ai = True
        return True

    def ai_reply(self) -> bool:
        if not self.awaiting_ai or self.finished:
            return False
        cell = self.ai.choose()
        res = Shot(cell, "AI").apply(self.hb)
        self.ai.update(cell, res)
        self.last_ai = (cell, res)
        self.awaiting_ai = False
        self._say(f"AI -> {label(cell)}: {word(res)}")
        if self.hb.all_sunk():
            self.winner = "AI"
            self._say(self.message + "   |   PEMENANG: AI")
        return True

    def fire(self, raw: str) -> bool:
        """Tembak lewat teks (mis. 'E5'); AI langsung membalas. False jika input ditolak."""
        try:
            cell = parse_cell(raw)
        except ValueError as exc:
            self.message = str(exc)
            return False
        if not self.human_fire(cell):
            return False
        self.ai_reply()
        return True

    # ------------------------------------------------------------ bantuan AI
    def hint(self) -> Explanation:
        self.used_ai = True
        return explain_move(self.helper)

    def auto_step(self) -> bool:
        """AI menembak untuk Anda (satu langkah), lalu lawan membalas jika sesi dijalankan tanpa animasi."""
        if self.finished or self.awaiting_ai:
            return False
        self.used_ai = True
        return self.human_fire(self.helper.choose())

    def auto_play(self, max_steps: int = 200) -> int:
        n = 0
        while not self.finished and n < max_steps:
            if self.awaiting_ai:
                self.ai_reply()
            elif self.auto_step():
                n += 1
            else:
                break
        return n
