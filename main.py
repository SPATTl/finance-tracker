"""
Personal Finance Tracker
Точка входа. Инициализирует БД, затем запускает UI.
"""
import sys
from database.db import init_db


def main():
    # Создаём таблицы и заполняем категориями (если первый запуск)
    init_db()

    # Запускаем UI (следующий шаг разработки)
    try:
        from ui.app import App
        app = App()
        app.mainloop()
    except ImportError:
        print("UI ещё не реализован. БД и слой данных работают.")
        print("Запусти python3 -c \"from database.db import init_db; init_db()\" для проверки.")


if __name__ == "__main__":
    main()
