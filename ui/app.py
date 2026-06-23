"""
Главное окно приложения.
Боковая панель навигации + зона контента.
"""
from __future__ import annotations

import customtkinter as ctk

# ── Тема ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CLR_SIDEBAR = "#0d0d1f"
CLR_BG      = "#0f0f23"
CLR_ACCENT  = "#7F77DD"
CLR_TEXT    = "#e0e0e0"
CLR_MUTED   = "#555577"
CLR_ACTIVE  = "#1a1a3e"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Finance Tracker")
        self.geometry("1200x760")
        self.minsize(900, 600)
        self.configure(fg_color=CLR_BG)

        self._build_layout()
        self._show_tab("dashboard")

    def _build_layout(self):
        # Сайдбар
        self._sidebar = ctk.CTkFrame(self, width=200, fg_color=CLR_SIDEBAR,
                                     corner_radius=0)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Логотип / заголовок
        logo_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(24, 20))

        ctk.CTkLabel(logo_frame, text="💰", font=("", 28)).pack(side="left")
        ctk.CTkLabel(logo_frame, text="Finance\nTracker",
                     font=("", 14, "bold"), text_color=CLR_TEXT,
                     justify="left").pack(side="left", padx=8)

        # Разделитель
        ctk.CTkFrame(self._sidebar, height=1, fg_color=CLR_MUTED
                     ).pack(fill="x", padx=12, pady=(0, 12))

        # Навигационные кнопки
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("dashboard",    "📊  Дашборд"),
            ("transactions", "📋  Транзакции"),
        ]
        for tab_id, label in nav_items:
            btn = ctk.CTkButton(
                self._sidebar, text=label,
                anchor="w", height=40, corner_radius=8,
                fg_color="transparent", hover_color=CLR_ACTIVE,
                text_color=CLR_MUTED, font=("", 13),
                command=lambda t=tab_id: self._show_tab(t),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_btns[tab_id] = btn

        # Версия внизу
        ctk.CTkLabel(self._sidebar, text="v1.0  ·  SQLite",
                     font=("", 10), text_color=CLR_MUTED
                     ).pack(side="bottom", pady=12)

        # Зона контента
        self._content = ctk.CTkFrame(self, fg_color=CLR_BG, corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        # Контейнеры для вкладок (создаём заранее, переключаем видимость)
        self._tabs: dict[str, ctk.CTkFrame] = {}

    def _show_tab(self, tab_id: str):
        # Скрываем все
        for frame in self._tabs.values():
            frame.pack_forget()

        # Создаём вкладку при первом открытии (lazy init)
        if tab_id not in self._tabs:
            self._tabs[tab_id] = self._create_tab(tab_id)

        self._tabs[tab_id].pack(fill="both", expand=True)

        # Подсвечиваем активную кнопку
        for tid, btn in self._nav_btns.items():
            if tid == tab_id:
                btn.configure(fg_color=CLR_ACTIVE, text_color=CLR_TEXT)
            else:
                btn.configure(fg_color="transparent", text_color=CLR_MUTED)

    def _create_tab(self, tab_id: str) -> ctk.CTkFrame:
        if tab_id == "dashboard":
            from ui.dashboard import DashboardFrame
            return DashboardFrame(self._content)

        if tab_id == "transactions":
            from ui.transactions import TransactionsFrame
            # При добавлении/удалении транзакции — обновляем дашборд
            def on_change():
                if "dashboard" in self._tabs:
                    self._tabs["dashboard"].refresh()

            return TransactionsFrame(self._content, on_change=on_change)

        # Заглушка для будущих вкладок
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        ctk.CTkLabel(frame, text=f"Вкладка «{tab_id}» в разработке",
                     text_color=CLR_MUTED, font=("", 16)).pack(expand=True)
        return frame
