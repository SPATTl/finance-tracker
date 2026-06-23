from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from pathlib import Path
from .models import Base, Category

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

# Создаём папку data/ рядом с проектом, если нет
DB_PATH.parent.mkdir(exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,   # True — видеть все SQL-запросы в консоли (полезно при обучении)
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Создаёт таблицы и наполняет категориями по умолчанию."""
    Base.metadata.create_all(engine)
    with get_session() as session:
        _seed_categories(session)


@contextmanager
def get_session() -> Session:
    """Контекстный менеджер сессии — гарантирует commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── Начальные данные ───────────────────────────────────────────────────────────

DEFAULT_CATEGORIES = [
    # расходы
    {"name": "Еда",           "color": "#E07A5F", "icon": "shopping-cart",  "type": "expense"},
    {"name": "Транспорт",     "color": "#3D405B", "icon": "car",            "type": "expense"},
    {"name": "Жильё",         "color": "#81B29A", "icon": "home",           "type": "expense"},
    {"name": "Здоровье",      "color": "#F2CC8F", "icon": "heart",          "type": "expense"},
    {"name": "Развлечения",   "color": "#A8DADC", "icon": "device-gamepad", "type": "expense"},
    {"name": "Одежда",        "color": "#C77DFF", "icon": "shirt",          "type": "expense"},
    {"name": "Образование",   "color": "#457B9D", "icon": "book",           "type": "expense"},
    {"name": "Прочие расходы","color": "#6D6875", "icon": "dots",           "type": "expense"},
    # доходы
    {"name": "Зарплата",      "color": "#2DC653", "icon": "briefcase",      "type": "income"},
    {"name": "Фриланс",       "color": "#52B788", "icon": "code",           "type": "income"},
    {"name": "Подарки",       "color": "#F4A261", "icon": "gift",           "type": "income"},
    {"name": "Прочие доходы", "color": "#90BE6D", "icon": "plus-circle",    "type": "income"},
]


def _seed_categories(session: Session) -> None:
    """Добавляет категории только если таблица пуста."""
    if session.query(Category).count() == 0:
        for data in DEFAULT_CATEGORIES:
            session.add(Category(**data))
