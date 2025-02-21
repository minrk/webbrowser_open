from __future__ import annotations

import ctypes.util
import sys
from ctypes import c_char_p, c_ulong, c_void_p
from typing import TYPE_CHECKING, cast, overload
from webbrowser import MacOSXOSAScript

if TYPE_CHECKING:
    from ctypes import _SimpleCData


def get_default_browser() -> str | None:
    """Identify the default browser"""
    # TODO: can these ever fail to load?
    objc_path = ctypes.util.find_library("objc")
    if objc_path is None:
        return None
    objc = ctypes.cdll.LoadLibrary(objc_path)
    for framework in ("Foundation", "AppKit"):
        framework_found = ctypes.util.find_library(framework)
        if framework_found:
            ctypes.cdll.LoadLibrary(framework_found)
        else:
            return None

    objc.objc_getClass.restype = c_void_p
    objc.sel_registerName.restype = c_void_p

    def getClass(name: str) -> int:
        return cast(int, objc.objc_getClass(name.encode()))

    def registerName(name: str) -> int:
        return cast(int, objc.sel_registerName(name.encode()))

    NSString = getClass("NSString")
    NSURL = getClass("NSURL")
    NSWorkspace = getClass("NSWorkspace")
    sharedWorkspace = registerName("sharedWorkspace")
    stringWithCString_encoding = registerName("stringWithCString:encoding:")
    URLWithString = registerName("URLWithString:")
    URLForApplicationToOpenURL = registerName("URLForApplicationToOpenURL:")
    fileSystemRepresentation = registerName("fileSystemRepresentation")
    # TODO: check if these can be None?

    @overload
    def msgSend(
        *args: int | bytes, argtypes: list[type[_SimpleCData]] | None = None
    ) -> int: ...
    @overload
    def msgSend(
        *args: int | bytes,
        argtypes: list[type[_SimpleCData]] | None = None,
        restype: type[c_char_p],
    ) -> bytes: ...
    def msgSend(
        *args: int | bytes,
        argtypes: list[type[_SimpleCData]] | None = None,
        restype: type[_SimpleCData] = c_void_p,
    ) -> bytes | int:
        if argtypes is None:
            argtypes = [c_void_p] * len(args)
        objc.objc_msgSend.argtypes = argtypes
        objc.objc_msgSend.restype = restype
        return objc.objc_msgSend(*args)  # type: ignore

    # We want to execute the equivalent of the objc:
    #    NSString *url_string =
    #        [NSString stringWithCString:"https://..."
    #                           encoding:NSUTF8StringEncoding];
    #   NSURL *http_url = [NSURL URLWithString:url_string];
    #   NSWorkspace *shared_ws = [NSWorkSpace sharedWorkspace];
    #   NSURL *app_url = [shared_ws URLForApplicationToOpenURL:http_url];
    #   char *app_path = [app_url fileSystemRepresentation];
    url_string = msgSend(
        NSString,
        stringWithCString_encoding,
        b"https://python.org",
        4,  # NSUTF8StringEncoding = 4
        argtypes=[c_void_p, c_void_p, c_char_p, c_ulong],
    )
    # Create an NSURL object representing the URL
    http_url = msgSend(NSURL, URLWithString, url_string)
    # get a handle on the shared workspace
    #     NSWorkspace *shared_ws = [NSWorkSpace sharedWorkspace];
    shared_ws = msgSend(NSWorkspace, sharedWorkspace)
    # Create an NSURL of the application associated with https urls
    # (the default browser)
    #   NSURL *app_url = [shared_ws URLForApplicationToOpenURL:http_url];
    app_url = msgSend(shared_ws, URLForApplicationToOpenURL, http_url)
    # get the URL as a filesystem path
    #   char *app_path = [app_url fileSystemRepresentation];
    app_path = msgSend(app_url, fileSystemRepresentation, restype=c_char_p)
    # decode path bytes to str, e.g. '/Applications/Safari.app'
    return app_path.decode(sys.getfilesystemencoding())


def make_opener() -> MacOSXOSAScript | None:
    browser = get_default_browser()
    if browser is None:
        return None
    return MacOSXOSAScript(browser)
