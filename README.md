# webbrowser_open

prototyping opening things with the default webbrowser

Most platforms have at least a semi-standard way to open URLs and discover the default browser.

`webbrowser.open` uses generic not-browser-specific APIs (e.g. `open`, `xdg-open`, `os.startfile`), which works fine with `http[s]` URLs.
However, all of these systems associate `file://` URLs with the default application for the file type, _not_ a webbrowser, which `webbrowser.open` is meant to launch.
The result is often `webbrowser.open` launching a file editor instead of a browser.

`webbrowser.open` does not work properly with `file://` URLs on any platform, though it _may_ if the default application for HTML files is a browser.

This is a prototype package for testing implementations to be submitted to the standard library.

ref: https://github.com/python/cpython/issues/128540
