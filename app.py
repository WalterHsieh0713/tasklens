from datetime import date, datetime, time as dtime

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_calendar import calendar

from tracker import store

st.set_page_config(page_title="TaskLens", page_icon="\U0001F4C5", layout="wide")
st_autorefresh(interval=8000, key="board_refresh")  # picks up watcher.py's updates automatically

# Streamlit's own Settings menu lets a user force light/dark independently of
# the OS, so we drive our colors off the theme Streamlit actually resolved
# (st.context.theme.type) instead of the OS-only `prefers-color-scheme`.
# Using the media query alone meant picking "Light" in Settings while the OS
# was dark left our custom colors dark while Streamlit's own widgets went
# light -- a broken, half-and-half look.
IS_DARK = st.context.theme.type == "dark"

STATUS_META = {
    "todo": {"label": "To Do", "color": "#ea4335"},
    "doing": {"label": "In Progress", "color": "#fbbc04"},
    "done": {"label": "Done", "color": "#34a853"},
}

# ----------------------------------------------------------------------------
# Global styling: Google Calendar-inspired look (Roboto type, soft shadows,
# pill buttons/tabs) with fade/lift transitions on load and on hover.
# ----------------------------------------------------------------------------
# Theme variables get their own tiny f-string block (kept separate from the
# large static stylesheet below so nothing there needs brace-escaping).
st.markdown(
    f"""
    <style>
    :root {{
        --gc-blue: #1a73e8;
        --gc-blue-light: {"rgba(26,115,232,0.18)" if IS_DARK else "#e8f0fe"};
        --gc-border: {"#3c4043" if IS_DARK else "#dadce0"};
        --gc-text: {"#e8eaed" if IS_DARK else "#3c4043"};
        --gc-text-soft: {"#9aa0a6" if IS_DARK else "#70757a"};
        --gc-app-bg: {"#131314" if IS_DARK else "#f1f3f4"};
        --gc-surface: {"#1e1f20" if IS_DARK else "#ffffff"};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], .stApp, button, input, textarea, select {
        font-family: 'Roboto', 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif !important;
    }

    @keyframes fadeInUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

    .stApp { background: var(--gc-app-bg); }
    .block-container { animation: fadeIn .5s ease; padding-top: 2rem; max-width: 1200px; }

    /* Today's date, shown as its own strip at the very top of the page */
    .tt-date-strip { display: flex; align-items: center; gap: 16px; margin-bottom: 22px; animation: fadeInUp .4s ease; }
    .tt-date-circle {
        width: 54px; height: 54px; border-radius: 50%; flex-shrink: 0;
        background: var(--gc-blue); color: #fff; font-weight: 700; font-size: 1.6rem;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 1px 3px rgba(60,64,67,.35);
    }
    .tt-date-text { display: flex; flex-direction: column; line-height: 1.25; }
    .tt-date-dow { font-size: .85rem; font-weight: 700; letter-spacing: .6px; text-transform: uppercase; color: var(--gc-blue); }
    .tt-date-full { font-size: 1.3rem; font-weight: 500; color: var(--gc-text); }

    /* Header */
    .tt-title { font-size: 2.3rem; font-weight: 600; color: var(--gc-text); margin: 0; display:flex; align-items:center; gap:.6rem; animation: fadeInUp .5s ease; }
    .tt-caption { color: var(--gc-text-soft); font-size: .95rem; margin-top: 4px; animation: fadeInUp .6s ease; }

    /* Buttons */
    .stButton > button {
        border-radius: 20px !important;
        transition: box-shadow .15s ease, transform .1s ease, background .15s ease !important;
        border: 1px solid var(--gc-border) !important;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(60,64,67,.2); }
    .stButton > button:active { transform: translateY(0); }
    .stButton > button[kind="primary"] {
        background: var(--gc-blue) !important;
        border: none !important;
        box-shadow: 0 1px 3px rgba(60,64,67,.3);
    }
    .stButton > button[kind="primary"]:hover { background: #1765cc !important; box-shadow: 0 3px 10px rgba(26,115,232,.4); }

    [data-testid="stPopoverButton"] { border-radius: 20px !important; }

    /* Metrics as soft, liftable cards */
    [data-testid="stMetric"] {
        background: var(--gc-blue-light);
        border-radius: 16px;
        padding: 12px 18px;
        box-shadow: 0 1px 2px rgba(60,64,67,.12);
        transition: transform .15s ease, box-shadow .15s ease;
        animation: fadeInUp .6s ease;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(60,64,67,.18); }

    .stProgress > div > div > div { border-radius: 8px; background: var(--gc-blue) !important; transition: width .3s ease; }

    /* Tabs styled as a segmented pill control */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(60,64,67,.06);
        padding: 4px;
        border-radius: 24px;
        width: fit-content;
        animation: fadeInUp .5s ease;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 20px;
        padding: 8px 22px;
        transition: background .15s ease, color .15s ease;
        color: var(--gc-text-soft);
    }
    .stTabs [data-baseweb="tab"] p { font-size: 1.05rem; font-weight: 500; }
    .stTabs [aria-selected="true"] {
        background: var(--gc-surface) !important;
        color: var(--gc-text) !important;
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(60,64,67,.2);
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-panel"] { animation: fadeIn .35s ease; }

    /* Task rows / cards */
    .task-row {
        border-radius: 14px;
        padding: 11px 16px;
        margin-bottom: 8px;
        line-height: 1.6;
        border: 1px solid transparent;
        transition: transform .15s ease, box-shadow .15s ease;
        animation: fadeInUp .45s ease both;
        box-shadow: 0 1px 2px rgba(60,64,67,.08);
    }
    .task-row:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(60,64,67,.18); }
    .task-row .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; }
    .task-row .title { font-weight: 600; font-size: 0.92rem; }
    .task-row .tag { font-size: 0.8rem; opacity: 0.65; }
    .task-row .due { font-size: 0.8rem; opacity: 0.75; }
    .task-row .due.overdue { color: #ff8080; opacity: 1; font-weight: 600; }
    .task-row .activity { display: block; font-size: 0.72rem; opacity: 0.5; margin-top: 2px; margin-left: 16px; }
    .task-timer {
        display: block; font-size: 0.78rem; font-weight: 600;
        margin-top: 4px; margin-left: 16px;
    }

    div[data-testid='stVerticalBlockBorderWrapper'] { border: none !important; }
    div[data-baseweb='select'] > div { min-height: 34px; }

    /* streamlit-calendar only reports its height to the host once, before
       FullCalendar finishes laying out, so the surrounding iframe gets stuck
       at height 0. Force it open at the height we asked the calendar for,
       and treat it as an elevated card so it matches the rest of the UI. */
    iframe[title="streamlit_calendar.calendar"] {
        height: 700px !important;
        min-height: 700px !important;
        border-radius: 22px !important;
        border: 1px solid var(--gc-border) !important;
        box-shadow: 0 1px 2px rgba(60,64,67,.15), 0 2px 10px rgba(60,64,67,.1) !important;
        overflow: hidden !important;
        animation: fadeInUp .45s ease both;
    }

    /* Status legend chips above the calendar */
    .status-legend { display: flex; gap: 18px; margin: 4px 0 16px; animation: fadeInUp .5s ease; }
    .status-legend .chip { display: flex; align-items: center; gap: 6px; font-size: .82rem; color: var(--gc-text-soft); }
    .status-legend .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
    </style>
    """,
    unsafe_allow_html=True,
)

