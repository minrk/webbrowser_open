from __future__ import annotations

import os
import platform
import typing
import webbrowser

__version__ = "0.1.0.dev"
__all__ = [
    "open",
    "register",
]

if typing.TYPE_CHECKING:

    class _Backend(typing.Protocol):
        @staticmethod
        def get_default_browser() -> str | None: ...
        @staticmethod
        def open_with_browser(url: str, browser: str) -> str | None: ...


_backend: _Backend | None = None
_system = platform.system()
if _system == "Darwin":
    try:
        from . import _mac as _backend  # type: ignore
    except ImportError:
        # e.g. ctypes unavailable
        raise
elif _system == "Windows":
    try:
        from . import _win as _backend  # type: ignore
    except ImportError:
        # e.g. winreg unavailable
        pass
elif _system == "Linux":
    try:
        from . import _linux as _backend  # type: ignore
    except ImportError:
        pass


class _DefaultBrowserOpener(webbrowser.BaseBrowser):
    name = "system-default"

    def __init__(self) -> None:
        if _backend is None:
            raise RuntimeError("No default app found!")
        self._browser = _backend.get_default_browser()

    def open(self, url: str, new: int = 0, autoraise: bool = True) -> bool:
        if self._browser is None or _backend is None:
            return False
        try:
            _backend.open_with_browser(url, self._browser)
        except Exception:
            return False
        else:
            return True

    def open_new(self, url: str) -> bool:
        return self.open(url)

    open_new_tab = open_new


def register(preferred: bool | None = None) -> _DefaultBrowserOpener | None:
    """Install the default-browser opener, if we find one

    Will set up as the preferred browser unless $BROWSER is set
    or preferred=True is given explicitly

    Has no effect if the default browser cannot be found
    """
    if _backend is None:
        # no backend found
        return None
    default_browser = _backend.get_default_browser()
    if default_browser is None:
        # did not find it, do nothing
        return None
    if preferred is None:
        # don't override $BROWSER by default
        preferred = not bool(os.environ.get("BROWSER"))

    opener = _DefaultBrowserOpener()
    webbrowser.register(
        _DefaultBrowserOpener.name,
        None,
        instance=opener,
        preferred=preferred,
    )
    return opener


def open(url: str) -> None:
    """Open a URL with the default browser"""
    if _backend is None:
        webbrowser.open(url)
        return
    browser = _backend.get_default_browser()
    if browser is None:
        # no default found
        webbrowser.open(url)
        return

    _backend.open_with_browser(url, browser)


def get_default_browser() -> str | None:
    """Return the default browser, as detected by the system

    None if none found
    """
    if _backend is None:
        return None
    return _backend.get_default_browser()
