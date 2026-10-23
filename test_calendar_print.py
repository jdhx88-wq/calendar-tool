import calendar
import sys
import os

import matplotlib
matplotlib.use("Agg")  # headless — no GUI window
import matplotlib.pyplot as plt
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from calendar_print import _truncate, plot_month, MAX_ACT_LEN, MAX_ACTS_PER_DAY


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


# ── _truncate ─────────────────────────────────────────────────────────────────

def test_truncate_short_string_unchanged():
    assert _truncate("hello") == "hello"

def test_truncate_at_exact_limit_unchanged():
    text = "x" * MAX_ACT_LEN
    assert _truncate(text) == text

def test_truncate_long_string_ends_with_ellipsis():
    long = "a" * (MAX_ACT_LEN + 5)
    result = _truncate(long)
    assert result.endswith("…")

def test_truncate_long_string_length_at_limit():
    long = "a" * (MAX_ACT_LEN + 5)
    result = _truncate(long)
    assert len(result) == MAX_ACT_LEN

def test_truncate_custom_max_len():
    assert _truncate("abcde", max_len=4) == "abc…"


# ── plot_month ────────────────────────────────────────────────────────────────

def _empty_events():
    return pd.DataFrame({"date": pd.to_datetime([]), "activity": []})

def test_plot_month_returns_figure():
    fig = plot_month(2026, 11, _empty_events())
    assert isinstance(fig, plt.Figure)

def test_plot_month_title_contains_month_and_year():
    fig = plot_month(2026, 11, _empty_events())
    assert "November" in fig.axes[0].get_title()
    assert "2026" in fig.axes[0].get_title()

def test_plot_month_no_events_does_not_raise():
    plot_month(2026, 1, _empty_events())  # January — no events

def test_plot_month_six_week_month_taller_than_five():
    # July 2023 has 6 weeks (starts on Saturday); November 2026 has 5
    fig5 = plot_month(2026, 11, _empty_events())
    fig6 = plot_month(2023, 7, _empty_events())
    assert fig6.get_size_inches()[1] > fig5.get_size_inches()[1]

def test_plot_month_events_appear_in_figure():
    events = pd.DataFrame({
        "date": pd.to_datetime(["2026-11-03"]),
        "activity": ["Dentist 9am"],
    })
    fig = plot_month(2026, 11, events)
    texts = [t.get_text() for t in fig.axes[0].texts]
    assert any("Dentist" in t for t in texts)

def test_plot_month_caps_events_at_max_per_day():
    # 6 events on the same day — only MAX_ACTS_PER_DAY should render
    dates = pd.to_datetime(["2026-11-03"] * 6)
    acts = [f"Event {i}" for i in range(6)]
    events = pd.DataFrame({"date": dates, "activity": acts})
    fig = plot_month(2026, 11, events)
    rendered = [t.get_text() for t in fig.axes[0].texts if t.get_text().startswith("Event")]
    assert len(rendered) == MAX_ACTS_PER_DAY

def test_plot_month_monday_start():
    # firstweekday=0 (Monday) should not raise
    fig = plot_month(2026, 11, _empty_events(), firstweekday=0)
    assert isinstance(fig, plt.Figure)

def test_plot_month_long_activity_is_truncated():
    long_act = "A" * (MAX_ACT_LEN + 10)
    events = pd.DataFrame({
        "date": pd.to_datetime(["2026-11-03"]),
        "activity": [long_act],
    })
    fig = plot_month(2026, 11, events)
    texts = [t.get_text() for t in fig.axes[0].texts]
    # No text on the figure should exceed MAX_ACT_LEN characters
    assert all(len(t) <= MAX_ACT_LEN for t in texts if t[0] == "A")
