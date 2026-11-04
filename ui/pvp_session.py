"""ui/pvp_session.py - Player vs Player game session (no AI)."""
from typing import List

from core.actions import Shot
from core.board import Board
from core.state import label, FLEET, MISS, HIT
from ui.textutil import word


class PvPSession:
    """Two-player session: Player 1 and Player 2 take turns on the same screen."""

    def __init__(self, p1_layout, p2_layout):
        self.p1_layout = p1_layout
        self.p2_layout = p2_layout
        self.reset()

    def reset(self):
        self.b1 = Board(self.p1_layout)   # Player 1's fleet (Player 2 fires here)
        self.b2 = Board(self.p2_layout)   # Player 2's fleet (Player 1 fires here)
        self.current_player = 1            # Whose turn: 1 or 2
        self.winner = None                 # None | 1 | 2
        self.last_shot = None              # (cell, ShotResult)
        self.log: List[str] = []
        self.message = "Player 1's turn: click on Enemy Radar to fire."
        self.shots_p1 = 0
        self.shots_p2 = 0

    @property
    def finished(self) -> bool:
        return self.winner is not None

    @property
    def active_board(self):
        """Board being shot at by current player."""
        return self.b2 if self.current_player == 1 else self.b1

    @property
    def own_board(self):
        """Current player's own fleet board."""
        return self.b1 if self.current_player == 1 else self.b2

    def _say(self, text):
        self.message = text
        self.log.append(text)

    def fire(self, cell) -> bool:
        """Current player fires at cell. Returns True if shot was valid."""
        if self.finished:
            return False
        target_board = self.active_board
        if cell in target_board.shots:
            self.message = "That cell was already fired upon."
            return False

        shooter_name = f"Player {self.current_player}"
        res = Shot(cell, shooter_name).apply(target_board)
        self.last_shot = (cell, res)

        if self.current_player == 1:
            self.shots_p1 += 1
        else:
            self.shots_p2 += 1

        self._say(f"{shooter_name} -> {label(cell)}: {word(res)}")

        if target_board.all_sunk():
            self.winner = self.current_player
            self._say(f"WINNER: Player {self.current_player}!")
            return True

        # Switch turns after the shot
        self.current_player = 2 if self.current_player == 1 else 1
        self.message = f"Player {self.current_player}'s turn: click on Enemy Radar to fire."
        return True
