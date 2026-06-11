"""Dashboard view — admin-focused data analysis with KPIs and charts."""

import tkinter as tk

import customtkinter as ctk

from utils.helpers import format_currency
from utils.security import session_manager
from views.components.theme import Theme
from views.components.widgets import PanelCard, QuickActionButton, StatCard


# ---------------------------------------------------------------------------
# BarChart widget — draws a 7-day revenue bar chart on a tk.Canvas
# ---------------------------------------------------------------------------
class BarChart(ctk.CTkFrame):
    """Canvas-based bar chart for time-series data."""

    def __init__(self, master, title: str, subtitle: str = "", **kwargs):
        super().__init__(
            master,
            fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1,
            border_color=Theme.BORDER,
            **kwargs,
        )
        self._data: list[tuple[str, float]] = []
        self._bar_color = Theme.ACCENT
        self._max_val = 1.0

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 2))

        ctk.CTkLabel(
            header, text=title, font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).pack(side="left")

        self._total_label = ctk.CTkLabel(
            header, text="", font=Theme.FONT_TINY,
            text_color=Theme.TEXT_MUTED, anchor="e",
        )
        self._total_label.pack(side="right")

        if subtitle:
            ctk.CTkLabel(
                self, text=subtitle, font=Theme.FONT_TINY,
                text_color=Theme.TEXT_MUTED, anchor="w",
            ).pack(fill="x", padx=16, pady=(0, 4))

        self.canvas = tk.Canvas(
            self, bg="#FFFFFF", bd=0, highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(4, 12))
        self.canvas.bind("<Configure>", lambda _: self._draw_bars())

    def set_data(self, data: list[tuple[str, float]], color: str | None = None) -> None:
        self._data = data
        self._bar_color = color or Theme.ACCENT
        self._max_val = max((v for _, v in data), default=1) or 1
        total = sum(v for _, v in data)
        self._total_label.configure(text=f"7-day total: {format_currency(total)}")
        self._draw_bars()

    def _draw_bars(self) -> None:
        self.canvas.delete("all")
        if not self._data:
            return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 20 or h < 20:
            return

        n = len(self._data)
        pl, pr, pt, pb = 52, 10, 16, 30
        chart_w = w - pl - pr
        chart_h = h - pt - pb
        slot = chart_w / n
        bar_w = max(8, slot * 0.58)

        # Horizontal grid lines + Y-axis labels
        steps = 4
        for i in range(steps + 1):
            y = pt + chart_h - (chart_h * i / steps)
            self.canvas.create_line(pl, y, w - pr, y, fill="#E2E8F0", dash=(4, 3))
            val = self._max_val * i / steps
            if val >= 1000:
                lbl = f"₱{val / 1000:.1f}k"
            else:
                lbl = f"₱{val:.0f}"
            self.canvas.create_text(
                pl - 4, y, text=lbl, anchor="e",
                font=("Segoe UI", 8), fill="#94A3B8",
            )

        # Bars
        for idx, (label, value) in enumerate(self._data):
            xc = pl + slot * idx + slot / 2
            ratio = value / self._max_val if self._max_val > 0 else 0
            bh = ratio * chart_h
            x0, x1 = xc - bar_w / 2, xc + bar_w / 2
            y0, y1 = pt + chart_h - bh, pt + chart_h

            # Rounded-top highlight bar
            self.canvas.create_rectangle(x0 + 2, y0 + 2, x1 + 2, y1, fill="#E2E8F0", outline="")
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=self._bar_color, outline="")

            # Value label above bar
            if bh > 18:
                val_str = f"₱{value / 1000:.1f}k" if value >= 1000 else f"₱{int(value)}"
                self.canvas.create_text(
                    xc, y0 - 4, text=val_str, anchor="s",
                    font=("Segoe UI", 8, "bold"), fill=Theme.TEXT_SECONDARY,
                )

            # Day label below chart
            self.canvas.create_text(
                xc, y1 + 8, text=label, anchor="n",
                font=("Segoe UI", 8), fill=Theme.TEXT_SECONDARY,
            )


