import argparse
import os
import sys
import webbrowser

import webbrowser_open


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="The URL to open")
    args = parser.parse_args()
    browser = webbrowser_open.get_default_browser()
    stdlib_default = webbrowser.get()
    # not all stdlibs have .name (at least on Python 3.9, they seem to on 3.13)
    stdlib_name = getattr(
        stdlib_default, "name", getattr(stdlib_default, "_name", str(stdlib_default))
    )
    print(f"Stdlib found default: {stdlib_name}", file=sys.stderr)
    if browser:
        print(f"Found default browser: {browser}", file=sys.stderr)
    else:
        print("No default browser found, falling back on stdlib", file=sys.stderr)
    if os.environ.get("BROWSER"):
        print(f"Found $BROWSER={os.environ['BROWSER']}, ignoring system default")
    webbrowser_open.open(args.url)


if __name__ == "__main__":
    main()
