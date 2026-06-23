# 💰 Personal Finance Tracker

Десктопное приложение для учёта личных финансов. Учебный проект на **Python + SQLite + CustomTkinter**.

## Стек

| Слой | Технология |
|------|-----------|
| GUI | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| ORM | SQLAlchemy 2.0 |
| БД | SQLite (файл `data/finance.db`) |
| Графики | Matplotlib (встроен в окно) |
| Данные | Pandas + openpyxl |

## Структура проекта

```
finance-tracker/
├── main.py                   # точка входа
├── requirements.txt
├── data/
│   └── finance.db            # создаётся автоматически
├── database/
│   ├── models.py             # SQLAlchemy модели (Category, Transaction, Budget)
│   ├── db.py                 # сессия, init_db(), начальные данные
│   └── queries.py            # весь SQL: CRUD + аналитика
├── ui/
│   ├── app.py                # главное окно (CTk)
│   ├── dashboard.py          # вкладка "Дашборд"
│   ├── transactions.py       # вкладка "История"
│   └── charts.py             # встроенные графики matplotlib
└── utils/
    └── export.py             # экспорт в CSV и Excel
```

## Запуск

```bash
pip install -r requirements.txt
python main.py
```

## Схема БД

```
categories                transactions              budgets
──────────────────        ──────────────────────   ─────────────────────
id       INTEGER PK       id          INTEGER PK   id           INTEGER PK
name     TEXT UNIQUE      amount      REAL          category_id  FK → categories
color    TEXT             type        TEXT          limit_amount REAL
icon     TEXT             category_id FK            month        TEXT  ('2024-06')
type     TEXT             date        DATE
                          note        TEXT
                          created_at  DATETIME
```