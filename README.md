# TaskLens

A task manager that watches what's actually on your screen to keep itself up
to date. It pairs a Kanban board and a Google Calendar-style calendar (built
on Streamlit + FullCalendar) with a background OCR/window-title watcher that
auto-advances tasks and times how long you spend on each one — no manual
status updates required.

## Features

- **Board view** — tasks grouped into To Do / In Progress / Done, with tags,
  due dates/times, and a running "time spent" timer per task.
- **Calendar view** — month/week/list views. Click a day to set a due date,
  or click a time slot in week/day view to set a due date *and* time, like
  Google Calendar Tasks. Tasks with a time render as timed events; tasks
  without one stay as all-day chips.
- **Screen watcher** (`tracker/watcher.py`) — runs as its own process,
  periodically checks the active window title and OCRs the screen, then
  fuzzy-matches what it sees against your task titles. A match:
  - flips a matching To Do task to In Progress automatically, and
  - accumulates time spent on whichever task is currently in progress and
    on screen.
- Filters (search, tag, sort), light/dark theme that follows Streamlit's own
  theme setting, and a "+ Create" dialog for adding tasks by hand.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Running it

Two separate processes, both from the project root:

```bash
streamlit run app.py            # the UI, at http://localhost:8501
python -m tracker.watcher        # the screen watcher (optional, but needed
                                  # for auto-advance + time tracking)
```

The watcher is Windows-only (it uses `pywin32` for the active window title)
and needs no configuration — it reads/writes the same `data/tasks.json` file
the UI uses.

## Project structure

```
app.py               Streamlit UI: board + calendar
tracker/
  store.py           Shared JSON task store (atomic read/write)
  matcher.py         Fuzzy-matches on-screen text against task titles
  watcher.py         Background loop: window title + OCR -> task updates
data/tasks.json      The task list (created automatically, gitignored)
```
