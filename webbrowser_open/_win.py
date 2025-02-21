from __future__ import annotations

import shlex
import sys
from webbrowser import GenericBrowser

assert sys.platform == "win32"  # for mypy

from winreg import (  # noqa:E402
    HKEY_CLASSES_ROOT,
    HKEY_CURRENT_USER,
    OpenKey,
    QueryValueEx,
)


def _registry_lookup(root_key: str, sub_key: str, value_name: str = "") -> str | None:
    """Lookup a registry item

    Returns None if no value could be read
    """
    try:
        with OpenKey(root_key, sub_key) as key:
            return QueryValueEx(key, value_name)[0]
    except OSError:
        return None
    return None


def get_default_browser() -> str | None:
    """Get the command to launch the default browser

    Returns None if not found
    """
    browser_id = _registry_lookup(
        HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice",
        "ProgId",
    )
    if browser_id is None:
        return None
    browser_cmd = _registry_lookup(
        HKEY_CLASSES_ROOT, browser_id + r"\shell\open\command"
    )
    return browser_cmd


def make_opener() -> GenericBrowser | None:
    browser = get_default_browser()
    if browser is None:
        return None
    # Windows uses %1, webbrowser uses %s
    browser = browser.replace("%1", "%s")
    return GenericBrowser(shlex.split(browser))
