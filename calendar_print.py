import calendar
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Your activity table: one row per activity
events = pd.DataFrame({
    "date": pd.to_datetime(["2026-11-03", "2026-11-03", "2026-11-11", "2026-11-26"]),
    "activity": ["Dentist 9am", "Team review", "Veterans Day", "Thanksgiving"],
})

MAX_ACT_LEN = 20  # characters before truncation
MAX_ACTS_PER_DAY = 4


def _truncate(text, max_len=MAX_ACT_LEN):
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def plot_month(year, month, events, firstweekday=6):  # 6 = weeks start Sunday
    weeks = calendar.Calendar(firstweekday).monthdayscalendar(year, month)
    m = events[(events.date.dt.year == year) & (events.date.dt.month == month)]
    by_day = m.groupby(m.date.dt.day)["activity"].apply(list)

    n_rows = len(weeks)
    fig_height = max(8.5, n_rows * 1.5)  # expand for 6-week months (6×1.5=9.0 > 8.5)
    fig, ax = plt.subplots(figsize=(11, fig_height))

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
                acts = by_day.get(day, [])[:MAX_ACTS_PER_DAY]
                for i, act in enumerate(acts):
                    ax.text(
                        c + 0.05, r + 0.30 + i * 0.15,
                        _truncate(act),
                        va="top", fontsize=8,
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
