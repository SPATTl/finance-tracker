"""
Вкладка "Дашборд":
  - Три карточки метрик (баланс, доходы, расходы)
  - Круговая диаграмма расходов
  - Линейный график за 6 месяцев
  - Топ категорий расходов
"""
from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from database import queries
from ui.charts import PieChart, LineChart

# ── Цвета ─────────────────────────────────────────────────────────────────────
CLR_GREEN  = "#2DC653"
CLR_RED    = "#E07A5F"
CLR_PURPLE = "#7F77DD"
CLR_SURFACE= "#16213e"
CLR_TEXT   = "#e0e0e0"
CLR_MUTED  = "#888888"


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._year  = datetime.now().year
        self._month = datetime.now().month

        self._build_header()
        self._build_metric_cards()
        self._build_charts_row()
        self._build_top_categories()

        self.refresh()

    # ── Построение UI ──────────────────────────────────────────────────────────

    def _build_header(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(16, 0))

        ctk.CTkLabel(row, text="Дашборд", font=("", 22, "bold"),
                     text_color=CLR_TEXT).pack(side="left")

        # Навигация по месяцу
        nav = ctk.CTkFrame(row, fg_color="transparent")
        nav.pack(side="right")

        ctk.CTkButton(nav, text="◀", width=32, height=28,
                      command=self._prev_month,
                      fg_color=CLR_SURFACE, hover_color="#1f2f4f",
                      text_color=CLR_TEXT, corner_radius=6).pack(side="left", padx=2)

        self._month_label = ctk.CTkLabel(
            nav, text=self._month_str(), width=110,
            font=("", 13), text_color=CLR_TEXT
        )
        self._month_label.pack(side="left", padx=4)

        ctk.CTkButton(nav, text="▶", width=32, height=28,
                      command=self._next_month,
                      fg_color=CLR_SURFACE, hover_color="#1f2f4f",
                      text_color=CLR_TEXT, corner_radius=6).pack(side="left", padx=2)

    def _build_metric_cards(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=16)
        row.columnconfigure((0, 1, 2), weight=1)

        self._card_balance  = _MetricCard(row, "Баланс",       "₽0",   CLR_PURPLE)
        self._card_income   = _MetricCard(row, "Доходы",        "₽0",   CLR_GREEN)
        self._card_expense  = _MetricCard(row, "Расходы",       "₽0",   CLR_RED)

        self._card_balance.grid (row=0, column=0, padx=(0, 8), sticky="nsew")
        self._card_income.grid  (row=0, column=1, padx=4,      sticky="nsew")
        self._card_expense.grid (row=0, column=2, padx=(8, 0), sticky="nsew")

    def _build_charts_row(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        row.columnconfigure(0, weight=4)
        row.columnconfigure(1, weight=5)

        # Pie
        pie_wrap = ctk.CTkFrame(row, fg_color=CLR_SURFACE, corner_radius=12)
        pie_wrap.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self._pie = PieChart(pie_wrap)
        self._pie.pack(fill="both", expand=True, padx=8, pady=8)

        # Line
        line_wrap = ctk.CTkFrame(row, fg_color=CLR_SURFACE, corner_radius=12)
        line_wrap.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        self._line = LineChart(line_wrap)
        self._line.pack(fill="both", expand=True, padx=8, pady=8)

    def _build_top_categories(self):
        wrap = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=12)
        wrap.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(wrap, text="Топ расходов месяца",
                     font=("", 13, "bold"), text_color=CLR_TEXT
                     ).pack(anchor="w", padx=14, pady=(10, 6))

        self._top_inner = ctk.CTkFrame(wrap, fg_color="transparent")
        self._top_inner.pack(fill="x", padx=14, pady=(0, 10))

    # ── Данные ─────────────────────────────────────────────────────────────────

    def refresh(self):
        stats  = queries.get_dashboard_stats(self._year, self._month)
        pie_data = queries.get_category_expenses_for_pie(self._year, self._month)
        monthly  = queries.get_monthly_totals(6)

        # Карточки
        self._card_balance.set_value(f"₽{stats.balance:,.0f}")
        self._card_income.set_value (f"₽{stats.income_month:,.0f}")
        self._card_expense.set_value(f"₽{stats.expense_month:,.0f}")

        # Графики
        self._pie.update(pie_data)
        self._line.update(monthly)

        # Топ
        for w in self._top_inner.winfo_children():
            w.destroy()

        if not stats.top_expense_categories:
            ctk.CTkLabel(self._top_inner, text="Нет расходов в этом месяце",
                         text_color=CLR_MUTED, font=("", 12)).pack(anchor="w")
        else:
            max_amount = stats.top_expense_categories[0][1]
            for name, amount, color in stats.top_expense_categories:
                _TopRow(self._top_inner, name, amount, color, max_amount).pack(
                    fill="x", pady=2)

    # ── Навигация по месяцам ───────────────────────────────────────────────────

    def _prev_month(self):
        if self._month == 1:
            self._month, self._year = 12, self._year - 1
        else:
            self._month -= 1
        self._month_label.configure(text=self._month_str())
        self.refresh()

    def _next_month(self):
        if self._month == 12:
            self._month, self._year = 1, self._year + 1
        else:
            self._month += 1
        self._month_label.configure(text=self._month_str())
        self.refresh()

    def _month_str(self) -> str:
        months = ["Янв","Фев","Мар","Апр","Май","Июн",
                  "Июл","Авг","Сен","Окт","Ноя","Дек"]
        return f"{months[self._month - 1]} {self._year}"


