"""core/campaign.py - Campaign Levels and AI progression for Island Map.
Features 10 progressive levels from Rookie Sailor to Pirate King,
with custom AI difficulties, star goals, and persistent progress tracking.
"""
import json
import os
import random
from typing import Dict, List, Tuple

import numpy as np

from core.bayes_ai import BayesAI
from core.random_ai import RandomAI
from core.state import N, all_cells


# ================================================================== CAMPAIGN AI OPPONENTS
class RookieAI(RandomAI):
    """Level 1: Pure random shots, perfect for beginners."""
    name = "Rookie Sailor"


class IslandGunnerAI:
    """Level 2-3: Mostly random, but when a hit occurs, explores neighbor cells."""
    name = "Island Gunner"

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.reset()

    def reset(self):
        self.shots = set()
        self.target_queue = []

    def choose(self) -> Tuple[int, int]:
        while self.target_queue:
            c = self.target_queue.pop(0)
            if c not in self.shots:
                return c
        candidates = [c for c in all_cells() if c not in self.shots]
        return self.rng.choice(candidates)

    def update(self, cell, res):
        self.shots.add(cell)
        if res.result in ("hit", "sunk"):
            r, c = cell
            nbrs = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
            for nr, nc in nbrs:
                if 0 <= nr < N and 0 <= nc < N and (nr, nc) not in self.shots:
                    if (nr, nc) not in self.target_queue:
                        self.target_queue.append((nr, nc))


class SmartBayesAI(BayesAI):
    """Level 4+: Bayesian AI with configurable accuracy and tactical parity hunting."""
    def __init__(self, rng=None, accuracy=1.0, parity=False):
        super().__init__(rng=rng)
        self.accuracy = accuracy
        self.use_parity = parity

    def choose(self):
        # With probability (1 - accuracy), take a casual random unexplored shot
        if self.accuracy < 0.99 and self.rng.random() > self.accuracy:
            unexplored = [(r, c) for r in range(N) for c in range(N)
                          if not (self.miss[r, c] or self.hit[r, c])]
            if unexplored:
                return self.rng.choice(unexplored)

        # Standard Bayesian distribution
        prob = self.probability()
        explored = self.miss | self.hit
        prob[explored] = -1.0

        if self.use_parity and self.mode == "hunt":
            # Parity checkerboard weighting: ships of size >= 2 must cross odd/even parity
            min_ship = min(self.remaining) if self.remaining else 2
            for r in range(N):
                for c in range(N):
                    if (r + c) % min_ship != 0 and not explored[r, c]:
                        prob[r, c] *= 0.25

        max_val = prob.max()
        if max_val <= 0:
            unexplored = [(r, c) for r in range(N) for c in range(N) if not explored[r, c]]
            return self.rng.choice(unexplored)

        best_cells = [(r, c) for r in range(N) for c in range(N) if prob[r, c] == max_val]
        return self.rng.choice(best_cells)