today = date.today()
st.markdown(
    f"""
    <div class="tt-date-strip">
        <span class="tt-date-circle">{today.day}</span>
        <span class="tt-date-text">
            <span class="tt-date-dow">{today.strftime('%A')}</span>
            <span class="tt-date-full">{today.strftime('%B')} {today.day}, {today.year}</span>
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

tasks = store.load_tasks()

# --- Header row: title, a collapsible Filters popover, and a standalone Create button ---
head_title, head_filters, head_create = st.columns([6, 1.4, 1.4], vertical_alignment="center")

with head_title:
    st.markdown("<p class='tt-title'>\U0001F4C5 TaskLens</p>", unsafe_allow_html=True)
    st.markdown(
        "<p class='tt-caption'>watcher.py runs separately, auto-advances tasks it detects on screen, and times how long you spend on each.</p>",
        unsafe_allow_html=True,
    )

with head_filters:
    with st.popover("⚙️ Filters", use_container_width=True):
        search = st.text_input("Search title/tag")
        tags = sorted({t["tag"] for t in tasks if t.get("tag")})
        tag_filter = st.multiselect("Tag", tags, default=[])
        sort_by = st.radio("Sort by", ["Due date", "Recently updated"], horizontal=False)
        max_per_section = st.slider("Max tasks shown per section", 10, 200, 40, step=10)


def _local_dt(iso_str: str) -> datetime:
    """FullCalendar reports times as UTC ISO strings even though they were
    picked in the browser's local time; since the server and browser are the
    same machine here, converting back to local time recovers what was
    actually clicked."""
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).astimezone()


@st.dialog("New task")
def add_task_dialog(prefill_due: date | None = None, prefill_time: dtime | None = None):
    new_title = st.text_input("Title")
    new_tag = st.text_input("Tag (optional)")
    has_due = st.checkbox("Set a due date", value=prefill_due is not None)
    new_due = st.date_input("Due date", value=prefill_due or date.today()) if has_due else None
    has_time = has_due and st.checkbox("Set a due time", value=prefill_time is not None)
    new_time = st.time_input("Due time", value=prefill_time or dtime(23, 59)) if has_time else None
    if st.button("Add task", type="primary", use_container_width=True):
        if new_title.strip():
            tasks.append({
                "id": f"task-{len(tasks)}-{datetime.now().timestamp():.0f}",
                "title": new_title.strip(),
                "tag": new_tag.strip(),
                "due_date": new_due.isoformat() if new_due else None,
                "due_time": new_time.strftime("%H:%M") if new_time else None,
                "status": "todo",
                "last_detected_activity": None,
                "last_updated": None,
                "time_spent_seconds": 0,
            })
            store.save_tasks(tasks)
            st.rerun()
        else:
            st.warning("Give the task a title first.")


with head_create:
    if st.button("➕ Create", type="primary", use_container_width=True):
        add_task_dialog()


def matches_filters(task: dict) -> bool:
    if search and search.lower() not in (task["title"] + " " + task.get("tag", "")).lower():
        return False
    if tag_filter and task.get("tag") not in tag_filter:
        return False
    return True


filtered = [t for t in tasks if matches_filters(t)]


def sort_key(task: dict):
    if sort_by == "Due date":
        return (task.get("due_date") is None, task.get("due_date") or "")
    return task.get("last_updated") or "", True


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def format_time_12h(hhmm: str) -> str:
    hour, minute = (int(part) for part in hhmm.split(":"))
    period = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12 or 12
    return f"{hour_12}:{minute:02d} {period}"


def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


# --- Summary metrics ---
counts = {s: sum(1 for t in tasks if t["status"] == s) for s in STATUS_META}
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total tasks", len(tasks))
m2.metric("To Do", counts["todo"])
m3.metric("In Progress", counts["doing"])
m4.metric("Done", counts["done"])
st.progress(counts["done"] / len(tasks) if tasks else 0)

st.divider()

if not tasks:
    st.info("No tasks yet -- add your first one with the ➕ Create button above.")

today_iso = date.today().isoformat()
board_tab, calendar_tab = st.tabs(["\U0001F4CB Board", "\U0001F4C5 Calendar"])

# --- Board, Notion-style tinted cards grouped by status (full-width sections) ---
with board_tab:
    for status in STATUS_META:
        meta = STATUS_META[status]
        section_tasks = sorted(
            (t for t in filtered if t["status"] == status), key=sort_key
        )[:max_per_section]

        st.markdown(
            f"<div style='font-weight:600; font-size:1.15rem; color:{meta['color']}; margin:16px 0 10px;'>"
            f"{meta['label']} &middot; {sum(1 for t in filtered if t['status'] == status)}</div>",
            unsafe_allow_html=True,
        )

        for row_idx, task in enumerate(section_tasks):
            row_text, row_status = st.columns([5, 3], vertical_alignment="center")
            with row_text:
                tag_html = f'<span class="tag"> &middot; {task["tag"]}</span>' if task.get("tag") else ""
                due_html = ""
                if task.get("due_date"):
                    overdue = task["due_date"] < today_iso and status != "done"
                    due_cls = "due overdue" if overdue else "due"
                    due_label = "Overdue" if overdue else "Due"
                    due_when = task["due_date"]
                    if task.get("due_time"):
                        due_when += " at " + format_time_12h(task["due_time"])
                    due_html = f'<span class="{due_cls}"> &middot; {due_label} {due_when}</span>'
                activity_html = ""
                if task.get("last_detected_activity"):
                    activity_html = f"<div class='activity'>\U0001F441 {task['last_detected_activity'][:90]}</div>"
                timer_html = ""
                time_spent = task.get("time_spent_seconds", 0)
                if time_spent:
                    timer_html = (
                        f"<div class='task-timer' style='color:{meta['color']}'>"
                        f"⏱️ {format_duration(time_spent)} spent"
                        f"</div>"
                    )
                row_style = (
                    f"background:{hex_to_rgba(meta['color'], 0.1)}; "
                    f"border-color:{hex_to_rgba(meta['color'], 0.28)}; "
                    f"animation-delay: {min(row_idx * 0.03, 0.6):.2f}s;"
                )
                row_html = (
                    f'<div class="task-row" style="{row_style}">'
                    f'<span class="status-dot" style="background:{meta["color"]}"></span>'
                    f'<span class="title">{task["title"]}</span>{tag_html}{due_html}'
                    f'{timer_html}'
                    f'{activity_html}'
                    f'</div>'
                )
                st.markdown(row_html, unsafe_allow_html=True)
            with row_status:
                new_status = st.segmented_control(
                    "Status",
                    options=list(STATUS_META.keys()),
                    format_func=lambda s: STATUS_META[s]["label"],
                    default=task["status"],
                    required=True,
                    key=f"status-{task['id']}",
                    label_visibility="collapsed",
                )
                if new_status != task["status"]:
                    store.update_task(task["id"], status=new_status)
                    st.rerun()

# --- Calendar, Google Calendar-style month/week/agenda views of due dates ---
with calendar_tab:
    dated = [t for t in filtered if t.get("due_date")]
    undated_count = len(filtered) - len(dated)

    events = []
    for task in dated:
        has_time = bool(task.get("due_time"))
        event = {
            "id": task["id"],
            "title": task["title"] + (f" ({task['tag']})" if task.get("tag") else ""),
            "start": f"{task['due_date']}T{task['due_time']}:00" if has_time else task["due_date"],
            "allDay": not has_time,
            "color": STATUS_META[task["status"]]["color"],
        }
        if not has_time:
            event["end"] = task["due_date"]
        events.append(event)

    legend_html = "<div class='status-legend'>" + "".join(
        f"<span class='chip'><span class='dot' style='background:{meta['color']}'></span>{meta['label']}</span>"
        for meta in STATUS_META.values()
    ) + "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)

    calendar_options = {
        "initialView": "dayGridMonth",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listMonth",
        },
        "height": 700,
        "editable": False,
        "eventDisplay": "block",
        "dayMaxEvents": 3,
        "fixedWeekCount": False,
        "firstDay": 0,
        # Selection is off by default -- month view only creates tasks via a
        # plain click (dateClick, below), never a drag. It's switched back on
        # for the timeGrid views so a click there can capture a specific time
        # of day, but selectMinDistance is set absurdly high everywhere so an
        # actual drag never completes -- only a zero-movement click resolves,
        # which is what disables dragging while keeping click-to-set-time.
        "selectable": False,
        "selectMirror": True,
        "unselectAuto": True,
        "selectMinDistance": 9999,
        "views": {
            "timeGridWeek": {"selectable": True},
            "timeGridDay": {"selectable": True},
        },
    }

    calendar_css = """
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600;700&display=swap');

    .fc {
        font-family: 'Roboto', 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
        --fc-border-color: transparent;
        padding: 6px 10px 10px;
    }
    .fc-icon { font-family: "fcicons" !important; }

    /* Toolbar */
    .fc .fc-toolbar { padding: 6px 6px 18px; }
    .fc .fc-toolbar-title { font-size: 1.35rem; font-weight: 500; color: #3c4043; letter-spacing: -.2px; }
    .fc .fc-button-group { gap: 4px; }
    .fc .fc-prev-button, .fc .fc-next-button {
        background: transparent; border: none; color: #5f6368; width: 36px; height: 36px;
        border-radius: 50%; padding: 0; display: inline-flex; align-items: center; justify-content: center;
        box-shadow: none; transition: background .15s ease, transform .1s ease;
    }
    .fc .fc-prev-button:hover, .fc .fc-next-button:hover { background: #f1f3f4; }
    .fc .fc-prev-button:active, .fc .fc-next-button:active { background: #e8eaed; transform: scale(.88); }
    .fc .fc-today-button {
        background: #fff; border: 1px solid #dadce0; color: #3c4043; margin-left: 10px;
        border-radius: 999px; padding: 7px 18px; text-transform: capitalize; box-shadow: none;
        transition: background .15s ease, box-shadow .15s ease;
    }
    .fc .fc-today-button:hover:not(:disabled) { background: #f1f3f4; }
    .fc .fc-today-button:disabled { opacity: .5; }
    .fc .fc-dayGridMonth-button, .fc .fc-timeGridWeek-button, .fc .fc-listMonth-button {
        background: #fff; border: 1px solid #dadce0 !important; color: #3c4043;
        padding: 7px 16px; text-transform: capitalize; box-shadow: none;
        border-radius: 999px !important; margin: 0 2px;
        transition: background .15s ease, box-shadow .15s ease;
    }
    .fc .fc-button:hover { background: #f1f3f4; }
    .fc .fc-button-primary:not(:disabled).fc-button-active {
        background: #fff !important; color: #3c4043 !important; border-color: #3c4043 !important;
        font-weight: 600;
    }
    .fc .fc-button-primary:focus, .fc .fc-button:focus { box-shadow: none; outline: none; }

    /* Seamless view switching: FullCalendar swaps in a fresh .fc-view node
       whenever you change Month/Week/List (or navigate dates), so animating
       that node on insert gives every switch a soft fade+rise instead of an
       abrupt pop. */
    .fc-view-harness { transition: height .25s ease; }
    .fc-view-harness > .fc-view {
        animation: fcViewIn .32s cubic-bezier(.2,.8,.2,1) both;
    }
    @keyframes fcViewIn {
        from { opacity: 0; transform: translateY(6px) scale(.995); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    /* Grid -- keep only faint horizontal separators, no vertical rules, for a
       softer / less boxed-in look than the FullCalendar default grid. */
    .fc-theme-standard td, .fc-theme-standard th { border: none; }
    .fc-col-header-cell {
        background: transparent; text-transform: uppercase; font-size: .7rem;
        font-weight: 600; letter-spacing: .5px; color: #70757a; padding: 10px 0 12px;
        border-bottom: 1px solid #eceff1 !important;
    }
    .fc-daygrid-day { border-bottom: 1px solid #f1f3f4 !important; }
    .fc-daygrid-day-frame { padding: 4px; }
    .fc-daygrid-day-top { padding: 6px; }
    .fc-daygrid-day-number {
        color: #3c4043; font-size: .82rem; padding: 4px 9px; margin: 2px;
        border-radius: 999px; transition: background .15s ease;
    }
    .fc-daygrid-day:hover .fc-daygrid-day-number { background: #f1f3f4; }
    .fc-day-today .fc-daygrid-day-number {
        background: #1a73e8; color: #fff !important; font-weight: 600;
    }
    /* The td itself uses border-collapse, which makes border-radius/background
       render inconsistently (a highlight box that doesn't fill the cell) --
       painting the inner frame div instead avoids that and insets evenly. */
    .fc-daygrid-day.fc-day-today { background: transparent; }
    .fc-day-today .fc-daygrid-day-frame { background: #e8f0fe80; border-radius: 12px; transition: background .2s ease; }
    .fc-day-sat, .fc-day-sun { background: rgba(60,64,67,.015); }
    .fc-daygrid-day-events { margin-top: 3px !important; }
    .fc-daygrid-day-frame { cursor: pointer; }

    /* Click-to-set-time preview (month view is not selectable, so this only
       ever shows for the single slot a click in week/day view resolves to) */
    .fc-highlight { background: rgba(26,115,232,.16); border-radius: 8px; }

    /* Week/day time grid: pointer cursor plus a skinny line across whichever
       half-hour slot the mouse is over, standing in for a moving "current
       time" guide since FullCalendar has no built-in hover-tracking line. */
    .fc-timegrid-slot-lane, .fc-timegrid-col-frame { cursor: pointer; }
    .fc-timegrid-slot-lane:hover {
        background: rgba(26,115,232,.06);
        box-shadow: inset 0 1px 0 0 #1a73e8;
    }

    /* Cells (and timegrid columns / list rows) are recreated on every prev/next
       navigation even though the surrounding view isn't, so a subtle fade-in
       on them makes date navigation feel as smooth as switching views. */
    .fc-daygrid-day, .fc-timegrid-col, .fc-list-event, .fc-list-day {
        animation: fcCellIn .22s ease both;
    }
    @keyframes fcCellIn { from { opacity: 0; } to { opacity: 1; } }

    /* Events -- rounder chips with more breathing room than a flush block */
    .fc-event {
        border: none; border-radius: 8px; padding: 4px 8px; margin: 2px 6px !important;
        font-size: .76rem; font-weight: 500; cursor: pointer;
        transition: transform .12s ease, box-shadow .12s ease;
    }
    .fc-event:hover { transform: translateY(-1px) scale(1.01); box-shadow: 0 2px 8px rgba(0,0,0,.22); }
    .fc-daygrid-more-link { font-size: .74rem; font-weight: 500; color: #1a73e8; margin-left: 6px; }
    .fc-daygrid-more-link:hover { text-decoration: none; color: #1765cc; }

    /* List view */
    .fc-list { border-radius: 16px; overflow: hidden; border: 1px solid #eceff1 !important; }
    .fc-list-day-cushion { background: #f8f9fa !important; font-weight: 600; }
    .fc-list-event:hover td { background: #f1f3f4 !important; cursor: pointer; }
    .fc-list-event-dot { border-radius: 50%; border-width: 5px !important; }
    .fc-list-table td { border-color: #f1f3f4 !important; }

    .fc-scrollgrid { border: none !important; border-radius: 0 0 18px 18px; overflow: hidden; }

    """

    # Streamlit's own Settings menu can put the app in a different theme than
    # the OS, so (like the main page CSS) this follows IS_DARK -- resolved
    # from st.context.theme.type -- instead of a `prefers-color-scheme` guess
    # that could disagree with what Streamlit itself is actually showing.
    if IS_DARK:
        calendar_css += """
        .fc { background: #1e1f20; }
        .fc-col-header-cell { color: #9aa0a6; border-color: #3c4043 !important; }
        .fc-daygrid-day { border-color: #2d2e30 !important; }
        .fc .fc-toolbar-title, .fc-daygrid-day-number { color: #e8eaed; }
        .fc .fc-button, .fc .fc-today-button { background: #2d2e30; border-color: #3c4043 !important; color: #e8eaed; }
        .fc .fc-button:hover, .fc .fc-prev-button:hover, .fc .fc-next-button:hover { background: #3c4043; }
        .fc .fc-button-primary:not(:disabled).fc-button-active {
            background: #2d2e30 !important; color: #8ab4f8 !important; border-color: #8ab4f8 !important;
        }
        .fc-day-today .fc-daygrid-day-frame { background: rgba(26,115,232,.18); }
        .fc-daygrid-day:hover .fc-daygrid-day-number { background: #3c4043; }
        .fc-day-sat, .fc-day-sun { background: rgba(255,255,255,.02); }
        .fc-list { border-color: #3c4043 !important; }
        .fc-list-day-cushion { background: #2d2e30 !important; color: #e8eaed; }
        .fc-list-event:hover td { background: #2d2e30 !important; }
        .fc-list-table td { border-color: #3c4043 !important; }
        """

    clicked = calendar(events=events, options=calendar_options, custom_css=calendar_css, key="task_calendar")

    if undated_count:
        st.caption(f"{undated_count} task(s) have no due date and aren't shown on the calendar.")

    if clicked.get("eventClick"):
        clicked_id = clicked["eventClick"]["event"]["id"]
        clicked_task = next((t for t in tasks if t["id"] == clicked_id), None)
        if clicked_task:
            st.divider()
            st.markdown(f"**{clicked_task['title']}**")
            if clicked_task.get("time_spent_seconds"):
                st.caption(f"⏱️ {format_duration(clicked_task['time_spent_seconds'])} spent")
            new_status = st.segmented_control(
                "Status",
                options=list(STATUS_META.keys()),
                format_func=lambda s: STATUS_META[s]["label"],
                default=clicked_task["status"],
                required=True,
                key=f"cal-status-{clicked_task['id']}",
            )
            if new_status != clicked_task["status"]:
                store.update_task(clicked_task["id"], status=new_status)
                st.rerun()

    # Click an empty day (month view) to set just a due date, or click a time
    # slot (week/day view) to set a due date *and* time -- like Google
    # Calendar Tasks. Dragging is disabled (see selectMinDistance above), so
    # both paths only ever resolve to a single click's worth of a payload.
    # The component keeps returning the same payload on every rerun
    # (including the 8s autorefresh) until the user clicks again, so each is
    # guarded on the last one it already handled.
    if clicked.get("dateClick"):
        dc = clicked["dateClick"]
        dc_key = dc["date"]
        if st.session_state.get("_last_cal_dateclick") != dc_key:
            st.session_state["_last_cal_dateclick"] = dc_key
            click_local = _local_dt(dc["date"])
            if dc.get("allDay"):
                add_task_dialog(prefill_due=click_local.date())
            else:
                add_task_dialog(prefill_due=click_local.date(), prefill_time=click_local.time())

    if clicked.get("select"):
        sel = clicked["select"]
        sel_key = f"{sel['start']}|{sel['end']}"
        if st.session_state.get("_last_cal_select") != sel_key:
            st.session_state["_last_cal_select"] = sel_key
            start_local = _local_dt(sel["start"])
            if sel.get("allDay"):
                add_task_dialog(prefill_due=start_local.date())
            else:
                add_task_dialog(prefill_due=start_local.date(), prefill_time=start_local.time())