# ---------------------------------------------------------------------------
# MiniProgressRow — labeled metric with a progress bar
# ---------------------------------------------------------------------------
class MiniProgressRow(ctk.CTkFrame):
    def __init__(
        self, master, label: str, value_text: str,
        progress: float, color: str = Theme.ACCENT, **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(
            top, text=label, font=Theme.FONT_TINY,
            text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            top, text=value_text, font=("Segoe UI", 10, "bold"),
            text_color=color, anchor="e",
        ).pack(side="right")

        bar = ctk.CTkProgressBar(
            self, height=6, corner_radius=3,
            fg_color=Theme.SECONDARY, progress_color=color,
        )
        bar.pack(fill="x", pady=(3, 0))
        bar.set(min(max(progress, 0.0), 1.0))


# ---------------------------------------------------------------------------
# KPI Summary card (big number + trend sub-label)
# ---------------------------------------------------------------------------
class KPICard(ctk.CTkFrame):
    """Larger card with a main metric and a supporting descriptor."""

    def __init__(
        self, master, title: str, value: str, icon: str,
        color: str, tint: str, note: str = "", **kwargs,
    ):
        super().__init__(
            master,
            fg_color=Theme.CARD_BG,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1,
            border_color=Theme.BORDER,
            **kwargs,
        )
        # Left accent bar
        ctk.CTkFrame(self, fg_color=color, width=4, corner_radius=0).pack(
            side="left", fill="y"
        )

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        top_row = ctk.CTkFrame(body, fg_color="transparent")
        top_row.pack(fill="x")

        icon_box = ctk.CTkFrame(top_row, fg_color=tint, width=36, height=36, corner_radius=8)
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=("Segoe UI Emoji", 15)).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ctk.CTkLabel(
            top_row, text=title, font=Theme.FONT_TINY,
            text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).pack(side="left", padx=(10, 0))

        self.value_label = ctk.CTkLabel(
            body, text=value, font=("Segoe UI", 22, "bold"),
            text_color=color, anchor="w",
        )
        self.value_label.pack(fill="x", pady=(4, 0))

        if note:
            self.note_label = ctk.CTkLabel(
                body, text=note, font=Theme.FONT_TINY,
                text_color=Theme.TEXT_MUTED, anchor="w",
            )
            self.note_label.pack(fill="x")
        else:
            self.note_label = None

    def set_value(self, value: str, note: str = "") -> None:
        self.value_label.configure(text=value)
        if self.note_label and note:
            self.note_label.configure(text=note)


