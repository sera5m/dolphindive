from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

FILTER_ALIASES = {
    "all": "all",
    "folder": "folder",
    "folders": "folder",
    "dir": "folder",
    "file": "file",
    "files": "file",
    "doc": "doc",
    "docs": "doc",
    "document": "doc",
    "pic": "pic",
    "pics": "pic",
    "image": "pic",
    "images": "pic",
    "photo": "pic",
    "video": "video",
    "videos": "video",
    "audio": "audio",
    "music": "audio",
    "code": "code",
    "src": "code",
    "archive": "archive",
    "zip": "archive",
}

TYPE_EXTENSIONS = {
    "doc": {
        ".pdf", ".odt", ".ods", ".odp", ".doc", ".docx", ".xls", ".xlsx",
        ".ppt", ".pptx", ".rtf", ".txt", ".md", ".epub", ".csv",
    },
    "pic": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tiff", ".heic"},
    "video": {".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v"},
    "audio": {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".opus", ".aac"},
    "code": {
        ".py", ".rs", ".go", ".c", ".h", ".cpp", ".hpp", ".js", ".ts",
        ".qml", ".java", ".kt", ".cs", ".rb", ".php", ".sh", ".cmake",
        ".json", ".toml", ".yaml", ".yml", ".xml", ".html", ".css",
    },
    "archive": {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar", ".iso"},
}

BALOO_TYPES = {
    "folder": "Folder",
    "doc": "Document",
    "pic": "Image",
    "video": "Video",
    "audio": "Audio",
    "archive": "Archive",
}


@dataclass
class ParsedQuery:
    text: str
    kind: str = "all"
    extensions: set[str] = field(default_factory=set)
    path_hint: str | None = None

    def matches_path(self, path: Path) -> bool:
        if self.kind == "folder" and not path.is_dir():
            return False
        if self.kind == "file" and not path.is_file():
            return False
        if self.kind in TYPE_EXTENSIONS and path.is_file():
            if path.suffix.lower() not in TYPE_EXTENSIONS[self.kind]:
                return False
        if self.extensions and path.is_file():
            if path.suffix.lower() not in self.extensions:
                return False
        if self.path_hint:
            hay = str(path).lower()
            if self.path_hint.lower() not in hay:
                return False
        return True


def parse_query(raw: str) -> ParsedQuery:
    tokens = raw.strip().split()
    kind = "all"
    extensions: set[str] = set()
    path_hint = None
    kept: list[str] = []

    for tok in tokens:
        lower = tok.lower()
        if lower.endswith(":") and lower[:-1] in FILTER_ALIASES:
            kind = FILTER_ALIASES[lower[:-1]]
            continue
        if ":" in tok and not tok.startswith("."):
            key, _, value = tok.partition(":")
            key = key.lower()
            if key in FILTER_ALIASES:
                kind = FILTER_ALIASES[key]
                if value:
                    kept.append(value)
                continue
            if key in {"ext", "type"}:
                for part in value.split(";"):
                    part = part.strip().lower()
                    if not part:
                        continue
                    if not part.startswith("."):
                        part = "." + part
                    extensions.add(part)
                continue
        if tok.startswith("*.") and len(tok) > 2:
            extensions.add("." + tok[2:].lower())
            continue
        if tok.endswith("/") and len(tok) > 1:
            path_hint = tok[:-1]
            continue
        if tok.endswith("\\") and len(tok) > 1:
            path_hint = tok[:-1]
            continue
        kept.append(tok)

    return ParsedQuery(text=" ".join(kept), kind=kind, extensions=extensions, path_hint=path_hint)
