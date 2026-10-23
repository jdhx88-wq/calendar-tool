# Calendar PDF Generator

Generates print-ready monthly calendar PDFs from a CSV file of events.
Weeks start on Sunday by default. Produces letter-size (11 × 8.5 in) landscape pages.

---

## Files

| File | Purpose |
|---|---|
| `calendar_print.py` | Core rendering logic (`plot_month`, `_truncate`) |
| `calendar_gui.py` | Tkinter GUI — run this to launch the app |
| `events_sample.csv` | Sample input file |
| `test_calendar_print.py` | Pytest test suite (13 tests) |
| `requirements.txt` | Python dependencies |

---

## Requirements

- Python 3.9+
- `tkinter` (included with standard Python on Windows/macOS)

Install dependencies:

```
pip install -r requirements.txt
```

---

## Running the GUI

```
python calendar_gui.py
```

The GUI lets you:
- **Browse** to your events CSV file
- Set **Start** and **End** month/year
- Choose **Sunday or Monday** as the first day of the week
- **Browse** to pick the output PDF path
- Click **Generate PDF**

---

## Input CSV Format

The file must have exactly two columns:

| Column | Format | Example |
|---|---|---|
| `date` | `YYYY-MM-DD` (or any format pandas can parse) | `2026-11-26` |
| `activity` | Free text (≤ 20 characters recommended) | `Thanksgiving` |

Multiple events on the same day are supported (up to 4 are shown per cell).
Activity text longer than 20 characters is truncated with `…`.

**Example (`events_sample.csv`):**

```csv
date,activity
2026-11-03,Dentist 9am
2026-11-03,Team review
2026-11-11,Veterans Day
2026-11-26,Thanksgiving
2026-12-25,Christmas
```

---

## Running Without the GUI

```python
import pandas as pd
from calendar_print import plot_month
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

events = pd.read_csv("events_sample.csv", parse_dates=["date"])

with PdfPages("my_calendar.pdf") as pdf:
    for month in range(1, 13):
        fig = plot_month(2026, month, events)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)
```

---

## Running the Tests

```
pytest test_calendar_print.py -v
```

All 13 tests should pass. The suite covers `_truncate` edge cases and
`plot_month` behavior including 6-week months, event caps, and both
Sunday and Monday week starts.

---

## Limits & Notes

- **4 events max per cell** (`MAX_ACTS_PER_DAY` in `calendar_print.py`). Events beyond the limit are silently dropped.
- **6-week months** (e.g. July 2023) render at 9 in tall instead of 8.5 in.
- `tkinter` is part of the Python standard library. On some minimal Linux installs it may need `sudo apt install python3-tk`.
