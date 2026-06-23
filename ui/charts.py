"""
Matplotlib-графики, встроенные в CustomTkinter-фреймы.
Каждый класс — самостоятельный виджет: создаёшь, вставляешь в layout, вызываешь update().
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")   # без отдельного окна — рендер в память

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk

# Тёмная тема для графиков
BG      = "#1a1a2e"
SURFACE = "#16213e"
TEXT    = "#e0e0e0"
MUTED   = "#888888"
ACCENT  = "#7F77DD"


def _apply_dark(fig, ax):
    """Применяет тёмный стиль ко всем элементам."""
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.spines["bottom"].set_color(MUTED)
    ax.spines["left"].set_color(MUTED)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.title.set_color(TEXT)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)


class PieChart(ctk.CTkFrame):
    """Круговая диаграмма расходов по категориям."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.fig, self.ax = plt.subplots(figsize=(4, 3.2), dpi=90)
        self.fig.patch.set_facecolor(BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update(self, data: list[tuple[str, float, str]]) -> None:
        """data = [(name, amount, hex_color), ...]"""
        self.ax.clear()
        self.fig.patch.set_facecolor(BG)
        self.ax.set_facecolor(BG)

        if not data:
            self.ax.text(
                0.5, 0.5, "Нет данных за этот месяц",
                ha="center", va="center",
                color=MUTED, fontsize=10,
                transform=self.ax.transAxes,
            )
            self.ax.set_axis_off()
            self.canvas.draw()
            return

        labels  = [d[0] for d in data]
        amounts = [d[1] for d in data]
        colors  = [d[2] for d in data]

        wedges, texts, autotexts = self.ax.pie(
            amounts,
            labels=None,
            colors=colors,
            autopct=lambda p: f"{p:.1f}%" if p > 5 else "",
            startangle=140,
            wedgeprops={"linewidth": 0.5, "edgecolor": BG},
            pctdistance=0.75,
        )
        for at in autotexts:
            at.set_color(TEXT)
            at.set_fontsize(8)

        # Легенда сбоку
        patches = [mpatches.Patch(color=c, label=f"{l}") for l, _, c in data[:6]]
        self.ax.legend(
            handles=patches,
            loc="center left",
            bbox_to_anchor=(0.9, 0.5),
            fontsize=8,
            frameon=False,
            labelcolor=TEXT,
        )
        self.ax.set_title("Расходы по категориям", color=TEXT, fontsize=11, pad=8)
        self.canvas.draw()


class LineChart(ctk.CTkFrame):
    """Линейный график доходов и расходов по месяцам."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.fig, self.ax = plt.subplots(figsize=(5.5, 3), dpi=90)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update(self, data) -> None:
        """data = [MonthlyPoint(month, income, expense), ...]"""
        self.ax.clear()
        _apply_dark(self.fig, self.ax)

        if not data:
            self.ax.text(0.5, 0.5, "Нет данных", ha="center", va="center",
                         color=MUTED, transform=self.ax.transAxes)
            self.canvas.draw()
            return

        months  = [d.month for d in data]
        incomes  = [d.income for d in data]
        expenses = [d.expense for d in data]

        self.ax.plot(months, incomes,  "o-", color="#2DC653", linewidth=2,
                     markersize=5, label="Доходы")
        self.ax.plot(months, expenses, "o-", color="#E07A5F", linewidth=2,
                     markersize=5, label="Расходы")

        self.ax.fill_between(months, incomes,  alpha=0.08, color="#2DC653")
        self.ax.fill_between(months, expenses, alpha=0.08, color="#E07A5F")

        self.ax.set_title("Динамика по месяцам", color=TEXT, fontsize=11, pad=8)
        self.ax.tick_params(axis="x", rotation=30)
        self.ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
        )

        legend = self.ax.legend(frameon=False, fontsize=9)
        for text in legend.get_texts():
            text.set_color(TEXT)

        self.fig.tight_layout()
        self.canvas.draw()


class MiniBarChart(ctk.CTkFrame):
    """Горизонтальные бары бюджет vs факт."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.fig, self.ax = plt.subplots(figsize=(4.5, 2.8), dpi=90)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update(self, data: list[dict]) -> None:
        """data = [{"name", "color", "limit", "spent"}, ...]"""
        self.ax.clear()
        _apply_dark(self.fig, self.ax)

        if not data:
            self.ax.text(0.5, 0.5, "Бюджеты не заданы", ha="center", va="center",
                         color=MUTED, transform=self.ax.transAxes)
            self.canvas.draw()
            return

        names  = [d["name"] for d in data]
        limits = [d["limit"] for d in data]
        spents = [d["spent"] for d in data]
        colors = [
            "#E07A5F" if d["spent"] > d["limit"] else d["color"]
            for d in data
        ]

        y = range(len(names))
        self.ax.barh(y, limits, height=0.4, color="#2a2a4a", label="Бюджет")
        self.ax.barh(y, spents, height=0.4, color=colors, alpha=0.85, label="Факт")
        self.ax.set_yticks(list(y))
        self.ax.set_yticklabels(names, color=TEXT)
        self.ax.set_title("Бюджет vs Факт", color=TEXT, fontsize=11, pad=8)

        legend = self.ax.legend(frameon=False, fontsize=8, loc="lower right")
        for t in legend.get_texts():
            t.set_color(TEXT)

        self.fig.tight_layout()
        self.canvas.draw()
