from __future__ import annotations

from dolphindive.engine.query import parse_query
from dolphindive.engine.rank import Hit, RankMode, score_hit
from dolphindive.index.backends import search_candidates
from dolphindive.usage.store import UsageStore


def search(raw: str, mode: RankMode = RankMode.SMART, limit: int = 40) -> list[Hit]:
    query = parse_query(raw)
    store = UsageStore()
    hits: list[Hit] = []
    for cand in search_candidates(query, limit=max(limit * 2, 80)):
        usage = store.get(str(cand.path))
        hit = Hit(
            path=str(cand.path),
            name=cand.path.name or str(cand.path),
            is_dir=cand.is_dir,
            mtime=cand.mtime,
            opens=usage.opens,
            last_open=usage.last_open,
        )
        scored = score_hit(hit, query.text, mode)
        if scored is not None:
            hits.append(scored)
    hits.sort(key=lambda h: h.final, reverse=True)
    return hits[:limit]
