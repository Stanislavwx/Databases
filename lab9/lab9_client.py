import psycopg2
from psycopg2 import Error
from dataclasses import dataclass
from typing import List, Optional
import time

# Конфігурації для двох БД: локальної та контейнеризованої
LOCAL_DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,       # локальна БД, як у лаб. 8
    "dbname": "lab8db",
    "user": "labuser",
    "password": "labpass",
}

DOCKER_DB_CONFIG = {
    "host": "127.0.0.1",   # Docker публікує порт на localhost
    "port": 5433,          # зовнішній порт з docker-compose
    "dbname": "lab9db",
    "user": "labuser",
    "password": "labpass",
}

# Глобальна змінна для збереження активної конфігурації
ACTIVE_DB_CONFIG = LOCAL_DB_CONFIG


def get_connection(config: dict):
    """Повертає нове підключення до БД за вказаною конфігурацією."""
    try:
        conn = psycopg2.connect(**config)
        conn.autocommit = True
        return conn
    except Error as e:
        print("Помилка підключення до бази даних:", e)
        return None


def init_db(conn):
    """Створення таблиці clients, якщо вона ще не існує."""
    sql = """
    CREATE TABLE IF NOT EXISTS clients (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        age INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    print("Таблиця clients готова до роботи.")


# ----------- Active Record -----------

@dataclass
class ClientRecord:
    """
    Active Record: клас = таблиця, об'єкт = рядок.
    Вміє сам себе зберігати / видаляти у БД.
    """
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    age: Optional[int] = None
    created_at: Optional[str] = None

    @staticmethod
    def _get_conn():
        """Отримати підключення до поточної активної БД."""
        return get_connection(ACTIVE_DB_CONFIG)

    @classmethod
    def all(cls) -> List["ClientRecord"]:
        conn = cls._get_conn()
        if conn is None:
            return []
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, email, age, created_at FROM clients ORDER BY id;")
            rows = cur.fetchall()
        conn.close()
        return [cls(*row) for row in rows]

    @classmethod
    def find(cls, client_id: int) -> Optional["ClientRecord"]:
        conn = cls._get_conn()
        if conn is None:
            return None
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, age, created_at FROM clients WHERE id = %s;",
                (client_id,),
            )
            row = cur.fetchone()
        conn.close()
        if row:
            return cls(*row)
        return None

    def save(self):
        """
        Якщо self.id порожній -> INSERT.
        Якщо self.id заданий -> UPDATE.
        """
        conn = self._get_conn()
        if conn is None:
            return
        with conn.cursor() as cur:
            if self.id is None:
                cur.execute(
                    """
                    INSERT INTO clients (name, email, age)
                    VALUES (%s, %s, %s)
                    RETURNING id, created_at;
                    """,
                    (self.name, self.email, self.age),
                )
                self.id, self.created_at = cur.fetchone()
                print(f"Створено клієнта з id={self.id}")
            else:
                cur.execute(
                    """
                    UPDATE clients
                    SET name = %s, email = %s, age = %s
                    WHERE id = %s;
                    """,
                    (self.name, self.email, self.age, self.id),
                )
                print(f"Оновлено клієнта з id={self.id}")
        conn.close()

    def delete(self):
        """Видалити поточний запис з БД."""
        if self.id is None:
            print("Неможливо видалити: id не встановлено.")
            return
        conn = self._get_conn()
        if conn is None:
            return
        with conn.cursor() as cur:
            cur.execute("DELETE FROM clients WHERE id = %s;", (self.id,))
        conn.close()
        print(f"Клієнта з id={self.id} видалено.")


# ----------- DAO -----------

class ClientDAO:
    """
    DAO: окремий клас для доступу до даних.
    Тільки SQL-операції, без бізнес-логіки.
    """

    def __init__(self, conn):
        self.conn = conn

    def get_all(self) -> List[ClientRecord]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, name, email, age, created_at FROM clients ORDER BY id;")
            rows = cur.fetchall()
        return [ClientRecord(*row) for row in rows]

    def get_by_id(self, client_id: int) -> Optional[ClientRecord]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, email, age, created_at FROM clients WHERE id = %s;",
                (client_id,),
            )
            row = cur.fetchone()
        return ClientRecord(*row) if row else None

    def insert(self, client: ClientRecord) -> ClientRecord:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO clients (name, email, age)
                VALUES (%s, %s, %s)
                RETURNING id, created_at;
                """,
                (client.name, client.email, client.age),
            )
            client.id, client.created_at = cur.fetchone()
        return client

    def update(self, client: ClientRecord):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE clients
                SET name = %s, email = %s, age = %s
                WHERE id = %s;
                """,
                (client.name, client.email, client.age, client.id),
            )

    def delete(self, client_id: int):
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM clients WHERE id = %s;", (client_id,))


# ----------- Вимірювання часу запитів -----------

def measure_query_time(config: dict, label: str):
    print(f"\nВимірювання часу SELECT для: {label}")
    conn = get_connection(config)
    if conn is None:
        return
    # Переконаємось, що таблиця існує
    init_db(conn)
    start = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM clients;")
        cur.fetchall()
    duration = (time.perf_counter() - start) * 1000
    conn.close()
    print(f"Час виконання SELECT: {duration:.2f} мс")


# ----------- Меню -----------

def print_menu():
    print(
        """
