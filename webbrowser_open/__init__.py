from __future__ import annotations

import os
import platform
import typing
import webbrowser

__version__ = "0.3.0"
__all__ = [
    "get",
    "get_default_browser",
    "open",
    "register",
]

if typing.TYPE_CHECKING:

    class _Backend(typing.Protocol):
        @staticmethod
        def get_default_browser() -> str | None: ...
        @staticmethod
        def make_opener() -> webbrowser.BaseBrowser | None: ...


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

_opener: webbrowser.BaseBrowser | None = None
_name: str = "webbrowser_open"


def _make_opener() -> webbrowser.BaseBrowser | None:
    """get the opener singleton"""
    global _opener
    if _opener is None and _backend is not None:
        _opener = _backend.make_opener()
    return _opener


def register(
    name: str = _name, *, preferred: bool | None = None
) -> webbrowser.BaseBrowser | None:
    """Install the default-browser opener, if we find one

    Will set up as the preferred browser unless $BROWSER is set
    or preferred=True is given explicitly

    Has no effect if the default browser cannot be found
    """
    if _backend is None:
        # no backend found
        return None

    opener = _make_opener()
    if opener is None:
        return None

    if preferred is None:
        # don't override $BROWSER by default
        preferred = not bool(os.environ.get("BROWSER"))
    webbrowser.register(
        name,
        None,
        instance=opener,
        preferred=preferred,
    )
    return opener


def open(url: str) -> None:
    """Open a URL with the default browser"""
    if _backend is None or os.environ.get("BROWSER"):
        webbrowser.open(url)
        return

    opener = _make_opener()
    if opener:
        opener.open(url)
    else:
        # no default found
        webbrowser.open(url)


def get(using: str | None = None) -> webbrowser.BaseBrowser:
    """Get an opener

    Same as `webbrowser.open`

    If a name is specified or $BROWSER is defined,
    this is a passthrough to `webbrowser.get`.

    If neither is specified, this package's default browser is returned if found,
    falling back on `webbrowser.get()`.
    """
    if _backend is None or (using and using != _name) or os.environ.get("BROWSER"):
        return webbrowser.get(using)

    opener = _make_opener()

    if opener:
        return opener
    else:
        # fallback on default
        return webbrowser.get()


def get_default_browser() -> str | None:
    """Return the default browser, as detected by the system

    None if not found
    """
    if _backend is None:
        return None
    return _backend.get_default_browser()
