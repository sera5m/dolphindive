from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import time

from .fuzzy import fuzzy_score


class RankMode(str, Enum):
    SMART = "smart"
    FUZZY_ONLY = "fuzzy"
    INVERT = "invert"


def next_mode(mode: RankMode) -> RankMode:
    order = [RankMode.SMART, RankMode.FUZZY_ONLY, RankMode.INVERT]
    return order[(order.index(mode) + 1) % len(order)]


@dataclass
class Hit:
    path: str
    name: str
    is_dir: bool
    mtime: float = 0.0
    opens: int = 0
    last_open: float = 0.0
    fuzzy: float = 0.0
    final: float = 0.0


def score_hit(
    hit: Hit,
    query_text: str,
    mode: RankMode,
    now: float | None = None,
) -> Hit | None:
    name_score = fuzzy_score(query_text, hit.name)
    path_score = fuzzy_score(query_text, hit.path)
    if name_score is None and path_score is None:
        return None
    fuzzy = max(name_score or -999, (path_score or -999) * 0.55)
    hit.fuzzy = fuzzy

    now = now or time.time()
    recency = 0.0
    if hit.last_open > 0:
        age_days = max((now - hit.last_open) / 86400.0, 0.0)
        recency = 18.0 / (1.0 + age_days)
    usage = 8.0 * math.log1p(hit.opens)

    if mode is RankMode.FUZZY_ONLY:
        hit.final = fuzzy
    elif mode is RankMode.INVERT:
        hit.final = -fuzzy - usage - recency
    else:
        hit.final = fuzzy + usage + recency
        if hit.is_dir:
            hit.final += 1.5
    return hit
