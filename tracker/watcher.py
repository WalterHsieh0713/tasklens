"""Background loop: watches the active window title (every few seconds) and periodically OCRs
the screen, fuzzy-matches what it sees against your task list, and bumps a matching To Do task
to In Progress. Runs as its own process -- `python watcher.py` -- separate from the Streamlit
UI, communicating only through data/tasks.json.
"""
import time
from datetime import datetime, timezone

import mss
import win32gui
import winocr
from PIL import Image

from tracker import store
from tracker.matcher import best_match

WINDOW_CHECK_INTERVAL = 5   # seconds between active-window-title checks
OCR_INTERVAL = 20           # seconds between full-screen OCR passes (heavier, so less often)


def get_active_window_title() -> str:
    hwnd = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(hwnd) or ""


def capture_screen_text() -> str:
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        shot = sct.grab(monitor)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    result = winocr.recognize_pil_sync(img, lang="en")
    return result.get("text", "")


def process_activity(haystack: str, elapsed_seconds: float) -> None:
    tasks = store.load_tasks()
    task, score = best_match(haystack, tasks)
    if task is None:
        return

    changed = False

    if task["status"] == "todo":
        task["status"] = "doing"
        changed = True

    # Only bill time to a task while it's actively "doing" and its content is
    # what's currently on screen -- this is what makes the tracked total mean
    # "time spent working on this," not just "time since it was created."
    if task["status"] == "doing":
        task["time_spent_seconds"] = task.get("time_spent_seconds", 0) + elapsed_seconds
        changed = True

    snippet = haystack.strip()[:200]
    if task.get("last_detected_activity") != snippet:
        task["last_detected_activity"] = snippet
        changed = True

    if changed:
        task["last_updated"] = datetime.now(timezone.utc).isoformat()
        store.save_tasks(tasks)
        print(f"[watcher] {task['title']} -> {task['status']} (match score {score}, +{elapsed_seconds:.0f}s)")


def main():
    print("Watcher started. Checking active window every "
          f"{WINDOW_CHECK_INTERVAL}s, full OCR every {OCR_INTERVAL}s. Ctrl+C to stop.")
    last_ocr = 0.0
    last_loop = time.time()
    while True:
        try:
            now = time.time()
            elapsed = now - last_loop
            last_loop = now

            title = get_active_window_title()
            haystack = title

            if time.time() - last_ocr >= OCR_INTERVAL:
                try:
                    haystack = f"{title}\n{capture_screen_text()}"
                except Exception as exc:
                    print(f"[watcher] OCR failed, falling back to window title only: {exc}")
                last_ocr = time.time()

            if haystack.strip():
                process_activity(haystack, elapsed)
        except Exception as exc:
            print(f"[watcher] loop error (continuing): {exc}")

        time.sleep(WINDOW_CHECK_INTERVAL)


if __name__ == "__main__":
    main()
