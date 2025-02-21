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
    name = webbrowser_open._DefaultBrowserOpener.name
    webbrowser._browsers.pop(name, None)
    if webbrowser._tryorder and name in webbrowser._tryorder:
        webbrowser._tryorder.remove(name)


def test_default_browser():
    browser = webbrowser_open.get_default_browser()
    if _linux:
        assert browser is None
        return
    assert browser is not None
    assert Path(shlex.split(browser)[0]).exists()
    if sys.platform == "win32":
        assert "%1" in browser


def test_register():
    opener = webbrowser_open.register()
    if _linux:
        assert opener is None
        return
    assert opener is not None
    assert webbrowser.get() is opener


def test_register_browser_env():
    with mock.patch.dict(os.environ, {"BROWSER": "bash -c 'echo %s'"}):
        opener = webbrowser_open.register()
    if _linux:
        assert opener is None
        return
    assert opener is not None
    print(webbrowser._browsers)
    print(webbrowser._tryorder)
    assert webbrowser.get() is not opener


@pytest.fixture
def mock_open_with_browser():
    if _linux:
        yield None
    else:
        with mock.patch.object(
            webbrowser_open._backend, "open_with_browser", return_value=True
        ) as method:
            yield method


def test_open(mock_open_with_browser):
    webbrowser_open.open("https://example.org")
    if _linux:
        return
    mock_open_with_browser.assert_called_once_with(
        "https://example.org", webbrowser_open.get_default_browser()
    )


def test_register_open(mock_open_with_browser):
    opener = webbrowser_open.register()
    if _linux:
        assert opener is None
        return
    webbrowser.open("https://example.org")
    mock_open_with_browser.assert_called_once_with(
        "https://example.org", webbrowser_open.get_default_browser()
    )