# ── Вспомогательные виджеты ───────────────────────────────────────────────────

class _MetricCard(ctk.CTkFrame):
    def __init__(self, master, label: str, value: str, accent: str, **kw):
        super().__init__(master, fg_color=CLR_SURFACE, corner_radius=12, **kw)

        # Цветная полоска сверху
        bar = ctk.CTkFrame(self, fg_color=accent, height=3, corner_radius=2)
        bar.pack(fill="x", padx=0, pady=(0, 0))

        ctk.CTkLabel(self, text=label, font=("", 11),
                     text_color=CLR_MUTED).pack(anchor="w", padx=14, pady=(10, 0))

        self._val_label = ctk.CTkLabel(
            self, text=value, font=("", 22, "bold"), text_color=accent
        )
        self._val_label.pack(anchor="w", padx=14, pady=(2, 12))

    def set_value(self, text: str):
        self._val_label.configure(text=text)


class _TopRow(ctk.CTkFrame):
    """Одна строка топа: цветная точка + название + прогресс-бар + сумма."""
    def __init__(self, master, name: str, amount: float,
                 color: str, max_amount: float, **kw):
        super().__init__(master, fg_color="transparent", **kw)

        dot = ctk.CTkFrame(self, fg_color=color, width=10, height=10,
                           corner_radius=5)
        dot.pack(side="left", padx=(0, 8))
        dot.pack_propagate(False)

        ctk.CTkLabel(self, text=name, font=("", 12),
                     text_color=CLR_TEXT, width=120,
                     anchor="w").pack(side="left")

        pct = amount / max_amount if max_amount else 0
        bar_bg = ctk.CTkFrame(self, fg_color="#2a2a4a", height=6,
                              corner_radius=3, width=140)
        bar_bg.pack(side="left", padx=8)
        bar_bg.pack_propagate(False)

        bar_fill = ctk.CTkFrame(bar_bg, fg_color=color, height=6,
                                corner_radius=3,
                                width=max(4, int(140 * pct)))
        bar_fill.place(x=0, y=0)

        ctk.CTkLabel(self, text=f"₽{amount:,.0f}", font=("", 12),
                     text_color=CLR_TEXT).pack(side="right")
