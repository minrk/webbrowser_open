from __future__ import annotations

import os
import shlex
import subprocess
import sys
from webbrowser import BaseBrowser

assert sys.platform == "win32"  # for mypy
import winreg


def _registry_lookup(root_key: str, sub_key: str, value_name: str = "") -> str | None:
    """Lookup a registry item

    Returns None if no value could be read
    """
    try:
        with winreg.OpenKey(root_key, sub_key) as key:
            return winreg.QueryValueEx(key, value_name)[0]
    except OSError:
        return None
    return None


def get_default_browser() -> str | None:
    """Get the command to launch the default browser

    Returns None if not found
    """
    browser_id = _registry_lookup(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
        "ProgId",
    )
    if browser_id is None:
        return None
    browser_cmd = _registry_lookup(
        winreg.HKEY_CLASSES_ROOT, browser_id + r"\shell\open\command"
    )
    return browser_cmd


class WindowsDefault(BaseBrowser):
    def _open_default_browser(self, url):
        """Open a URL with the default browser

        launches the web browser no matter what `url` is,
        unlike startfile.

        Raises OSError if registry lookups fail.
        Returns False if URL not opened.
        """
        try:
            import winreg
        except ImportError:
            return False
        # lookup progId for https URLs
        # e.g. 'FirefoxURL-abc123'
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
        ) as key:
            browser_id = winreg.QueryValueEx(key, "ProgId")[0]
        # lookup launch command-line
        # e.g. '"C:\\Program Files\\Mozilla Firefox\\firefox.exe" -osint -url "%1"'
        with winreg.OpenKey(
            winreg.HKEY_CLASSES_ROOT,
            browser_id + r"\shell\open\command",
        ) as key:
            browser_cmd = winreg.QueryValueEx(key, "")[0]
        if "%1" not in browser_cmd:
            # don't know how to build cmd
            # (is append safe?)
            return False
        # this part copied from BackgroundBrowser
        cmdline = [arg.replace("%1", url) for arg in shlex.split(browser_cmd)]
        try:
            p = subprocess.Popen(cmdline)
            return p.poll() is None
        except OSError:
            return False

    def open(self, url, new=0, autoraise=True):
        sys.audit("webbrowser.open", url)

        proto, _sep, _rest = url.partition(":")
        if proto.lower() not in {"http", "https"}:
            # need to lookup browser if it's not a web URL
            try:
                opened = self._open_default_browser(url)
            except OSError:
                # failed to lookup registry items
                opened = False
            if opened:
                return opened

        # fallback: os.startfile; identical to 3.13
        try:
            os.startfile(url)
        except OSError:
            # [Error 22] No application is associated with the specified
            # file for this operation: '<URL>'
            return False
        else:
            return True


def make_opener() -> WindowsDefault | None:
    browser = get_default_browser()
    if browser is None:
        return None
    return WindowsDefault()
