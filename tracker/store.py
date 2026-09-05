"""Shared JSON task store. Both the watcher process and the Streamlit UI read/write this file,
so writes are atomic (write to a temp file, then replace) to avoid corrupting it if both touch
it at nearly the same moment."""
import json
import os
import time
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "tasks.json"

STATUSES = ("todo", "doing", "done")


def load_tasks() -> list[dict]:
    if not DATA_PATH.exists():
        save_tasks([])
    for attempt in range(3):
        try:
            return json.loads(DATA_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            if attempt == 2:
                raise
            time.sleep(0.05)
    return []


def save_tasks(tasks: list[dict]) -> None:
    DATA_PATH.parent.mkdir(exist_ok=True)
    tmp_path = DATA_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
    os.replace(tmp_path, DATA_PATH)


def update_task(task_id: str, **fields) -> None:
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t.update(fields)
            break
    save_tasks(tasks)
