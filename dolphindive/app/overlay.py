from __future__ import annotations

from pathlib import Path
import sys

from dolphindive.dolphin.client import open_in_dolphin, open_path
from dolphindive.engine.rank import RankMode, next_mode
from dolphindive.pipeline import search
from dolphindive.usage.store import UsageStore

CHIPS = ["all", "folder", "file", "doc", "pic", "video", "audio", "code", "archive"]


def run_overlay() -> int:
    try:
        from PyQt6.QtCore import Qt, QTimer
        from PyQt6.QtGui import QFont, QKeySequence, QShortcut
        from PyQt6.QtWidgets import (
            QApplication,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QPushButton,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:
        print("PyQt6 missing. On EndeavourOS: sudo pacman -S python-pyqt6", file=sys.stderr)
        return 2

    app = QApplication.instance() or QApplication(sys.argv)
    win = DiveWindow()
    win.show()
    win.raise_()
    win.activateWindow()
    return app.exec()


class DiveWindow(QWidget):  # type: ignore[misc]
    def __init__(self) -> None:
        from PyQt6.QtCore import Qt, QTimer
        from PyQt6.QtGui import QFont, QKeySequence, QShortcut
        from PyQt6.QtWidgets import (
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QPushButton,
            QVBoxLayout,
        )

        super().__init__()
        self.setWindowTitle("DolphinDive")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.resize(720, 460)
        self.mode = RankMode.SMART
        self.chip = "all"
        self.store = UsageStore()
        self._hits = []

        root = QVBoxLayout(self)
        self.input = QLineEdit()
        self.input.setPlaceholderText("search…  try: report doc:   or   *.pdf   or   projects/")
        self.input.setFont(QFont("Noto Sans", 14))
        root.addWidget(self.input)

        chips = QHBoxLayout()
        self.chip_buttons: dict[str, QPushButton] = {}
        for name in CHIPS:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setChecked(name == "all")
            btn.clicked.connect(lambda _=False, n=name: self.set_chip(n))
            self.chip_buttons[name] = btn
            chips.addWidget(btn)
        root.addLayout(chips)

        meta = QHBoxLayout()
        self.mode_label = QLabel()
        self.hint = QLabel("Enter open · Ctrl+Enter folder in Dolphin · Ctrl+R cycle rank · Esc close")
        meta.addWidget(self.mode_label)
        meta.addStretch()
        meta.addWidget(self.hint)
        root.addLayout(meta)

        self.list = QListWidget()
        root.addWidget(self.list, 1)

        self._refresh_mode()
        self.input.textChanged.connect(self.schedule_search)
        self.list.itemActivated.connect(lambda _: self.open_selected(False))

        QShortcut(QKeySequence("Escape"), self, activated=self.close)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.cycle_mode)
        QShortcut(QKeySequence("Return"), self, activated=lambda: self.open_selected(False))
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=lambda: self.open_selected(True))

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.run_search)
        self.input.setFocus()

    def set_chip(self, name: str) -> None:
        self.chip = name
        for n, btn in self.chip_buttons.items():
            btn.setChecked(n == name)
        self.schedule_search()

    def cycle_mode(self) -> None:
        self.mode = next_mode(self.mode)
        self._refresh_mode()
        self.run_search()

    def _refresh_mode(self) -> None:
        labels = {
            RankMode.SMART: "rank: smart (usage + fuzzy)",
            RankMode.FUZZY_ONLY: "rank: fuzzy only",
            RankMode.INVERT: "rank: inverted",
        }
        self.mode_label.setText(labels[self.mode])

    def schedule_search(self) -> None:
        self._timer.start(90)

    def _query_text(self) -> str:
        raw = self.input.text().strip()
        if self.chip != "all" and f"{self.chip}:" not in raw.lower():
            raw = f"{raw} {self.chip}:".strip()
        return raw

    def run_search(self) -> None:
        raw = self._query_text()
        self.list.clear()
        if not raw or raw.endswith(":"):
            self._hits = []
            return
        self._hits = search(raw, mode=self.mode, limit=40)
        from PyQt6.QtWidgets import QListWidgetItem

        for hit in self._hits:
            mark = "▸" if hit.is_dir else " "
            item = QListWidgetItem(f"{mark} {hit.name}    {hit.path}")
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def open_selected(self, folder_in_dolphin: bool) -> None:
        row = self.list.currentRow()
        if row < 0 or row >= len(self._hits):
            return
        hit = self._hits[row]
        path = Path(hit.path)
        self.store.record_open(str(path))
        if folder_in_dolphin or path.is_dir():
            open_in_dolphin(path, select_file=path.is_file())
        else:
            open_path(path)
        self.close()
