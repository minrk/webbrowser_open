from __future__ import annotations

import shlex
import sys
from subprocess import Popen

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


def open_with_browser(url: str, browser: str) -> None:
    """Launch a URL with the given browser

    'browser' should be the launch command for the browser app.
    it should have '%1' somewhere for input arguments.
    """
    browser_cmd = shlex.split(browser)
    inserted = False
    for i, field in enumerate(browser_cmd):
        if "%1" in field:
            browser_cmd[i] = field.replace("%1", url)
            inserted = True
    if not inserted:
        # no %1, append arg
        # is this right?
        browser_cmd.append(url)
    p = Popen(browser_cmd)
    status = p.poll()
    if status is not None:
        raise RuntimeError(f"{browser_cmd} exited with [status={status}]")
