"""
Все запросы к БД сосредоточены здесь.
UI ничего не знает о SQLAlchemy — только вызывает функции из этого модуля.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from sqlalchemy import text, func, extract
from sqlalchemy.orm import Session

from .models import Transaction, Category, Budget
from .db import get_session


# ── Dataclasses для передачи данных в UI ──────────────────────────────────────

@dataclass
class TransactionRow:
    id: int
    amount: float
    type: str
    category_name: str
    category_color: str
    date: date
    note: str


@dataclass
class DashboardStats:
    balance: float
    income_month: float
    expense_month: float
    top_expense_categories: list[tuple[str, float, str]]   # (name, amount, color)


@dataclass
class MonthlyPoint:
    month: str      # '2024-06'
    income: float
    expense: float


# ── Транзакции ─────────────────────────────────────────────────────────────────

def add_transaction(
    amount: float,
    type_: str,
    category_id: int,
    date_: date,
    note: str = "",
) -> Transaction:
    with get_session() as s:
        tx = Transaction(amount=amount, type=type_, category_id=category_id, date=date_, note=note)
        s.add(tx)
        s.flush()   # получаем id до commit
        s.expunge(tx)
        return tx


def delete_transaction(tx_id: int) -> None:
    with get_session() as s:
        tx = s.get(Transaction, tx_id)
        if tx:
            s.delete(tx)


def get_transactions(
    *,
    type_filter: Optional[str] = None,
    category_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[TransactionRow]:
    """Возвращает транзакции с фильтрами. JOIN с categories для имени и цвета."""
    with get_session() as s:
        q = (
            s.query(Transaction, Category)
            .join(Category, Transaction.category_id == Category.id)
            .order_by(Transaction.date.desc(), Transaction.id.desc())
        )
        if type_filter:
            q = q.filter(Transaction.type == type_filter)
        if category_id:
            q = q.filter(Transaction.category_id == category_id)
        if date_from:
            q = q.filter(Transaction.date >= date_from)
        if date_to:
            q = q.filter(Transaction.date <= date_to)

        rows = q.offset(offset).limit(limit).all()

        return [
            TransactionRow(
                id=tx.id,
                amount=tx.amount,
                type=tx.type,
                category_name=cat.name,
                category_color=cat.color,
                date=tx.date,
                note=tx.note,
            )
            for tx, cat in rows
        ]


def count_transactions(**kwargs) -> int:
    """Считает транзакции с теми же фильтрами (для пагинации)."""
    with get_session() as s:
        q = s.query(func.count(Transaction.id))
        if kwargs.get("type_filter"):
            q = q.filter(Transaction.type == kwargs["type_filter"])
        if kwargs.get("category_id"):
            q = q.filter(Transaction.category_id == kwargs["category_id"])
        if kwargs.get("date_from"):
            q = q.filter(Transaction.date >= kwargs["date_from"])
        if kwargs.get("date_to"):
            q = q.filter(Transaction.date <= kwargs["date_to"])
        return q.scalar() or 0


# ── Дашборд ────────────────────────────────────────────────────────────────────

def get_dashboard_stats(year: int, month: int) -> DashboardStats:
    """
    Пример нескольких SQL-паттернов:
    - SUM с условием через CASE
    - GROUP BY + ORDER BY + LIMIT
    - подзапрос через func
    """
    with get_session() as s:
        # Суммы за выбранный месяц одним запросом через CASE
        result = s.execute(text("""
            SELECT
                SUM(CASE WHEN type = 'income'  THEN amount ELSE 0 END) AS income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense
            FROM transactions
            WHERE strftime('%Y', date) = :year
              AND strftime('%m', date) = :month
        """), {"year": str(year), "month": f"{month:02d}"}).one()

        income_month = result.income or 0.0
        expense_month = result.expense or 0.0

        # Общий баланс за всё время
        bal = s.execute(text("""
            SELECT SUM(CASE WHEN type='income' THEN amount ELSE -amount END)
            FROM transactions
        """)).scalar() or 0.0

        # Топ категорий расходов за месяц — JOIN + GROUP BY + ORDER BY + LIMIT
        top = s.execute(text("""
            SELECT c.name, SUM(t.amount) AS total, c.color
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.type = 'expense'
              AND strftime('%Y', t.date) = :year
              AND strftime('%m', t.date) = :month
            GROUP BY c.id
            ORDER BY total DESC
            LIMIT 5
        """), {"year": str(year), "month": f"{month:02d}"}).all()

        return DashboardStats(
            balance=bal,
            income_month=income_month,
            expense_month=expense_month,
            top_expense_categories=[(r.name, r.total, r.color) for r in top],
        )


def get_monthly_totals(months: int = 6) -> list[MonthlyPoint]:
    """Данные для линейного графика — последние N месяцев."""
    with get_session() as s:
        rows = s.execute(text("""
            SELECT
                strftime('%Y-%m', date) AS month,
                SUM(CASE WHEN type = 'income'  THEN amount ELSE 0 END) AS income,
                SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense
            FROM transactions
            GROUP BY month
            ORDER BY month DESC
            LIMIT :months
        """), {"months": months}).all()

        return [MonthlyPoint(r.month, r.income, r.expense) for r in reversed(rows)]


def get_category_expenses_for_pie(year: int, month: int) -> list[tuple[str, float, str]]:
    """Данные для круговой диаграммы: (name, amount, color)."""
    with get_session() as s:
        rows = s.execute(text("""
            SELECT c.name, SUM(t.amount) AS total, c.color
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.type = 'expense'
              AND strftime('%Y', t.date) = :year
              AND strftime('%m', t.date) = :month
            GROUP BY c.id
            HAVING total > 0
            ORDER BY total DESC
        """), {"year": str(year), "month": f"{month:02d}"}).all()

        return [(r.name, r.total, r.color) for r in rows]


# ── Категории ──────────────────────────────────────────────────────────────────

def get_categories(type_: Optional[str] = None) -> list[Category]:
    with get_session() as s:
        q = s.query(Category).order_by(Category.name)
        if type_:
            q = q.filter(Category.type == type_)
        cats = q.all()
        s.expunge_all()
        return cats


# ── Бюджеты ────────────────────────────────────────────────────────────────────

def set_budget(category_id: int, month: str, limit_amount: float) -> None:
    """Upsert бюджета: обновляет если есть, создаёт если нет."""
    with get_session() as s:
        existing = (
            s.query(Budget)
            .filter_by(category_id=category_id, month=month)
            .first()
        )
        if existing:
            existing.limit_amount = limit_amount
        else:
            s.add(Budget(category_id=category_id, month=month, limit_amount=limit_amount))


def get_budget_vs_actual(year: int, month: int) -> list[dict]:
    """Сравнение бюджет vs факт по категориям."""
    month_str = f"{year}-{month:02d}"
    with get_session() as s:
        rows = s.execute(text("""
            SELECT
                c.name,
                c.color,
                b.limit_amount,
                COALESCE(SUM(t.amount), 0) AS spent
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            LEFT JOIN transactions t
                ON t.category_id = b.category_id
                AND t.type = 'expense'
                AND strftime('%Y-%m', t.date) = :month
            WHERE b.month = :month
            GROUP BY b.id
            ORDER BY spent DESC
        """), {"month": month_str}).all()

        return [
            {"name": r.name, "color": r.color, "limit": r.limit_amount, "spent": r.spent}
            for r in rows
        ]
