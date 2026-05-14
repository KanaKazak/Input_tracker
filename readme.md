# Input Tracker

A background input monitor that tracks keyboard, mouse, and Xbox gamepad inputs simultaneously and saves everything to a local database. Originally built to find out how many times you click your mouse during a gaming session.

---

## Features

- **Mouse tracking** — records every click with coordinates and button
- **Keyboard tracking** — records every key press including special keys
- **Gamepad tracking** — tracks Xbox controller inputs: buttons, D-pad, analog sticks, and shoulder triggers
- **Debouncing** — analog inputs (sticks, triggers) use a cooldown to avoid flooding the database with continuous values
- **Session summary** — shows a Tkinter popup on exit with total inputs, inputs per second, and breakdown by device
- **SQLite logging** — all inputs saved with timestamps for later analysis
- **PyInstaller build** — ships as a standalone `.exe`, no Python required to run
- Press `F12` to stop and show the summary

---

## The Interesting Problem

Mouse/keyboard and gamepad use completely different input systems in Python — `pynput` for mouse/keyboard (event-driven listeners in separate threads) and `inputs` for gamepad (a polling loop). Combining them required running each in its own thread with a shared thread-safe database lock to avoid write conflicts.

Analog inputs (thumbsticks, triggers) presented a second problem: they fire continuously as long as you hold them, which would flood the database. Solved with per-axis cooldown timestamps — only one event recorded per axis per second.

---

## Known Issue

If no gamepad is connected when the program starts, gamepad tracking is disabled for the session. Hot-plugging a controller after launch is handled — it re-enables tracking automatically — but the initial check requires the controller to be plugged in.

---

## Tech Stack

| Library | Purpose |
|---|---|
| pynput | Mouse and keyboard event listeners |
| inputs | Xbox gamepad polling |
| sqlite3 | Local database for input logging |
| tkinter | Summary popup window |
| threading | Runs mouse, keyboard, and gamepad concurrently |
| playsound | Audio feedback on start and stop |

---

## Project Structure

```
├── Input_tracker.py      # Main script
├── input_data.db         # SQLite database (auto-created)
├── input_tracker.exe     # Standalone build (PyInstaller)
└── input_tracker.spec    # PyInstaller build config
```

---

## Getting Started

### Prerequisites

- Python 3.x
- Windows
- Xbox controller (optional — keyboard/mouse tracking works without one)

### Install dependencies

```bash
pip install pynput inputs playsound
```

### Run

```bash
python Input_tracker.py
```

Press `F12` to stop. A summary window will appear showing your session stats.

---

## Database Schema

All inputs are saved to `input_data.db`:

```sql
CREATE TABLE input_data (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    type      TEXT,     -- 'keyboard', 'mouse', or 'gamepad'
    detail    TEXT,     -- description of the input
    timestamp REAL      -- Unix timestamp
)
```

---

## Backlog

- [ ] Fix: require gamepad to be connected at startup
- [ ] Live dashboard showing real-time input stats
- [ ] Per-session history (currently appends to one database indefinitely)
- [ ] Heatmap of mouse click locations