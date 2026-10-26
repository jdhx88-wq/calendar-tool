import calendar
import sys
import os

import matplotlib
matplotlib.use("Agg")  # headless — no GUI window
import matplotlib.pyplot as plt
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from calendar_print import (
    _truncate, _collect_lines, _text_style, _styled_lines,
    plot_month, MAX_ACT_LEN, WRAP_WIDTH,
)


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

def test_plot_month_too_many_events_capped_by_lines():
    # 20 short events — rendered lines must not exceed what fits in the cell
    dates = pd.to_datetime(["2026-11-03"] * 20)
    acts = [f"Event {i}" for i in range(20)]
    events = pd.DataFrame({"date": dates, "activity": acts})
    fig = plot_month(2026, 11, events)
    rendered = [t.get_text() for t in fig.axes[0].texts if t.get_text().startswith("Event")]
    # With dynamic line capping, fewer than 20 should appear
    assert len(rendered) < 20

def test_plot_month_monday_start():
    # firstweekday=0 (Monday) should not raise
    fig = plot_month(2026, 11, _empty_events(), firstweekday=0)
    assert isinstance(fig, plt.Figure)

def test_plot_month_long_activity_wraps():
    # A long activity should appear as multiple shorter lines, not one truncated line
    long_act = "Morning standup with the engineering team"   # 41 chars > WRAP_WIDTH
    events = pd.DataFrame({
        "date": pd.to_datetime(["2026-11-03"]),
        "activity": [long_act],
    })
    fig = plot_month(2026, 11, events)
    texts = [t.get_text() for t in fig.axes[0].texts]
    act_texts = [t for t in texts if any(w in t for w in ("Morning", "standup", "engineering"))]
    # Should have been split into at least 2 lines
    assert len(act_texts) >= 2
    # Each individual line must fit within WRAP_WIDTH
    assert all(len(t) <= WRAP_WIDTH for t in act_texts)

# ── _collect_lines ────────────────────────────────────────────────────────────

def test_collect_lines_single_short_act():
    assert _collect_lines(["hello"], wrap_width=20, max_lines=5) == ["hello"]

def test_collect_lines_wraps_long_act():
    lines = _collect_lines(["word " * 10], wrap_width=20, max_lines=10)
    assert len(lines) > 1
    assert all(len(l) <= 20 for l in lines)

def test_collect_lines_respects_max_lines():
    acts = ["a long activity description that wraps"] * 5
    lines = _collect_lines(acts, wrap_width=20, max_lines=3)
    assert len(lines) == 3

def test_collect_lines_empty():
    assert _collect_lines([], wrap_width=20, max_lines=5) == []


# ── _text_style ───────────────────────────────────────────────────────────────

def test_style_lane_build_green():
    assert _text_style("Lane Build D0130")["color"] == "green"

def test_style_lane_build_case_insensitive():
    assert _text_style("LANE BUILD")["color"] == "green"

def test_style_mxxx_build_blue():
    assert _text_style("M123 build start")["color"] == "blue"

def test_style_mxxx_build_case_insensitive():
    assert _text_style("m456 BUILD")["color"] == "blue"

def test_style_internal_fat_brown():
    assert _text_style("Internal FAT D0130")["color"] == "saddlebrown"

def test_style_fat_no_internal_red():
    assert _text_style("SS FAT D0130")["color"] == "red"

def test_style_fat_with_internal_not_red():
    # "internal fat" takes priority over plain fat
    assert _text_style("Internal FAT")["color"] != "red"

def test_style_out_purple_bg():
    style = _text_style("Don H OUT")
    assert style["color"] == "white"
    assert style["bbox"]["facecolor"] == "purple"

def test_style_out_word_boundary():
    # "output" should NOT trigger the out rule
    style = _text_style("Check output log")
    assert style.get("color") != "white"

def test_style_default_black():
    assert _text_style("Team lunch")["color"] == "black"

def test_style_lane_build_beats_fat():
    # "lane build" takes priority (checked first)
    assert _text_style("lane build fat check")["color"] == "green"


# ── _styled_lines ─────────────────────────────────────────────────────────────

def test_styled_lines_returns_tuples():
    result = _styled_lines(["SS FAT D0130"], wrap_width=24, max_lines=5)
    assert all(isinstance(r, tuple) and len(r) == 2 for r in result)

def test_styled_lines_color_propagates_to_wrapped_segments():
    # A long red activity that wraps should have red on every segment
    long_fat = "SS FAT " + "x " * 15        # forces wrapping
    result = _styled_lines([long_fat], wrap_width=24, max_lines=10)
    assert len(result) > 1
    assert all(style["color"] == "red" for _, style in result)

def test_styled_lines_mixed_activities():
    acts = ["Lane Build D0130", "Don H OUT", "Team review"]
    result = _styled_lines(acts, wrap_width=24, max_lines=10)
    colors = [style["color"] for _, style in result]
    assert "green" in colors
    assert "white" in colors   # purple bg / white text
    assert "black" in colors
