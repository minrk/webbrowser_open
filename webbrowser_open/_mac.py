from __future__ import annotations

import os
import sys
from subprocess import CalledProcessError, check_output
from webbrowser import BaseBrowser


def get_default_browser() -> str | None:
    """Identify the default browser"""
    script = """
        use framework "AppKit"
        use AppleScript version "2.4"
        use scripting additions
        
        property NSWorkspace : a reference to current application's NSWorkspace
        property NSURL : a reference to current application's NSURL
        
        set http_url to NSURL's URLWithString:"https://python.org"
        set browser_url to (NSWorkspace's sharedWorkspace)'s ¬
            URLForApplicationToOpenURL:http_url
        set app_path to browser_url's relativePath as text -- NSURL to absolute path '/Applications/Safari.app'
        return app_path
    """
    try:
        app_path = check_output(["osascript"], input=script, text=True).strip()
    except (OSError, CalledProcessError):
        return None
    if os.path.exists(app_path):
        return app_path
    else:
        return None


class MacOSXOSAScript(BaseBrowser):
    def __init__(self, name: str = "default") -> None:
        super().__init__(name)

    def open(self, url: str, new: int = 0, autoraise: bool = True) -> bool:
        sys.audit("webbrowser.open", url)
        url = url.replace('"', "%22")
        if self.name == "default":
            proto, sep, rest = url.partition(":")
            if proto in {"http", "https"}:
                script = f'open location "{url}"'
            else:
                # if not a web URL, need to lookup default browser to ensure a browser is launched
                # this should always work, but is overkill to lookup http handler before launching http
                script = f'''
                    use framework "AppKit"
                    use AppleScript version "2.4"
                    use scripting additions
                    
                    property NSWorkspace : a reference to current application's NSWorkspace
                    property NSURL : a reference to current application's NSURL
                    
                    set http_url to NSURL's URLWithString:"https://python.org"
                    set browser_url to (NSWorkspace's sharedWorkspace)'s ¬
                        URLForApplicationToOpenURL:http_url
                    set app_path to browser_url's relativePath as text -- NSURL to absolute path '/Applications/Safari.app'

                    tell application app_path
                        activate
                        open location "{url}"
                    end tell
                '''
        else:
            script = f'''
               tell application "{self.name}"
                   activate
                   open location "{url}"
               end
               '''

        osapipe = os.popen("osascript", "w")
        if osapipe is None:
            return False

        osapipe.write(script)
        rc = osapipe.close()
        return not rc


def make_opener() -> MacOSXOSAScript | None:
    browser = get_default_browser()
    if browser is None:
        return None
    return MacOSXOSAScript()