=== Головне меню (Lab 9) ===
1. Показати всіх клієнтів (Active Record)
2. Додати клієнта (Active Record)
3. Оновити клієнта (Active Record)
4. Видалити клієнта (Active Record)

5. Показати всіх клієнтів (DAO)
6. Додати клієнта (DAO)
7. Оновити клієнта (DAO)
8. Видалити клієнта (DAO)

9. Виміряти час SELECT для обох БД
0. Вихід
"""
    )


def main():
    global ACTIVE_DB_CONFIG

    print("Оберіть джерело даних:")
    print("1 - Локальна БД (PostgreSQL, як у лаб. 8)")
    print("2 - Контейнеризована БД (PostgreSQL у Docker)")
    choice = input("Ваш вибір [1/2]: ").strip()

    if choice == "2":
        ACTIVE_DB_CONFIG = DOCKER_DB_CONFIG
        print("Використовується контейнеризована БД.")
    else:
        ACTIVE_DB_CONFIG = LOCAL_DB_CONFIG
        print("Використовується локальна БД.")

    # Ініціалізуємо БД (створюємо таблицю, якщо її нема)
    base_conn = get_connection(ACTIVE_DB_CONFIG)
    if base_conn is None:
        print("Неможливо продовжити роботу без підключення до БД.")
        return
    init_db(base_conn)
    base_conn.close()

    while True:
        print_menu()
        action = input("Оберіть пункт меню: ").strip()

        # --- Active Record ---
        if action == "1":
            clients = ClientRecord.all()
            for c in clients:
                print(c)

        elif action == "2":
            name = input("Ім'я: ")
            email = input("Email: ")
            age = input("Вік (ціле число): ")
            age_val = int(age) if age else None
            client = ClientRecord(name=name, email=email, age=age_val)
            client.save()

        elif action == "3":
            cid = int(input("ID клієнта для оновлення: "))
            client = ClientRecord.find(cid)
            if not client:
                print("Клієнта не знайдено.")
            else:
                print("Поточні дані:", client)
                new_name = input(f"Нове ім'я [{client.name}]: ") or client.name
                new_email = input(f"Новий email [{client.email}]: ") or client.email
                new_age_input = input(f"Новий вік [{client.age}]: ") or str(client.age)
                client.name = new_name
                client.email = new_email
                client.age = int(new_age_input) if new_age_input else None
                client.save()

        elif action == "4":
            cid = int(input("ID клієнта для видалення: "))
            client = ClientRecord.find(cid)
            if not client:
                print("Клієнта не знайдено.")
            else:
                client.delete()

        # --- DAO ---
        elif action == "5":
            conn = get_connection(ACTIVE_DB_CONFIG)
            if conn:
                dao = ClientDAO(conn)
                clients = dao.get_all()
                for c in clients:
                    print(c)
                conn.close()

        elif action == "6":
            name = input("Ім'я: ")
            email = input("Email: ")
            age = input("Вік (ціле число): ")
            age_val = int(age) if age else None
            conn = get_connection(ACTIVE_DB_CONFIG)
            if conn:
                dao = ClientDAO(conn)
                client = ClientRecord(name=name, email=email, age=age_val)
                dao.insert(client)
                conn.close()
                print(f"Створено клієнта DAO з id={client.id}")

        elif action == "7":
            cid = int(input("ID клієнта для оновлення: "))
            conn = get_connection(ACTIVE_DB_CONFIG)
            if conn:
                dao = ClientDAO(conn)
                client = dao.get_by_id(cid)
                if not client:
                    print("Клієнта не знайдено.")
                else:
                    print("Поточні дані:", client)
                    new_name = input(f"Нове ім'я [{client.name}]: ") or client.name
                    new_email = input(f"Новий email [{client.email}]: ") or client.email
                    new_age_input = input(f"Новий вік [{client.age}]: ") or str(client.age)
                    client.name = new_name
                    client.email = new_email
                    client.age = int(new_age_input) if new_age_input else None
                    dao.update(client)
                    print("Клієнта оновлено.")
                conn.close()

        elif action == "8":
            cid = int(input("ID клієнта для видалення: "))
            conn = get_connection(ACTIVE_DB_CONFIG)
            if conn:
                dao = ClientDAO(conn)
                dao.delete(cid)
                conn.close()
                print("Клієнта видалено (DAO).")

        # --- Вимірювання часу ---
        elif action == "9":
            measure_query_time(LOCAL_DB_CONFIG, "Локальна БД")
            measure_query_time(DOCKER_DB_CONFIG, "Контейнерна БД")

        elif action == "0":
            print("Вихід...")
            break
        else:
            print("Невірний вибір, спробуйте ще раз.")


if __name__ == "__main__":
    main()
