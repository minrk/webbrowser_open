from __future__ import annotations

import os
import shlex
import subprocess
import sys
from webbrowser import BaseBrowser

assert sys.platform == "win32"  # for mypy


def get_default_browser() -> str | None:
    """Get the command to launch the default browser

    Returns None if not found
    """
    import winreg

    browser_id = WindowsDefault._registry_lookup(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
        "ProgId",
    )
    if browser_id is None:
        return None
    browser_cmd = WindowsDefault._registry_lookup(
        winreg.HKEY_CLASSES_ROOT, browser_id + r"\shell\open\command"
    )
    return browser_cmd


class WindowsDefault(BaseBrowser):
    @staticmethod
    def _registry_lookup(
        root_key: str, sub_key: str, value_name: str = ""
    ) -> str | None:
        """Lookup a registry item

        Returns None if no value could be read
        """
        import winreg

        try:
            with winreg.OpenKey(root_key, sub_key) as key:
                return winreg.QueryValueEx(key, value_name)[0]
        except OSError:
            return None
        return None

    def _open_default_browser(self, url):
        try:
            import winreg
        except ImportError:
            return False
        browser_id = self._registry_lookup(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
            "ProgId",
        )
        if browser_id is None:
            return False
        browser_cmd = self._registry_lookup(
            winreg.HKEY_CLASSES_ROOT, browser_id + r"\shell\open\command"
        )
        if browser_cmd is None or "%1" not in browser_cmd:
            return False
        # this part copied from BackgroundBrowser
        cmdline = [arg.replace("%1", url) for arg in shlex.split(browser_cmd)]
        p = subprocess.Popen(cmdline)
        return p.poll() is None

    def open(self, url, new=0, autoraise=True):
        sys.audit("webbrowser.open", url)

        opened = False
        try:
            opened = self._open_winreg(url)
        except OSError:
            # failed to lookup registry items
            pass
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
