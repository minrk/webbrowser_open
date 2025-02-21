# webbrowser_open

prototyping opening things with the default webbrowser

## Use

The simplest way to use this package is to replace:

```python
import webbrowser

...
webbrowser.open(url)
```

with

```python
import webbrowser_open

...
webbrowser_open.open(url)
```

You can also launch a URL with

```
python3 -m webbrowser_open URL
```

to see the difference (if any) in your environment.

The only difference in behavior is that `webbrowser_open` looks up the default browser application before opening the URL.
This should only result in a change in behavior for opening `file://` URLs
where the default application associated with the file type is used instead of the default browser.

The $BROWSER environment variable still takes priority, if defined,
in which case `webbrowser_open.open` just wraps a call to `webbrowser.open` with no changes.

This package uses the following APIs to explicitly launch the default browser:

| platform | API                                                                                                                                         | notes                                                                                                                                                                                                                |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| mac      | [URLForApplicationToOpenURL](<https://developer.apple.com/documentation/appkit/nsworkspace/urlforapplication(toopen:)-7qkzf?language=objc>) | requires ctypes and access to libobjc. This is the mac equivalent to the [ios implementation in Python 3.13](https://github.com/python/cpython/blob/5d66c55c8ad0a0aeff8d06021ddca1d02c5f4416/Lib/webbrowser.py#L627) |
| Windows  | HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\https\\UserChoice                                    | I don't yet know which cases this might not work for (UWP, minumum Windows versions, etc.), but it works in my own limited tests                                                                                     |
| linux    | `xdg-settings get default-webbrowser` or `xdg-mime query default x-scheme-handler/https` plus `gtk-launch` or `gio launch`                  | `gtk-launch` appears to locate .deskop files correctly, while `gio launch` only appears to accept absolute paths. I'm not sure how many different ways there are to lookup and/or launch default browsers on linux.  |

## Background

Most platforms have at least a semi-standard way to open URLs and discover the default browser.

`webbrowser.open` uses generic not-browser-specific APIs (e.g. `open`, `xdg-open`, `os.startfile`), which works fine with `http[s]` URLs.
However, all of these systems associate `file://` URLs with the default application for the file type, _not necessary_ a webbrowser, which `webbrowser.open` is meant to launch.
The result is often `webbrowser.open` launching a file editor instead of a browser.

`webbrowser.open` does not work reliably with `file://` URLs on any platform, though it _may_ if the default application for HTML files is a browser,
which it often is, except for developers.

Linux is in the best situation by default, because it does call [`xdg-settings get default-web-browser`](https://github.com/python/cpython/blob/5d66c55c8ad0a0aeff8d06021ddca1d02c5f4416/Lib/webbrowser.py#L524) to actually lookup a browser,
but it only uses this if a matching browser is already known ahead of time and found in [`register_X_browsers`](https://github.com/python/cpython/blob/5d66c55c8ad0a0aeff8d06021ddca1d02c5f4416/Lib/webbrowser.py#L421).
This is still known to fail [at least sometimes](https://github.com/jupyter/notebook/issues/4304).

This is a prototype package for testing implementations to be submitted to the standard library.

ref: https://github.com/python/cpython/issues/128540
