"""
Вкладка "Транзакции":
  - Фильтры (тип, категория, диапазон дат)
  - Таблица с пагинацией
  - Форма добавления новой транзакции
  - Удаление выбранной строки
  - Экспорт в CSV / Excel
"""
from __future__ import annotations

from datetime import date, datetime
from tkinter import messagebox
from tkinter import filedialog
from typing import Optional, Callable

import customtkinter as ctk

from database import queries
from database.queries import TransactionRow
from utils.export import export_to_csv, export_to_excel

# ── Палитра ───────────────────────────────────────────────────────────────────
CLR_BG      = "#0f0f23"
CLR_SURFACE = "#16213e"
CLR_CARD    = "#1a1a2e"
CLR_TEXT    = "#e0e0e0"
CLR_MUTED   = "#888888"
CLR_ACCENT  = "#7F77DD"
CLR_GREEN   = "#2DC653"
CLR_RED     = "#E07A5F"
CLR_BORDER  = "#2a2a4a"

PAGE_SIZE = 15


class TransactionsFrame(ctk.CTkFrame):
    def __init__(self, master, on_change: Optional[Callable] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_change = on_change   # callback → дашборд перерисуется
        self._page = 0
        self._selected_id: Optional[int] = None

        self._build_header()
        self._build_filters()
        self._build_table()
        self._build_pagination()
        self._build_add_form()

        self.refresh()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_header(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(16, 0))

        ctk.CTkLabel(row, text="Транзакции", font=("", 22, "bold"),
                     text_color=CLR_TEXT).pack(side="left")

        # Экспорт
        exp = ctk.CTkFrame(row, fg_color="transparent")
        exp.pack(side="right")
        ctk.CTkButton(exp, text="↓ CSV", width=72, height=28,
                      command=lambda: self._export("csv"),
                      fg_color=CLR_SURFACE, hover_color="#1f2f4f",
                      text_color=CLR_TEXT, corner_radius=6).pack(side="left", padx=2)
        ctk.CTkButton(exp, text="↓ Excel", width=80, height=28,
                      command=lambda: self._export("xlsx"),
                      fg_color=CLR_SURFACE, hover_color="#1f2f4f",
                      text_color=CLR_TEXT, corner_radius=6).pack(side="left", padx=2)

    def _build_filters(self):
        wrap = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=10)
        wrap.pack(fill="x", padx=20, pady=12)

        inner = ctk.CTkFrame(wrap, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        # Тип
        ctk.CTkLabel(inner, text="Тип", text_color=CLR_MUTED,
                     font=("", 11)).grid(row=0, column=0, sticky="w", padx=(0,4))
        self._type_var = ctk.StringVar(value="Все")
        ctk.CTkOptionMenu(inner, variable=self._type_var, width=100, height=28,
                          values=["Все", "Доход", "Расход"],
                          command=self._on_filter,
                          fg_color=CLR_CARD, button_color=CLR_BORDER,
                          text_color=CLR_TEXT, dropdown_fg_color=CLR_CARD,
                          dropdown_text_color=CLR_TEXT
                          ).grid(row=0, column=1, padx=(0, 16))

        # Категория
        ctk.CTkLabel(inner, text="Категория", text_color=CLR_MUTED,
                     font=("", 11)).grid(row=0, column=2, sticky="w", padx=(0,4))
        all_cats = queries.get_categories()
        cat_names = ["Все"] + [c.name for c in all_cats]
        self._cat_map = {c.name: c.id for c in all_cats}
        self._cat_var = ctk.StringVar(value="Все")
        ctk.CTkOptionMenu(inner, variable=self._cat_var, width=140, height=28,
                          values=cat_names,
                          command=self._on_filter,
                          fg_color=CLR_CARD, button_color=CLR_BORDER,
                          text_color=CLR_TEXT, dropdown_fg_color=CLR_CARD,
                          dropdown_text_color=CLR_TEXT
                          ).grid(row=0, column=3, padx=(0, 16))

        # Дата от
        ctk.CTkLabel(inner, text="От", text_color=CLR_MUTED,
                     font=("", 11)).grid(row=0, column=4, sticky="w", padx=(0,4))
        self._date_from = ctk.CTkEntry(inner, width=100, height=28,
                                       placeholder_text="дд.мм.гггг",
                                       fg_color=CLR_CARD, border_color=CLR_BORDER,
                                       text_color=CLR_TEXT)
        self._date_from.grid(row=0, column=5, padx=(0, 8))
        self._date_from.bind("<Return>", self._on_filter)

        # Дата до
        ctk.CTkLabel(inner, text="До", text_color=CLR_MUTED,
                     font=("", 11)).grid(row=0, column=6, sticky="w", padx=(0,4))
        self._date_to = ctk.CTkEntry(inner, width=100, height=28,
                                     placeholder_text="дд.мм.гггг",
                                     fg_color=CLR_CARD, border_color=CLR_BORDER,
                                     text_color=CLR_TEXT)
        self._date_to.grid(row=0, column=7, padx=(0, 12))
        self._date_to.bind("<Return>", self._on_filter)

        ctk.CTkButton(inner, text="Сброс", width=64, height=28,
                      command=self._reset_filters,
                      fg_color=CLR_BORDER, hover_color="#3a3a6a",
                      text_color=CLR_TEXT, corner_radius=6
                      ).grid(row=0, column=8)

    def _build_table(self):
        wrap = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=10)
        wrap.pack(fill="both", expand=True, padx=20, pady=(0, 6))

        # Заголовки
        header = ctk.CTkFrame(wrap, fg_color=CLR_BORDER, corner_radius=0)
        header.pack(fill="x", padx=0)
        for col, (text, w) in enumerate(
            [("Дата", 90), ("Тип", 70), ("Сумма", 100),
             ("Категория", 150), ("Заметка", 0)]
        ):
            ctk.CTkLabel(
                header, text=text, width=w if w else 0,
                font=("", 11, "bold"), text_color=CLR_MUTED,
                anchor="w"
            ).grid(row=0, column=col, padx=(12 if col == 0 else 4, 4),
                   pady=6, sticky="w")
        header.columnconfigure(4, weight=1)

        # Скроллируемый список строк
        self._rows_frame = ctk.CTkScrollableFrame(
            wrap, fg_color="transparent", corner_radius=0
        )
        self._rows_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self._rows_frame.columnconfigure(4, weight=1)

    def _build_pagination(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=4)

        self._btn_prev = ctk.CTkButton(
            row, text="◀ Назад", width=90, height=26,
            command=self._prev_page,
            fg_color=CLR_SURFACE, hover_color="#1f2f4f",
            text_color=CLR_TEXT, corner_radius=6
        )
        self._btn_prev.pack(side="left")

        self._page_label = ctk.CTkLabel(row, text="", text_color=CLR_MUTED,
                                        font=("", 11))
        self._page_label.pack(side="left", padx=12)

        self._btn_next = ctk.CTkButton(
            row, text="Вперёд ▶", width=90, height=26,
            command=self._next_page,
            fg_color=CLR_SURFACE, hover_color="#1f2f4f",
            text_color=CLR_TEXT, corner_radius=6
        )
        self._btn_next.pack(side="left")

        # Удалить выбранную
        self._btn_delete = ctk.CTkButton(
            row, text="🗑 Удалить", width=100, height=26,
            command=self._delete_selected,
            fg_color="#3d1515", hover_color="#5a1f1f",
            text_color=CLR_RED, corner_radius=6
        )
        self._btn_delete.pack(side="right")
        self._btn_delete.configure(state="disabled")

    def _build_add_form(self):
        wrap = ctk.CTkFrame(self, fg_color=CLR_SURFACE, corner_radius=10)
        wrap.pack(fill="x", padx=20, pady=(4, 16))

        ctk.CTkLabel(wrap, text="Добавить транзакцию",
                     font=("", 13, "bold"), text_color=CLR_TEXT
                     ).pack(anchor="w", padx=14, pady=(10, 6))

        inner = ctk.CTkFrame(wrap, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=(0, 10))

        # Тип
        self._form_type = ctk.StringVar(value="Расход")
        ctk.CTkSegmentedButton(
            inner, values=["Доход", "Расход"],
            variable=self._form_type,
            command=self._on_type_change,
            width=160, height=30,
            selected_color=CLR_ACCENT, selected_hover_color="#6860c0",
            unselected_color=CLR_CARD, unselected_hover_color=CLR_BORDER,
            text_color=CLR_TEXT, fg_color=CLR_CARD,
        ).grid(row=0, column=0, padx=(0, 12))

        # Сумма
        self._form_amount = ctk.CTkEntry(
            inner, width=110, height=30, placeholder_text="Сумма",
            fg_color=CLR_CARD, border_color=CLR_BORDER, text_color=CLR_TEXT
        )
        self._form_amount.grid(row=0, column=1, padx=(0, 12))

        # Категория (зависит от типа)
        expense_cats = queries.get_categories(type_="expense")
        income_cats  = queries.get_categories(type_="income")
        self._cats_expense = {c.name: c.id for c in expense_cats}
        self._cats_income  = {c.name: c.id for c in income_cats}

        self._form_cat_var = ctk.StringVar(value=list(self._cats_expense)[0] if self._cats_expense else "")
        self._form_cat_menu = ctk.CTkOptionMenu(
            inner, variable=self._form_cat_var,
            values=list(self._cats_expense),
            width=150, height=30,
            fg_color=CLR_CARD, button_color=CLR_BORDER,
            text_color=CLR_TEXT, dropdown_fg_color=CLR_CARD,
            dropdown_text_color=CLR_TEXT,
        )
        self._form_cat_menu.grid(row=0, column=2, padx=(0, 12))

        # Дата
        self._form_date = ctk.CTkEntry(
            inner, width=110, height=30,
            placeholder_text=date.today().strftime("%d.%m.%Y"),
            fg_color=CLR_CARD, border_color=CLR_BORDER, text_color=CLR_TEXT
        )
        self._form_date.grid(row=0, column=3, padx=(0, 12))

        # Заметка
        self._form_note = ctk.CTkEntry(
            inner, width=180, height=30, placeholder_text="Заметка (необязательно)",
            fg_color=CLR_CARD, border_color=CLR_BORDER, text_color=CLR_TEXT
        )
        self._form_note.grid(row=0, column=4, padx=(0, 12))

        # Добавить
        ctk.CTkButton(
            inner, text="+ Добавить", width=100, height=30,
            command=self._add_transaction,
            fg_color=CLR_ACCENT, hover_color="#6860c0",
            text_color="#ffffff", corner_radius=6
        ).grid(row=0, column=5)

    # ── Логика ────────────────────────────────────────────────────────────────

    def refresh(self):
        self._page = 0
        self._load_page()

    def _load_page(self):
        filters = self._get_filters()
        offset  = self._page * PAGE_SIZE
        rows    = queries.get_transactions(limit=PAGE_SIZE, offset=offset, **filters)
        total   = queries.count_transactions(**filters)

        # Очищаем строки
        for w in self._rows_frame.winfo_children():
            w.destroy()
        self._selected_id = None
        self._btn_delete.configure(state="disabled")

        for i, tx in enumerate(rows):
            self._add_row(tx, i)

        # Пагинация
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        self._page_label.configure(
            text=f"Стр. {self._page + 1} из {pages}  ({total} записей)"
        )
        self._btn_prev.configure(state="normal" if self._page > 0 else "disabled")
        self._btn_next.configure(state="normal" if self._page < pages - 1 else "disabled")

    def _add_row(self, tx: TransactionRow, idx: int):
        bg = CLR_CARD if idx % 2 == 0 else "#12122a"
        row = ctk.CTkFrame(self._rows_frame, fg_color=bg, corner_radius=4, height=32)
        row.grid(row=idx, column=0, columnspan=5, sticky="ew", padx=4, pady=1)
        row.columnconfigure(4, weight=1)
        row.grid_propagate(False)

        sign  = "+" if tx.type == "income" else "−"
        color = CLR_GREEN if tx.type == "income" else CLR_RED

        vals = [
            (tx.date.strftime("%d.%m.%Y"), 90,  CLR_MUTED, "w"),
            (("Доход" if tx.type == "income" else "Расход"), 70, color, "w"),
            (f"{sign}₽{tx.amount:,.0f}", 100, color, "e"),
            (tx.category_name,            150, CLR_TEXT,  "w"),
            (tx.note or "—",              0,   CLR_MUTED, "w"),
        ]
        for col, (text, w, clr, anchor) in enumerate(vals):
            lbl = ctk.CTkLabel(row, text=text, width=w if w else 0,
                               font=("", 11), text_color=clr, anchor=anchor)
            lbl.grid(row=0, column=col,
                     padx=(12 if col == 0 else 4, 4), pady=4, sticky="w" if anchor == "w" else "e")
            lbl.bind("<Button-1>", lambda e, r=row, tid=tx.id: self._select_row(r, tid))

        row.bind("<Button-1>", lambda e, r=row, tid=tx.id: self._select_row(r, tid))

    def _select_row(self, row_widget, tx_id: int):
        # Сбрасываем предыдущий выбор
        for w in self._rows_frame.winfo_children():
            if hasattr(w, "_is_selected") and w._is_selected:
                w.configure(fg_color=w._original_bg)
                w._is_selected = False

        row_widget._original_bg = row_widget.cget("fg_color")
        row_widget.configure(fg_color="#2a2a6a")
        row_widget._is_selected = True
        self._selected_id = tx_id
        self._btn_delete.configure(state="normal")

    def _delete_selected(self):
        if not self._selected_id:
            return
        if messagebox.askyesno("Удалить?", "Удалить выбранную транзакцию?"):
            queries.delete_transaction(self._selected_id)
            self._selected_id = None
            self._btn_delete.configure(state="disabled")
            self._load_page()
            if self._on_change:
                self._on_change()

    def _add_transaction(self):
        # Сбор данных формы
        amount_str = self._form_amount.get().strip().replace(",", ".")
        type_ru    = self._form_type.get()
        cat_name   = self._form_cat_var.get()
        date_str   = self._form_date.get().strip()
        note       = self._form_note.get().strip()

        # Валидация
        try:
            amount = float(amount_str)
            assert amount > 0
        except Exception:
            messagebox.showerror("Ошибка", "Введите корректную сумму (число > 0)")
            return

        type_ = "income" if type_ru == "Доход" else "expense"
        cats  = self._cats_income if type_ == "income" else self._cats_expense
        cat_id = cats.get(cat_name)
        if not cat_id:
            messagebox.showerror("Ошибка", "Выберите категорию")
            return

        if date_str:
            try:
                tx_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            except ValueError:
                messagebox.showerror("Ошибка", "Формат даты: дд.мм.гггг")
                return
        else:
            tx_date = date.today()

        queries.add_transaction(amount, type_, cat_id, tx_date, note)

        # Очистка формы
        self._form_amount.delete(0, "end")
        self._form_date.delete(0, "end")
        self._form_note.delete(0, "end")

        self._load_page()
        if self._on_change:
            self._on_change()

    def _on_type_change(self, val):
        cats = self._cats_income if val == "Доход" else self._cats_expense
        self._form_cat_menu.configure(values=list(cats))
        if cats:
            self._form_cat_var.set(list(cats)[0])

    def _get_filters(self) -> dict:
        filters = {}
        type_ru = self._type_var.get()
        if type_ru == "Доход":
            filters["type_filter"] = "income"
        elif type_ru == "Расход":
            filters["type_filter"] = "expense"

        cat = self._cat_var.get()
        if cat != "Все":
            filters["category_id"] = self._cat_map.get(cat)

        df = self._date_from.get().strip()
        dt = self._date_to.get().strip()
        try:
            if df:
                filters["date_from"] = datetime.strptime(df, "%d.%m.%Y").date()
            if dt:
                filters["date_to"] = datetime.strptime(dt, "%d.%m.%Y").date()
        except ValueError:
            pass

        return filters

    def _on_filter(self, *_):
        self._page = 0
        self._load_page()

    def _reset_filters(self):
        self._type_var.set("Все")
        self._cat_var.set("Все")
        self._date_from.delete(0, "end")
        self._date_to.delete(0, "end")
        self._on_filter()

    def _prev_page(self):
        self._page = max(0, self._page - 1)
        self._load_page()

    def _next_page(self):
        self._page += 1
        self._load_page()

    def _export(self, fmt: str):
        filters = self._get_filters()
        ext  = "xlsx" if fmt == "xlsx" else "csv"
        path = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[(ext.upper(), f"*.{ext}")],
            initialfile=f"transactions.{ext}",
        )
        if not path:
            return
        try:
            if fmt == "xlsx":
                n = export_to_excel(path, **filters)
            else:
                n = export_to_csv(path, **filters)
            messagebox.showinfo("Готово", f"Экспортировано {n} строк → {path}")
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", str(e))