# ---------------------------------------------------------------------------
# Main DashboardView
# ---------------------------------------------------------------------------
class DashboardView(ctk.CTkFrame):
    def __init__(self, master, get_stats_callback, on_navigate=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.get_stats = get_stats_callback
        self.on_navigate = on_navigate
        self._kpi_cards: dict[str, KPICard] = {}
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        # 4 equal columns
        self.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="col")
        # Row weights: 0=row-A KPIs, 1=row-B KPIs, 2=charts(expand)
        self.grid_rowconfigure(2, weight=1)

        # ── Row 0: Primary KPI row (4 cards) ─────────────────────────────
        row1 = [
            ("total_patients",    "Total Patients",    "👥", Theme.ACCENT,   Theme.ACCENT_LIGHT,   "Active records"),
            ("monthly_revenue",   "Monthly Revenue",   "💰", Theme.SUCCESS,  Theme.SUCCESS_LIGHT,  "This month"),
            ("today_revenue",     "Today's Revenue",   "💵", "#0891B2",      "#ECFEFF",            "Collected today"),
            ("avg_daily_revenue", "Avg Daily Revenue", "📈", Theme.WARNING,  Theme.WARNING_LIGHT,  "Month-to-date avg"),
        ]
        for col, (key, title, icon, color, tint, note) in enumerate(row1):
            pad_left  = 0 if col == 0 else 4
            pad_right = 0 if col == 3 else 4
            card = KPICard(self, title, "—", icon, color, tint, note)
            card.grid(row=0, column=col, sticky="ew", padx=(pad_left, pad_right), pady=(0, 8))
            self._kpi_cards[key] = card

        # ── Row 1: Secondary KPI row (4 cards) ───────────────────────────
        row2 = [
            ("today_appointments",    "Today's Appointments",  "📅", Theme.PURPLE, Theme.PURPLE_LIGHT, "Scheduled & confirmed"),
            ("today_consultations",   "Today's Consultations", "🩺", "#D97706",    "#FFFBEB",          "Seen today"),
            ("monthly_consultations", "Monthly Consultations", "📋", "#059669",    "#ECFDF5",          "This month"),
            ("monthly_new_patients",  "New Patients (MTD)",    "➕", Theme.DANGER, Theme.DANGER_LIGHT, "Registered this month"),
        ]
        for col, (key, title, icon, color, tint, note) in enumerate(row2):
            pad_left  = 0 if col == 0 else 4
            pad_right = 0 if col == 3 else 4
            card = KPICard(self, title, "—", icon, color, tint, note)
            card.grid(row=1, column=col, sticky="ew", padx=(pad_left, pad_right), pady=(0, 10))
            self._kpi_cards[key] = card

        # ── Row 2: Analysis panels ────────────────────────────────────────

        # Left (span 2): Weekly Revenue bar chart
        self._revenue_chart = BarChart(self, "Weekly Revenue Trend", "Last 7 days — daily collections")
        self._revenue_chart.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0, 6))

        # Middle (span 1): Performance indicators
        perf_panel = PanelCard(self, "Performance Indicators", "Current period benchmarks")
        perf_panel.grid(row=2, column=2, sticky="nsew", padx=6)
        self._perf_body = perf_panel.body
        self._perf_body.grid_columnconfigure(0, weight=1)

        # Right (span 1): Alerts (top) + Quick Actions (bottom)
        right_col = ctk.CTkFrame(self, fg_color="transparent")
        right_col.grid(row=2, column=3, sticky="nsew", padx=(6, 0))
        right_col.grid_columnconfigure(0, weight=1)
        right_col.grid_rowconfigure(0, weight=1)
        right_col.grid_rowconfigure(1, weight=1)

        alerts_panel = PanelCard(right_col, "Stock Alerts", "")
        alerts_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
        self._alerts_body = alerts_panel.body

        actions_panel = PanelCard(right_col, "Quick Actions", "")
        actions_panel.grid(row=1, column=0, sticky="nsew")
        for text, icon, route in [
            ("Register Patient", "👤", "patients"),
            ("New Appointment",  "📅", "appointments"),
            ("Consultation",     "🩺", "consultations"),
            ("Billing",          "💳", "billing"),
        ]:
            QuickActionButton(
                actions_panel.body, text, icon, Theme.ACCENT, Theme.ACCENT_HOVER,
                command=lambda r=route: self._navigate(r),
            ).pack(fill="x", pady=2)

    # ------------------------------------------------------------------
    def _navigate(self, route: str) -> None:
        if self.on_navigate:
            self.on_navigate(route)

    # ------------------------------------------------------------------
    def refresh(self) -> None:
        stats = self.get_stats()

        monthly_rev   = float(stats.get("monthly_revenue", 0))
        avg_daily_rev = float(stats.get("avg_daily_revenue", 0))

        # ── Primary KPI cards ─────────────────────────────────────────────
        today_rev = float(stats.get("today_revenue", 0))
        self._kpi_cards["total_patients"].set_value(
            str(stats.get("total_patients", 0)), "Active records"
        )
        self._kpi_cards["monthly_revenue"].set_value(
            format_currency(monthly_rev), "This month"
        )
        self._kpi_cards["today_revenue"].set_value(
            format_currency(today_rev), "Collected today"
        )
        self._kpi_cards["avg_daily_revenue"].set_value(
            format_currency(avg_daily_rev), "Month-to-date avg"
        )

        # ── Secondary KPI cards ───────────────────────────────────────────
        self._kpi_cards["today_appointments"].set_value(
            str(stats.get("today_appointments", 0)), "Scheduled & confirmed"
        )
        self._kpi_cards["today_consultations"].set_value(
            str(stats.get("today_consultations", 0)), "Seen today"
        )
        self._kpi_cards["monthly_consultations"].set_value(
            str(stats.get("monthly_consultations", 0)), "This month"
        )
        self._kpi_cards["monthly_new_patients"].set_value(
            str(stats.get("monthly_new_patients", 0)), "Registered this month"
        )

        # ── Bar chart ─────────────────────────────────────────────────────
        weekly = stats.get("weekly_revenue", [])
        if weekly:
            self._revenue_chart.set_data(weekly, Theme.ACCENT)

        # ── Performance indicators ────────────────────────────────────────
        for w in self._perf_body.winfo_children():
            w.destroy()

        total_pts     = stats.get("total_patients", 0)
        monthly_pts   = stats.get("monthly_new_patients", 0)
        mtd_consults  = stats.get("monthly_consultations", 0)
        low_stock_cnt = stats.get("low_stock_count", 0)
        expiring_cnt  = stats.get("expiring_count", 0)

        # Revenue target ₱50 000 / month
        rev_target = 50_000
        MiniProgressRow(
            self._perf_body,
            "Monthly Revenue  (target ₱50k)",
            format_currency(monthly_rev),
            monthly_rev / rev_target,
            Theme.SUCCESS,
        ).pack(fill="x", pady=(0, 10))

        # Today vs monthly average
        daily_ratio = today_rev / max(avg_daily_rev, 1)
        MiniProgressRow(
            self._perf_body,
            "Today vs Avg Daily Revenue",
            f"{int(daily_ratio * 100)}%",
            min(daily_ratio, 1.0),
            Theme.WARNING,
        ).pack(fill="x", pady=(0, 10))

        # Patient growth (new vs total — scaled for visibility)
        pt_ratio = min((monthly_pts / max(total_pts, 1)) * 8, 1.0)
        MiniProgressRow(
            self._perf_body,
            "New Patients This Month",
            f"{monthly_pts} patients",
            pt_ratio,
            Theme.ACCENT,
        ).pack(fill="x", pady=(0, 10))

        # Monthly consultation load (target 100)
        consult_target = 100
        MiniProgressRow(
            self._perf_body,
            "Monthly Consultations  (target 100)",
            str(mtd_consults),
            min(mtd_consults / consult_target, 1.0),
            Theme.PURPLE,
        ).pack(fill="x", pady=(0, 10))

        # Inventory health
        alert_total = low_stock_cnt + expiring_cnt
        inv_health = max(0.0, 1.0 - alert_total / 20)
        inv_label = "Healthy ✓" if inv_health > 0.7 else f"{alert_total} items need attention"
        MiniProgressRow(
            self._perf_body,
            "Inventory Health",
            inv_label,
            inv_health,
            Theme.SUCCESS if inv_health > 0.7 else Theme.DANGER,
        ).pack(fill="x", pady=(0, 10))

        # ── Stock alerts ──────────────────────────────────────────────────
        for w in self._alerts_body.winfo_children():
            w.destroy()

        low_stock = stats.get("low_stock_medicines", [])[:3]
        expiring  = stats.get("expiring_medicines", [])[:2]

        if not low_stock and not expiring:
            ctk.CTkLabel(
                self._alerts_body, text="All stock levels OK ✓",
                font=Theme.FONT_TINY, text_color=Theme.SUCCESS,
            ).pack(anchor="w", pady=4)
        else:
            for med in low_stock:
                self._alert_chip(
                    f"⚠ {med.generic_name}  ({med.stock_quantity} left)", Theme.DANGER
                )
            for med in expiring:
                exp = getattr(med, "expiration_date", "—") or "—"
                self._alert_chip(f"⏰ {med.generic_name}  (exp: {exp})", Theme.WARNING)

    def _alert_chip(self, text: str, color: str) -> None:
        row = ctk.CTkFrame(self._alerts_body, fg_color=Theme.SECONDARY, corner_radius=5, height=28)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)
        ctk.CTkLabel(
            row, text=text, font=Theme.FONT_TINY, text_color=color, anchor="w",
        ).pack(fill="x", padx=8, pady=4)
