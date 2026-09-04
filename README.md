# DolphinDive

Listary-shaped file search for **KDE Dolphin on Plasma 6 / EndeavourOS**.

This is not a `dolphin-plugins` VCS `.so`. Listary is a pile of features; we split them the same way:

| package | job |
|---|---|
| `dolphindive.engine` | query parse, Sublime-ish fuzzy, rank modes |
| `dolphindive.index` | Baloo first, home walk fallback |
| `dolphindive.usage` | SQLite "I open this a lot" |
| `dolphindive.dolphin` | D-Bus into a running Dolphin |
| `dolphindive.app` | CLI + Qt overlay |

File-dialog Quick Switch is **not** in 0.1. That lives in KIO `KFileWidget`, not Dolphin, and Wayland will not let us inject into other apps cleanly.

## QA on EndeavourOS Titan

```bash
sudo pacman -S python python-pyqt6 python-dbus baloo
git clone https://github.com/sera5m/dolphindive.git
cd dolphindive
python -m pip install -e '.[dev]' --user
dive selftest
python -m pytest -q
dive search report doc:
dive overlay
```

Bind **Alt+F** (or whatever):

1. Copy `packaging/dolphindive.desktop` to `~/.local/share/applications/`
2. `update-desktop-database ~/.local/share/applications`
3. System Settings → Shortcuts → add custom command `dive overlay` → Alt+F

If Alt+F is eaten by a menu mnemonic, pick Alt+Space or double-check KWin.

## Query syntax

```
budget                 fuzzy name
budget doc:            documents only
shader *.glsl          extension
invoice ext:pdf;odt
photos/ vacation       path hint (folder token ending in /)
```

Chips in the overlay inject the same `kind:` filter.

## Rank

`Ctrl+R` cycles:

1. **smart** — fuzzy + log(opens) + recency
2. **fuzzy only** — ignore habit
3. **invert** — dump the usual suspects to the bottom

Usage is stored in `~/.local/share/dolphindive/usage.sqlite`.

## Keys in the overlay

| key | action |
|---|---|
| Enter | open file / jump folder in Dolphin |
| Ctrl+Enter | always reveal in Dolphin |
| Ctrl+R | cycle rank mode |
| Esc | close |

## What 0.1 will feel like

- Fast enough to QA the ranking idea
- Depends on Baloo being indexed (`balooctl status`)
- Fallback walk is shallow (home, depth 4) so unindexed disks will look empty
- No pinyin / CJK tokenizer yet
- No content search
- No Open/Save hijack

Break it. File issues. That is the point of this drop.
