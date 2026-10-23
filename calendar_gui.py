import calendar
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd

from calendar_print import plot_month

MONTHS = [calendar.month_name[m] for m in range(1, 13)]
CURRENT_YEAR = 2026


class CalendarApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calendar PDF Generator")
        self.resizable(False, False)
        self._build_ui()

    # ── layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = dict(padx=8, pady=4)
        frame = ttk.Frame(self, padding=16)
        frame.grid(sticky="nsew")

        # Input file
        ttk.Label(frame, text="Events file (CSV):").grid(row=0, column=0, sticky="w", **pad)
        self.input_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.input_var, width=42).grid(row=0, column=1, **pad)
        ttk.Button(frame, text="Browse…", command=self._pick_input).grid(row=0, column=2, **pad)

        # Start month/year
        ttk.Label(frame, text="Start:").grid(row=1, column=0, sticky="w", **pad)
        self.start_month = ttk.Combobox(frame, values=MONTHS, width=12, state="readonly")
        self.start_month.current(0)
        self.start_month.grid(row=1, column=1, sticky="w", **pad)
        self.start_year = ttk.Spinbox(frame, from_=2000, to=2099, width=7)
        self.start_year.set(CURRENT_YEAR)
        self.start_year.grid(row=1, column=1, sticky="e", **pad)

        # End month/year
        ttk.Label(frame, text="End:").grid(row=2, column=0, sticky="w", **pad)
        self.end_month = ttk.Combobox(frame, values=MONTHS, width=12, state="readonly")
        self.end_month.current(11)
        self.end_month.grid(row=2, column=1, sticky="w", **pad)
        self.end_year = ttk.Spinbox(frame, from_=2000, to=2099, width=7)
        self.end_year.set(CURRENT_YEAR)
        self.end_year.grid(row=2, column=1, sticky="e", **pad)

        # Output file
        ttk.Label(frame, text="Save PDF as:").grid(row=3, column=0, sticky="w", **pad)
        self.output_var = tk.StringVar(value="calendar_output.pdf")
        ttk.Entry(frame, textvariable=self.output_var, width=42).grid(row=3, column=1, **pad)
        ttk.Button(frame, text="Browse…", command=self._pick_output).grid(row=3, column=2, **pad)

        # Week start
        ttk.Label(frame, text="Week starts on:").grid(row=4, column=0, sticky="w", **pad)
        self.week_start = ttk.Combobox(frame, values=["Sunday", "Monday"], width=10, state="readonly")
        self.week_start.current(0)
        self.week_start.grid(row=4, column=1, sticky="w", **pad)

        ttk.Separator(frame, orient="horizontal").grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=8
        )

        # Generate button + status
        self.generate_btn = ttk.Button(frame, text="Generate PDF", command=self._generate)
        self.generate_btn.grid(row=6, column=1, sticky="e", **pad)
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(frame, textvariable=self.status_var, foreground="gray").grid(
            row=7, column=0, columnspan=3, sticky="w", **pad
        )

    # ── file dialogs ──────────────────────────────────────────────────────────

    def _pick_input(self):
        path = filedialog.askopenfilename(
            title="Select events CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.input_var.set(path)

    def _pick_output(self):
        path = filedialog.asksaveasfilename(
            title="Save PDF as",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if path:
            self.output_var.set(path)

    # ── generation ────────────────────────────────────────────────────────────

    def _generate(self):
        # Validate inputs
        input_path = self.input_var.get().strip()
        output_path = self.output_var.get().strip()
        if not input_path:
            messagebox.showerror("Missing input", "Please select an events CSV file.")
            return
        if not Path(input_path).exists():
            messagebox.showerror("File not found", f"Cannot find:\n{input_path}")
            return
        if not output_path:
            messagebox.showerror("Missing output", "Please specify an output PDF path.")
            return

        try:
            start_m = MONTHS.index(self.start_month.get()) + 1
            start_y = int(self.start_year.get())
            end_m = MONTHS.index(self.end_month.get()) + 1
            end_y = int(self.end_year.get())
        except ValueError as exc:
            messagebox.showerror("Invalid date", str(exc))
            return

        if (start_y, start_m) > (end_y, end_m):
            messagebox.showerror("Invalid range", "Start must be before or equal to End.")
            return

        firstweekday = 6 if self.week_start.get() == "Sunday" else 0

        self.generate_btn.config(state="disabled")
        self.status_var.set("Generating…")
        threading.Thread(
            target=self._run,
            args=(input_path, output_path, start_y, start_m, end_y, end_m, firstweekday),
            daemon=True,
        ).start()

    def _run(self, input_path, output_path, start_y, start_m, end_y, end_m, firstweekday):
        try:
            events = pd.read_csv(input_path, parse_dates=["date"])
        except Exception as exc:
            self.after(0, lambda: self._done(f"Could not read file: {exc}", error=True))
            return

        try:
            with PdfPages(output_path) as pdf:
                y, m = start_y, start_m
                while (y, m) <= (end_y, end_m):
                    self.after(0, lambda mn=m, yr=y: self.status_var.set(
                        f"Rendering {calendar.month_name[mn]} {yr}…"
                    ))
                    fig = plot_month(y, m, events, firstweekday=firstweekday)
                    pdf.savefig(fig, bbox_inches="tight")
                    plt.close(fig)
                    m += 1
                    if m > 12:
                        m, y = 1, y + 1
        except Exception as exc:
            self.after(0, lambda: self._done(f"Error: {exc}", error=True))
            return

        self.after(0, lambda: self._done(f"Saved → {output_path}"))

    def _done(self, message, error=False):
        self.generate_btn.config(state="normal")
        self.status_var.set(message)
        if error:
            messagebox.showerror("Error", message)
        else:
            messagebox.showinfo("Done", message)


if __name__ == "__main__":
    app = CalendarApp()
    app.mainloop()
