from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(r"C:\Users\v\AppData\Local\Programs\Python\Python312\python.exe")
if not PYTHON.exists():
    PYTHON = Path(sys.executable)
PORT = int(os.environ.get("NUTRIAI_SMOKE_PORT", "8502"))
URL = f"http://localhost:{PORT}"


def wait_for_server(timeout_sec: int = 45) -> None:
    deadline = time.time() + timeout_sec
    last_error = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(URL, timeout=2) as response:
                if response.status < 500:
                    return
        except Exception as exc:  # pragma: no cover - diagnostic script
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"Streamlit server did not become ready: {last_error}")


def main():
    log_path = PROJECT_ROOT / "ui_smoke_server.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [
                str(PYTHON),
                "-m",
                "streamlit",
                "run",
                "code\\app.py",
                "--server.port",
                str(PORT),
                "--server.headless",
                "true",
                "--browser.gatherUsageStats",
                "false",
            ],
            cwd=str(PROJECT_ROOT),
            stdout=log,
            stderr=log,
        )
        try:
            wait_for_server()
            screenshot_path = PROJECT_ROOT / "ui_smoke.png"
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1440, "height": 1050})
                page.goto(URL, wait_until="networkidle", timeout=60000)
                page.get_by_text("NutriAI", exact=True).wait_for(timeout=60000)
                page.get_by_text("Generate plan", exact=True).wait_for(timeout=60000)
                sidebar_title = page.get_by_text("Plan inputs", exact=True)
                sidebar_title.wait_for(timeout=60000)
                page.locator('[data-testid="stSidebarCollapseButton"] button').first.click(timeout=60000)
                expand_button = page.locator('button[data-testid="stExpandSidebarButton"]').first
                expand_button.wait_for(state="visible", timeout=60000)
                expand_box = expand_button.bounding_box()
                if expand_box is None or expand_box["width"] < 30 or expand_box["height"] < 30:
                    raise RuntimeError(f"Sidebar restore button is not visibly clickable: {expand_box}")
                expand_button.click(timeout=60000)
                sidebar_title.wait_for(timeout=60000)
                page.get_by_text("Generation", exact=True).wait_for(timeout=60000)
                page.get_by_text("Weekly macro mix", exact=True).wait_for(timeout=60000)
                page.get_by_text("7-day plan", exact=True).wait_for(timeout=60000)
                page.get_by_text("Menu item", exact=True).wait_for(state="attached", timeout=60000)
                page.get_by_text("Download meal plan CSV", exact=True).wait_for(timeout=60000)
                page.get_by_text("Sources", exact=True).click(timeout=60000)
                page.get_by_text("Source provenance", exact=True).wait_for(timeout=60000)
                page.get_by_text("USDA ingredient reference rows", exact=True).wait_for(state="attached", timeout=60000)
                page.get_by_text("Runtime external API calls", exact=True).wait_for(state="attached", timeout=60000)
                page.get_by_text("Plan", exact=True).click(timeout=60000)
                page.get_by_text("Weekly macro mix", exact=True).wait_for(timeout=60000)
                donut = page.locator("svg.macro-donut-svg")
                first_macro_slice = page.locator("svg.macro-donut-svg .macro-slice").nth(0)
                donut_box = donut.bounding_box()
                if donut_box is None:
                    raise RuntimeError("Macro donut was not laid out.")
                page.mouse.move(donut_box["x"] + donut_box["width"] * 0.62, donut_box["y"] + donut_box["height"] * 0.14)
                page.wait_for_timeout(300)
                tooltip_opacity = first_macro_slice.locator(".macro-svg-tooltip").evaluate(
                    "element => Number(getComputedStyle(element).opacity)"
                )
                if tooltip_opacity < 0.9:
                    raise RuntimeError(f"Macro tooltip did not appear; opacity={tooltip_opacity}")
                page.wait_for_timeout(2500)
                page.screenshot(path=str(screenshot_path), full_page=True)
                browser.close()
            print(f"UI smoke PASS: {URL}")
            print(f"Screenshot: {screenshot_path}")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)


if __name__ == "__main__":
    main()
