#!/usr/bin/env python3
"""Run the engine tests in a real browser, with no automation library.

    python3 test/run.py
    python3 test/run.py --browser "/path/to/chrome"
    python3 test/run.py --only dark

A throwaway HTTP server serves the fixture, harness.js drives every component
and posts its verdicts back, and this script reports them. It runs three times
— wide, narrow, and with a dark colour scheme — because a good number of the
failures worth catching only show up in one of them.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_browser(explicit: str | None) -> str | None:
    if explicit:
        return explicit if (Path(explicit).exists() or shutil.which(explicit)) else None
    for c in CANDIDATES:
        if Path(c).exists():
            return c
        found = shutil.which(c)
        if found:
            return found
    return None


class Collector(SimpleHTTPRequestHandler):
    payload: dict | None = None
    arrived = threading.Event()

    def do_POST(self):  # noqa: N802 - http.server's naming
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        try:
            Collector.payload = json.loads(body)
        except json.JSONDecodeError as e:
            Collector.payload = {"error": f"unreadable results: {e}", "raw": body[:400]}
        Collector.arrived.set()
        self.send_response(204)
        self.end_headers()

    def log_message(self, *_args):
        pass


def run_once(browser: str, width: int, height: int, timeout: float,
             extra_flags: list[str] | None = None) -> dict:
    Collector.payload = None
    Collector.arrived = threading.Event()

    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Collector, directory=str(ROOT)))
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    with tempfile.TemporaryDirectory() as profile:
        chrome = subprocess.Popen(
            [
                browser, "--headless=new", "--disable-gpu", "--no-first-run",
                "--no-default-browser-check", "--hide-scrollbars", "--mute-audio",
                f"--user-data-dir={profile}",
                f"--window-size={width},{height}",
                *(extra_flags or []),
                f"http://127.0.0.1:{port}/test/fixture.html",
            ],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        got = Collector.arrived.wait(timeout)
        chrome.terminate()
        try:
            chrome.wait(timeout=10)
        except subprocess.TimeoutExpired:
            chrome.kill()
        stderr = (chrome.stderr.read().decode("utf-8", "ignore") if chrome.stderr else "")

    server.shutdown()

    if not got:
        tail = [l for l in stderr.splitlines() if "ERROR" in l][-3:]
        raise SystemExit(
            f"the harness never reported back within {timeout:.0f}s.\n"
            + ("browser stderr: " + " | ".join(tail) if tail else
               "the page probably threw before the harness finished.")
        )
    return Collector.payload or {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser", default=os.environ.get("UNDERSTORY_BROWSER"))
    ap.add_argument("--only", choices=["desktop", "narrow", "dark"], default=None)
    ap.add_argument("--timeout", type=float, default=45.0)
    args = ap.parse_args()

    browser = find_browser(args.browser)
    if not browser:
        print("run: no Chrome, Chromium or Edge found. Pass --browser /path/to/chrome, "
              "or set UNDERSTORY_BROWSER.", file=sys.stderr)
        return 2

    # Chrome will not open a window narrower than ~500px; the harness measures a
    # true phone viewport in an iframe instead.
    runs = {
        "desktop": (1280, 1000, []),
        "narrow": (375, 800, []),
        "dark": (1280, 1000, ["--blink-settings=preferredColorScheme=0"]),
    }
    if args.only:
        runs = {args.only: runs[args.only]}

    total_failed = 0
    for label, (w, h, flags) in runs.items():
        report = run_once(browser, w, h, args.timeout, flags)
        if "error" in report:
            print(f"{label}: {report['error']}")
            return 1
        total_failed += report.get("failed", 0)

        print(f"\n{label} ({report['viewport']}px, {report.get('scheme', '?')} scheme): "
              f"{report['passed']} passed, {report['failed']} failed")
        for r in report["results"]:
            if r["ok"]:
                print(f"  ok   {r['name']}")
            else:
                print(f"  FAIL {r['name']}\n         {r.get('detail', '')}")

    print()
    if total_failed:
        print(f"✗ {total_failed} failing assertion(s).")
        return 1
    print("✓ engine tests pass at every viewport.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