# ================================================================== 10 CAMPAIGN LEVELS
LEVELS = [
    {
        "id": 1,
        "name": "Calm Cove",
        "opponent": "Rookie Sailor",
        "avatar": "sailor",
        "stars_req": (42, 60),      # <= 42 shots = 3 stars, <= 60 = 2 stars, else 1 star
        "ai_factory": lambda rng: RookieAI(rng),
        "dialogue": "Ahoy! Let's see if you know how to command a ship!",
    },
    {
        "id": 2,
        "name": "Coral Reef",
        "opponent": "Reef Gunner",
        "avatar": "gunner",
        "stars_req": (42, 58),
        "ai_factory": lambda rng: IslandGunnerAI(rng),
        "dialogue": "Careful around the coral! I won't go easy on you.",
    },
    {
        "id": 3,
        "name": "Smuggler's Bay",
        "opponent": "First Mate",
        "avatar": "mate",
        "stars_req": (40, 56),
        "ai_factory": lambda rng: SmartBayesAI(rng, accuracy=0.45),
        "dialogue": "My cannons are primed and loaded, Captain!",
    },
    {
        "id": 4,
        "name": "Treasure Coast",
        "opponent": "Reef Navigator",
        "avatar": "navigator",
        "stars_req": (38, 54),
        "ai_factory": lambda rng: SmartBayesAI(rng, accuracy=0.65),
        "dialogue": "I can read the winds and the radar like a book.",
    },
    {
        "id": 5,
        "name": "Lighthouse Isle",
        "opponent": "Lighthouse Keeper",
        "avatar": "keeper",
        "stars_req": (38, 52),
        "ai_factory": lambda rng: SmartBayesAI(rng, accuracy=0.80),
        "dialogue": "The lighthouse beacon shines right through your fleet!",
    },
    {
        "id": 6,
        "name": "Octopus Atoll",
        "opponent": "Captain Octo",
        "avatar": "octopus",
        "stars_req": (36, 50),
        "ai_factory": lambda rng: SmartBayesAI(rng, accuracy=0.88),
        "dialogue": "Eight tentacles, eight cannons ready to fire!",
    },
    {
        "id": 7,
        "name": "Skull Shallows",
        "opponent": "Corsair Admiral",
        "avatar": "corsair",
        "stars_req": (36, 48),
        "ai_factory": lambda rng: SmartBayesAI(rng, accuracy=0.92, parity=True),
        "dialogue": "No merchant vessel has ever escaped these waters.",
    },
    {
        "id": 8,
        "name": "Tempest Cape",
        "opponent": "Storm Commander",
        "avatar": "commander",
        "stars_req": (34, 46),
        "ai_factory": lambda rng: SmartBayesAI(rng, accuracy=0.96, parity=True),
        "dialogue": "Lightning and thunder will guide my shells!",
    },
    {
        "id": 9,
        "name": "Kraken Trench",
        "opponent": "Deep Sea Hunter",
        "avatar": "hunter",
        "stars_req": (34, 45),
        "ai_factory": lambda rng: SmartBayesAI(rng, accuracy=1.00, parity=True),
        "dialogue": "You are fighting the deepest currents of the ocean now.",
    },
    {
        "id": 10,
        "name": "King's Harbor",
        "opponent": "Pirate King",
        "avatar": "king",
        "stars_req": (32, 44),
        "ai_factory": lambda rng: SmartBayesAI(rng, accuracy=1.00, parity=True),
        "dialogue": "I rule the Seven Seas! Prove your fleet is worthy of glory!",
    },
]


# ================================================================== PROGRESS STORAGE
class CampaignProgress:
    """Tracks unlocked levels and star ratings, persisting to JSON."""
    def __init__(self, filepath=None):
        if filepath is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            filepath = os.path.join(base_dir, "data", "campaign_progress.json")
        self.filepath = filepath
        self.unlocked_level = 1
        self.stars: Dict[int, int] = {}
        self.load()

    def load(self):
        try:
            if os.path.exists(self.filepath):
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.unlocked_level = max(1, min(len(LEVELS), int(data.get("unlocked_level", 1))))
                    self.stars = {int(k): int(v) for k, v in data.get("stars", {}).items()}
        except Exception as exc:
            print(f"[CampaignProgress] Note loading progress: {exc}")
            self.unlocked_level = 1
            self.stars = {}

    def save(self):
        try:
            d = os.path.dirname(self.filepath)
            if d:
                os.makedirs(d, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "unlocked_level": self.unlocked_level,
                    "stars": self.stars
                }, f, indent=2)
        except Exception as exc:
            print(f"[CampaignProgress] Note saving progress: {exc}")

    def is_unlocked(self, level_id: int) -> bool:
        return level_id <= self.unlocked_level

    def get_stars(self, level_id: int) -> int:
        return self.stars.get(level_id, 0)

    def total_stars(self) -> int:
        return sum(self.stars.values())

    def record_victory(self, level_id: int, shots: int) -> int:
        """Calculates stars, unlocks next level, and persists."""
        lvl = next((L for L in LEVELS if L["id"] == level_id), None)
        if not lvl:
            return 1
        s3, s2 = lvl["stars_req"]
        if shots <= s3:
            earned = 3
        elif shots <= s2:
            earned = 2
        else:
            earned = 1

        prev = self.stars.get(level_id, 0)
        self.stars[level_id] = max(prev, earned)
        if level_id >= self.unlocked_level and self.unlocked_level < len(LEVELS):
            self.unlocked_level = level_id + 1
        self.save()
        return earned
