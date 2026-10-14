#!/usr/bin/env python3
"""Intentionally look for a missing element in real Chrome and retain evidence.

Usage: python automation/capture_missing_element.py [--out DIR]

Exit 0 only if Selenium raised the expected NoSuchElementException/TimeoutException
and a nonempty screenshot plus context file were written. Otherwise nonzero.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from automation import helpers  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MISSING_ID = "intentionally-missing-element"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(ROOT / "evidence" / "intentional-missing-element"))
    args = parser.parse_args(argv)
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:8765")

    from selenium.common.exceptions import NoSuchElementException, TimeoutException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait

    driver = None
    try:
        driver, identity = helpers.start_browser(
            headed=os.environ.get("HEADED") == "1",
            binary=os.environ.get("CHROME_BINARY") or None,
            driver_path=os.environ.get("CHROMEDRIVER") or None)
        print(f"[capture] browser: {identity}")
        driver.get(base_url)
        WebDriverWait(driver, 5).until(
            lambda d: d.find_element(By.ID, "settings").get_attribute("aria-busy") == "false")
        caught = None
        try:
            WebDriverWait(driver, 2).until(lambda d: d.find_element(By.ID, MISSING_ID))
        except (NoSuchElementException, TimeoutException) as exc:
            caught = exc
        if caught is None:
            print("[capture] FAILED: missing element was unexpectedly found")
            return 1
        result = helpers.capture_failure_evidence(driver, args.out, "missing_element", caught)
    except helpers.BrowserStartupError as exc:
        print(f"[capture] BLOCKED: {exc}")
        return 125
    finally:
        if driver is not None:
            driver.quit()

    png = Path(result["screenshot"]) if result["screenshot"] else None
    context = Path(result["context"])
    if not (png and png.exists() and png.stat().st_size > 0 and context.stat().st_size > 0):
        print(f"[capture] FAILED: evidence incomplete: {result}")
        return 2
    print(f"[capture] expected failure caught: {type(caught).__name__}")
    print(f"[capture] evidence: {png} ({png.stat().st_size} bytes), {context}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
