from sqlalchemy import Column, Integer, String, Float, Date, Text, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import date, datetime


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True)
    color = Column(String(7), nullable=False, default="#888888")   # hex: #RRGGBB
    icon = Column(String(32), nullable=False, default="circle")    # tabler icon name
    type = Column(String(7), nullable=False)                       # 'income' | 'expense'

    transactions = relationship("Transaction", back_populates="category", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category id={self.id} name={self.name!r} type={self.type}>"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("type IN ('income', 'expense')", name="chk_tx_type"),
        CheckConstraint("amount > 0", name="chk_tx_amount"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    type = Column(String(7), nullable=False)                       # 'income' | 'expense'
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    date = Column(Date, nullable=False, default=date.today)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction id={self.id} amount={self.amount} type={self.type} date={self.date}>"


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("limit_amount > 0", name="chk_budget_amount"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    limit_amount = Column(Float, nullable=False)
    month = Column(String(7), nullable=False)                      # формат: '2024-06'

    category = relationship("Category", back_populates="budgets")

    def __repr__(self):
        return f"<Budget id={self.id} category_id={self.category_id} month={self.month} limit={self.limit_amount}>"
