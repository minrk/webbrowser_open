from __future__ import annotations

import os
import shutil
from pathlib import Path
from subprocess import CalledProcessError, check_output
from webbrowser import BackgroundBrowser


def locate_desktop(name: str) -> str | None:
    """Locate .desktop file by name

    Returns absolute path to .desktop file found on $XDG_DATA search path
    or None if no matching .desktop file is found.
    """
    if not name.endswith(".desktop"):
        # ensure it ends in .desktop
        name += ".desktop"
    data_home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    xdg_data_dirs = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share/:/usr/share/"
    all_data_dirs = [data_home]
    all_data_dirs.extend(xdg_data_dirs.split(os.pathsep))
    for data_dir in all_data_dirs:
        desktop_path = Path(data_dir) / "applications" / name
        if desktop_path.exists():
            return str(desktop_path)
    return None


def get_default_browser() -> str | None:
    """Get the command to launch the default browser

    Returns None if not found
    """
    # only works if we have gtk-launch and can lookup the default browser
    if shutil.which("gtk-launch") is None or shutil.which("gio") is None:
        return None
    if shutil.which("xdg-settings") is None and shutil.which("xdg-mime") is None:
        return None

    # first, lookup the browser
    browser: str | None = None
    if shutil.which("xdg-settings"):
        try:
            browser = check_output(
                ["xdg-settings", "get", "default-web-browser"], text=True
            ).strip()
        except (CalledProcessError, OSError):
            pass
    if browser is None and shutil.which("xdg-mime"):
        try:
            browser = check_output(
                ["xdg-mime", "query", "default", "x-scheme-handler/https"], text=True
            ).strip()
        except (CalledProcessError, OSError):
            pass

    if browser is None:
        return None

    # next, lookup the launcher
    # gtk-launch is best because it searches paths correctly
    if shutil.which("gtk-launch"):
        return browser
    elif shutil.which("gio"):
        # `gio launch` also works, but doesn't search paths, it needs an absolute path
        # only accept this if our search finds it;
        # I'm not sure our search is 100% correct on all systems,
        # but at least it should follow XDG spec
        desktop_path = locate_desktop(browser)
        if desktop_path:
            return desktop_path
    return None


def make_opener() -> BackgroundBrowser | None:
    browser = get_default_browser()
    if browser is None:
        return None
    if shutil.which("gtk-launch"):
        cmd = ["gtk-launch", browser]
    elif shutil.which("gio"):
        cmd = ["gio", "launch", browser]
    return BackgroundBrowser(cmd)
