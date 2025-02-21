import shutil
from subprocess import CalledProcessError, check_output
from webbrowser import GenericBrowser


def get_default_browser() -> str | None:
    """Get the command to launch the default browser

    Returns None if not found
    """
    # only works if we have gtk-launch and can lookup the default browser
    if shutil.which("gtk-launch") is None:
        return None
    if shutil.which("xdg-settings") is None and shutil.which("xdg-mime") is None:
        return None
    browser: str | None = None
    if shutil.which("xdg-settings"):
        try:
            browser = check_output(
                ["xdg-settings", "get", "default-web-browser"], text=True
            ).strip()
        except (CalledProcessError, OSError):
            pass
    if browser is None and shutil.which("xdg-mime"):
        try:
            browser = check_output(
                ["xdg-mime", "query", "default", "x-scheme-handler/https"], text=True
            ).strip()
        except (CalledProcessError, OSError):
            pass
    return browser


def make_opener() -> GenericBrowser | None:
    browser = get_default_browser()
    if browser is None:
        return None
    # only works if we have gtk-launch
    # are there other ways to
    if shutil.which("gtk-launch") is None:
        return None
    return GenericBrowser(["gtk-launch", browser])
