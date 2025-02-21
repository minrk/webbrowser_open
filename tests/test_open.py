import os
import shlex
import sys
import webbrowser
from pathlib import Path
from unittest import mock

import webbrowser_open


def test_default_browser():
    browser = webbrowser_open.get_default_browser()
    assert browser is not None
    assert Path(browser).exists()
    assert browser is not None
    assert os.path.exists(shlex.split(browser)[0])
    if sys.platform == "win32":
        assert "%1" in browser


def test_register():
    opener = webbrowser_open.register()
    assert opener is not None
    assert webbrowser.get() is opener


def test_register_browser_env():
    with mock.patch.dict(os.environ, {"BROWSER": "temporary"}):
        opener = webbrowser_open.register()
    assert opener is not None
    assert webbrowser.get() is not opener


def test_open():
    webbrowser_open.open("https://example.org")


def test_register_open():
    opener = webbrowser_open.register()
    assert opener is not None
    with mock.patch.object(
        webbrowser_open._backend, "open_with_browser", return_value=True
    ) as method:
        webbrowser.open("https://example.org")
    method.assert_called_once_with(
        "https://example.org", webbrowser_open.get_default_browser()
    )
