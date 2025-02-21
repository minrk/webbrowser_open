import os
import platform
import shlex
import sys
import webbrowser
from pathlib import Path
from unittest import mock

import pytest

import webbrowser_open

_linux = platform.system() == "Linux"


@pytest.fixture(autouse=True)
def reset():
    webbrowser_open._opener = None
    # reset the state of the webbrowser module
    # webbrowser has no public API for this
    # but it's stdlib, so hopefully stable enough for testing purposes
    webbrowser._browsers.clear()
    webbrowser._tryorder = None


def test_default_browser():
    browser = webbrowser_open.get_default_browser()
    assert browser is not None
    if _linux:
        from webbrowser_open._linux import locate_desktop

        browser_path = locate_desktop(browser)
        assert browser_path is not None
    else:
        browser_path = shlex.split(browser)[0]
    assert Path(browser_path).exists()
    if sys.platform == "win32":
        assert "%1" in browser


def test_register():
    opener = webbrowser_open.register()
    assert opener is not None
    assert webbrowser.get() is opener


def test_register_browser_env():
    with mock.patch.dict(os.environ, {"BROWSER": "bash -c 'echo %s'"}):
        opener = webbrowser_open.register()
    assert opener is not None
    assert webbrowser.get() is not opener


@pytest.fixture
def mock_opener():
    if webbrowser_open._backend is None:
        yield None

    opener = webbrowser_open._backend.make_opener()
    with (
        mock.patch("webbrowser_open._opener", opener),
        mock.patch.object(opener, "open", return_value=True) as open_method,
    ):
        assert webbrowser_open._opener is opener
        yield open_method


def test_open(mock_opener):
    webbrowser_open.open("https://example.org")
    mock_opener.assert_called_once_with("https://example.org")


def test_register_open(mock_opener):
    webbrowser_open.register()
    webbrowser.open("https://example.org")
    mock_opener.assert_called_once_with("https://example.org", 0, True)
