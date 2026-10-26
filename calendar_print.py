import calendar
import re
import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Your activity table: one row per activity
events = pd.DataFrame({
    "date": pd.to_datetime(["2026-11-03", "2026-11-03", "2026-11-11", "2026-11-26"]),
    "activity": ["Dentist 9am", "Team review", "Veterans Day", "Thanksgiving"],
})

MAX_ACT_LEN = 20  # kept for backward compatibility / tests
MAX_ACTS_PER_DAY = 4

FONT_SIZE_ACT = 7      # activity text size in points
WRAP_WIDTH = 24        # characters per wrapped line
ACT_Y_START = 0.29    # data-unit offset from cell top where activities begin
ACT_Y_END = 0.96      # data-unit offset where activities must stop


def _truncate(text, max_len=MAX_ACT_LEN):
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def _text_style(activity):
    """Return ax.text() keyword overrides for a given activity string.

    Priority (most specific first):
      1. "lane build"           → green text
      2. M<digits> + "build"   → blue text
      3. "internal fat"         → brown text
      4. "fat" (no "internal") → red text
      5. word "out"             → white text on purple background
    """
    t = activity.lower()
    if "lane build" in t:
        return {"color": "green"}
    if re.search(r'm\d+', t) and "build" in t:
        return {"color": "blue"}
    if "internal fat" in t:
        return {"color": "saddlebrown"}
    if "fat" in t:
        return {"color": "red"}
    if re.search(r'\bout\b', t):
        return {
            "color": "white",
            "bbox": {"boxstyle": "square,pad=0.15", "facecolor": "purple", "edgecolor": "none"},
        }
    return {"color": "black"}


def _styled_lines(acts, wrap_width, max_lines):
    """Return list of (display_line, style_kwargs) pairs, capped at max_lines.

    All wrapped segments of one activity share that activity's style.
    """
    result = []
    for act in acts:
        style = _text_style(act)
        wrapped = textwrap.wrap(act, width=wrap_width) or [act[:wrap_width]]
        for seg in wrapped:
            result.append((seg, style))
            if len(result) >= max_lines:
                return result
    return result


def _collect_lines(acts, wrap_width, max_lines):
    """Wrap each activity and return a flat list of display lines, capped at max_lines."""
    lines = []
    for act in acts:
        wrapped = textwrap.wrap(act, width=wrap_width) or [act[:wrap_width]]
        lines.extend(wrapped)
        if len(lines) >= max_lines:
            break
    return lines[:max_lines]


def plot_month(year, month, events, firstweekday=6):  # 6 = weeks start Sunday
    weeks = calendar.Calendar(firstweekday).monthdayscalendar(year, month)
    m = events[(events.date.dt.year == year) & (events.date.dt.month == month)]
    by_day = m.groupby(m.date.dt.day)["activity"].apply(list)

    n_rows = len(weeks)
    fig_height = max(8.5, n_rows * 1.5)  # expand for 6-week months (6×1.5=9.0 > 8.5)
    fig, ax = plt.subplots(figsize=(11, fig_height))

    # Compute how many wrapped lines fit in the activity area of one cell.
    # Cell height in inches = fig_height / n_rows.
    # One text line in inches = font_pts / 72 * line_spacing_factor.
    cell_h_in = fig_height / n_rows
    line_h_in = FONT_SIZE_ACT / 72 * 1.35        # 1.35× for comfortable leading
    line_step = line_h_in / cell_h_in             # in data units
    max_lines = max(1, int((ACT_Y_END - ACT_Y_START) / line_step))

    # Day-of-week headers
    for c in range(7):
        ax.text(
            c + 0.5, -0.25,
            calendar.day_abbr[(firstweekday + c) % 7],
            ha="center", va="center", weight="bold",
        )

    # Separator between header row and grid
    ax.axhline(0, color="black", lw=1.5)

    for r, week in enumerate(weeks):
        for c, day in enumerate(week):
            ax.add_patch(plt.Rectangle((c, r), 1, 1, fill=False, lw=1))
            if day:
                ax.text(c + 0.05, r + 0.08, str(day), va="top", weight="bold")
                acts = by_day.get(day, [])
                for i, (line, style) in enumerate(
                    _styled_lines(acts, WRAP_WIDTH, max_lines)
                ):
                    ax.text(
                        c + 0.05, r + ACT_Y_START + i * line_step,
                        line,
                        va="top", fontsize=FONT_SIZE_ACT,
                        **style,
                    )

    ax.set_xlim(0, 7)
    ax.set_ylim(n_rows, -0.5)  # row 0 at the top
    ax.axis("off")
    ax.set_title(
        f"{calendar.month_name[month]} {year}", fontsize=18, weight="bold", pad=16
    )
    return fig


if __name__ == "__main__":
    # --- single month ---
    fig = plot_month(2026, 11, events)
    fig.savefig("november_2026.pdf", bbox_inches="tight")
    plt.close(fig)

    # --- full year as a single PDF ---
    with PdfPages("calendar_2026.pdf") as pdf:
        for month in range(1, 13):
            fig = plot_month(2026, month, events)
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
