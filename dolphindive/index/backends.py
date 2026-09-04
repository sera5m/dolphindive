from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

from dolphindive.engine.query import BALOO_TYPES, ParsedQuery


@dataclass
class Candidate:
    path: Path
    is_dir: bool
    mtime: float = 0.0


def search_candidates(query: ParsedQuery, limit: int = 80) -> list[Candidate]:
    hits = _baloo(query, limit)
    if hits:
        return hits
    return _walk_home(query, limit)


def _baloo(query: ParsedQuery, limit: int) -> list[Candidate]:
    exe = shutil.which("baloosearch")
    if not exe:
        return []
    parts: list[str] = []
    if query.kind in BALOO_TYPES:
        parts.append(f"type:{BALOO_TYPES[query.kind]}")
    if query.text:
        parts.append(f"filename:{query.text}")
    if not parts:
        parts.append("*")
    cmd = [exe, "-l", str(limit), " ".join(parts)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return []
    out: list[Candidate] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line.startswith("/"):
            continue
        path = Path(line)
        try:
            is_dir = path.is_dir()
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if not query.matches_path(path):
            continue
        out.append(Candidate(path=path, is_dir=is_dir, mtime=mtime))
    return out


def _walk_home(query: ParsedQuery, limit: int) -> list[Candidate]:
    roots = [Path.home()]
    extra = Path.home() / "Downloads"
    if extra.exists():
        roots.append(extra)
    skip = {".git", ".cache", "node_modules", "__pycache__", ".local"}
    needle = query.text.lower()
    found: list[Candidate] = []
    for root in roots:
        for path in _iter_files(root, skip, max_depth=4):
            if needle and needle not in path.name.lower() and needle not in str(path).lower():
                if not _subseq(needle, path.name.lower()):
                    continue
            if not query.matches_path(path):
                continue
            try:
                st = path.stat()
            except OSError:
                continue
            found.append(Candidate(path=path, is_dir=path.is_dir(), mtime=st.st_mtime))
            if len(found) >= limit * 3:
                return found
    return found


def _iter_files(root: Path, skip: set[str], max_depth: int):
    stack = [(root, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > max_depth:
            continue
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.name.startswith(".") and entry.name not in {".config"}:
                continue
            if entry.name in skip:
                continue
            yield entry
            if entry.is_dir():
                stack.append((entry, depth + 1))


def _subseq(p: str, t: str) -> bool:
    if not p:
        return True
    it = iter(t)
    return all(c in it for c in p)
