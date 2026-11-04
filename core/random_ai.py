"""core/random_ai.py - AI pembanding (baseline): menembak sel acak yang belum pernah ditembak."""
import random

from core.state import all_cells


class RandomAI:
    name = "Random AI"

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.reset()

    def reset(self):
        self.pool = all_cells()
        self.rng.shuffle(self.pool)

    def choose(self):
        return self.pool.pop()

    def update(self, cell, res):
        pass
