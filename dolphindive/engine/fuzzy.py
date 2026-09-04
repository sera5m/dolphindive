from __future__ import annotations


def fuzzy_score(pattern: str, text: str) -> float | None:
    """Sublime-ish sequential fuzzy score. None = no match.

    Higher is better. Empty pattern matches everything at 0.
    """
    if not pattern:
        return 0.0

    p = pattern.lower()
    t = text.lower()
    if p not in t and not _is_subsequence(p, t):
        return None

    score = 0.0
    ti = 0
    consecutive = 0
    first = True
    for pc in p:
        found = -1
        for j in range(ti, len(t)):
            if t[j] == pc:
                found = j
                break
        if found < 0:
            return None

        score += 16
        if found == ti and not first:
            consecutive += 1
            score += 15 * consecutive
        else:
            consecutive = 0

        if found == 0:
            score += 24
        elif text[found].isupper() and found > 0 and text[found - 1].islower():
            score += 18
        elif found > 0 and text[found - 1] in "/\\._- ":
            score += 20

        if not first:
            gap = found - ti
            if gap > 1:
                score -= min(gap - 1, 8)

        ti = found + 1
        first = False

    leftover = len(t) - len(p)
    score -= leftover * 0.15
    if t.startswith(p):
        score += 30
    return score


def _is_subsequence(p: str, t: str) -> bool:
    it = iter(t)
    return all(c in it for c in p)
