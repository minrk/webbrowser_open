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
def unregister():
    # unregister our handler
    # webbrowser has no public API for this
    name = "system-default"
    webbrowser._browsers.pop(name, None)
    if webbrowser._tryorder and name in webbrowser._tryorder:
        webbrowser._tryorder.remove(name)
    webbrowser_open._opener = None


def test_default_browser():
    browser = webbrowser_open.get_default_browser()
    assert browser is not None
    assert Path(shlex.split(browser)[0]).exists()
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
