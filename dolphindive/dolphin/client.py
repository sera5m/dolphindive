from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def open_path(path: Path) -> None:
    if path.is_dir():
        open_in_dolphin(path)
        return
    opener = shutil.which("xdg-open") or shutil.which("kde-open")
    if opener:
        subprocess.Popen([opener, str(path)])
    else:
        raise RuntimeError("no xdg-open / kde-open")


def open_in_dolphin(path: Path, select_file: bool = False) -> bool:
    target = path if path.is_dir() else path.parent
    try:
        from dbus import SessionBus, Interface  # type: ignore
    except Exception:
        return _spawn_dolphin(target, path if select_file or path.is_file() else None)

    bus = SessionBus()
    dbus_iface = Interface(
        bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus"),
        "org.freedesktop.DBus",
    )
    names = [n for n in dbus_iface.ListNames() if n.startswith("org.kde.dolphin")]
    if not names:
        return _spawn_dolphin(target, path if path.is_file() else None)

    for name in sorted(names, reverse=True):
        try:
            obj = bus.get_object(name, "/dolphin/Dolphin_1")
            iface = Interface(obj, "org.kde.dolphin.MainWindow")
            if path.is_file():
                iface.openFiles([str(path)], False)
            else:
                iface.openDirectories([str(target)], False)
            try:
                iface.activateWindow()
            except Exception:
                pass
            return True
        except Exception:
            continue
    return _spawn_dolphin(target, path if path.is_file() else None)


def _spawn_dolphin(directory: Path, select: Path | None) -> bool:
    exe = shutil.which("dolphin")
    if not exe:
        return False
    cmd = [exe]
    if select is not None:
        cmd.extend(["--select", str(select)])
    else:
        cmd.append(str(directory))
    subprocess.Popen(cmd)
    return True
