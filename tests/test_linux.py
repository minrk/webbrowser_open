import os
import shlex
import subprocess
import sys
from functools import partial
from unittest import mock

import pytest

from webbrowser_open import _linux

url = "file:///tmp/test.html"

pytestmark = pytest.mark.skipif(sys.platform.startswith("win"), reason="not on windows")


def shutil_finds(*found_names):
    def _mock_which(name):
        if name in found_names or "*" in found_names:
            return f"/usr/bin/{name}"
        else:
            return None

    return mock.patch("shutil.which", _mock_which)


def mock_xdg_lookup_browser(cmd, _kind="xdg-settings", *args, **kwargs):
    if _kind == "xdg-settings" and cmd == [
        "xdg-settings",
        "get",
        "default-web-browser",
    ]:
        return "found-default.desktop"
    if _kind == "xdg-mime" and cmd == [
        "xdg-mime",
        "query",
        "default",
        "x-scheme-handler/https",
    ]:
        return "found-mime.desktop"
    print("raising!", _kind, cmd)
    raise subprocess.CalledProcessError(1, cmd)


def xdg_finds(kind):
    return mock.patch(
        "webbrowser_open._linux.check_output",
        partial(mock_xdg_lookup_browser, _kind=kind),
    )


@pytest.fixture
def default_browser():
    desktop_name = "found.desktop"
    with mock.patch(
        "webbrowser_open._linux.get_default_browser", return_value=desktop_name
    ):
        yield desktop_name


@pytest.fixture
def default_browser_exists(default_browser, tmp_path):
    xdg_data = tmp_path / "xdg_data"
    applications = xdg_data / "applications"
    applications.mkdir(parents=True)
    desktop_file = applications / default_browser
    with desktop_file.open("w") as f:
        f.write("touch")
    with mock.patch.dict(
        os.environ, {"XDG_DATA_DIRS": f"{tmp_path / 'nosuch'}:{xdg_data}"}
    ):
        yield desktop_file


@pytest.fixture
def no_default_browser():
    with mock.patch("webbrowser_open._linux.get_default_browser", return_value=None):
        yield


@pytest.mark.parametrize(
    "which_finds, finds, expected",
    [
        ("xdg-settings", "xdg-settings", "found-default.desktop"),
        ("xdg-mime", "xdg-mime", "found-mime.desktop"),
        ("xdg-settings,xdg-mime", "xdg-mime", "found-mime.desktop"),
        ("xdg-settings,xdg-mime", None, None),
        (None, None, None),
    ],
)
def test_get_default_browser(which_finds, finds, expected):
    if which_finds:
        which_find_names = [name.strip() for name in which_finds.split(",")]
    else:
        which_find_names = []
    with shutil_finds(*which_find_names), xdg_finds(finds):
        assert _linux.get_default_browser() == expected


def test_get_default_browser_nothing_found():
    # don't call programs we don't find
    with shutil_finds(), mock.patch("subprocess.check_output") as check:
        assert _linux.get_default_browser() is None
    assert check.call_count == 0


class PopenMock(mock.MagicMock):
    def poll(self):
        return 0

    def wait(self, seconds=None):
        return 0


@pytest.mark.parametrize(
    "which_finds, expected",
    [
        ("gtk-launch", "gtk-launch found.desktop URL"),
        ("gtk4-launch", "gtk4-launch found.desktop URL"),
        ("gio", "gio launch ABSOLUTE_APP URL"),
    ],
)
def test_make_opener(default_browser, default_browser_exists, which_finds, expected):
    if which_finds:
        which_find_names = [name.strip() for name in which_finds.split(",")]
    else:
        which_find_names = []
    with shutil_finds(*which_find_names):
        browser = _linux.make_opener()
    if expected is None:
        assert browser is None
        return
    assert browser is not None

    expected = expected.replace("ABSOLUTE_APP", str(default_browser_exists))
    expected = expected.replace("URL", url)
    expected_cmd = shlex.split(expected)
    with mock.patch("subprocess.Popen", PopenMock()) as popen:
        browser.open(url)
        cmd = popen.call_args[0][0]
    assert cmd == expected_cmd


def test_kde(no_default_browser):
    with (
        mock.patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "KDE"}),
        shutil_finds("kioclient"),
    ):
        browser = _linux.make_opener()
    assert browser.name == "kioclient"

    with mock.patch("subprocess.Popen", PopenMock()) as popen:
        browser.open(url)
        cmd = popen.call_args[0][0]
    assert cmd == ["kioclient", "exec", url, "x-scheme-handler/https"]


def test_xfce(no_default_browser):
    with (
        mock.patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "XFCE"}),
        shutil_finds("exo-open"),
    ):
        browser = _linux.make_opener()
    assert browser is not None
    assert browser.name == "exo-open"

    with mock.patch("subprocess.Popen", PopenMock()) as popen:
        browser.open(url)
        cmd = popen.call_args[0][0]
    assert cmd == ["exo-open", "--launch", "WebBrowser", url]
