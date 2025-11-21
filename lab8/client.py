import psycopg2
from psycopg2 import Error


# Налаштування підключення до PostgreSQL
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "lab8db",
    "user": "labuser",
    "password": "labpass",
}


def get_connection():
    """
    Створює та повертає нове підключення до БД.
    """
    return psycopg2.connect(**DB_CONFIG)


def init_db(conn):
    """
    На всяк випадок створює таблицю clients, якщо її ще немає.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    age INTEGER,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """
            )
        conn.commit()
    except Error as e:
        print("Помилка ініціалізації таблиці clients:", e)
        conn.rollback()


def list_tables(conn):
    """
    Виведення списку таблиць у схемі public.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
                """
            )
            rows = cur.fetchall()

        if not rows:
            print("У схемі public немає таблиць.")
            return

        print("\nТаблиці в схемі public:")
        for (name,) in rows:
            print(f" - {name}")

    except Error as e:
        print("Помилка при отриманні списку таблиць:")
        print(e)


def show_table_structure(conn):
    """
    Показ структури (колонок) обраної таблиці.
    """
    table = input("Введіть назву таблиці: ").strip()
    if not table:
        print("Назва таблиці не може бути порожньою.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                ORDER BY ordinal_position;
                """,
                (table,),
            )
            rows = cur.fetchall()

        if not rows:
            print(f"Таблиці '{table}' не знайдено.")
            return

        print(f"\nСтруктура таблиці {table}:")
        print(f"{'column_name':20} {'data_type':15} {'nullable':10} {'default'}")
        print("-" * 70)
        for name, data_type, nullable, default in rows:
            print(
                f"{name:20} {data_type:15} {nullable:10} {str(default)}"
            )

    except Error as e:
        print("Помилка при отриманні структури таблиці:")
        print(e)


def select_all_clients(conn):
    """
    SELECT: Вивести всі записи з таблиці clients.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, email, age, created_at
                FROM clients
                ORDER BY id;
                """
            )
            rows = cur.fetchall()

        if not rows:
            print("Таблиця clients порожня.")
            return

        print("\nКлієнти:")
        print(f"{'id':4} {'name':20} {'email':25} {'age':5} {'created_at'}")
        print("-" * 80)
        for row in rows:
            cid, name, email, age, created_at = row
            print(
                f"{cid:<4} {name:20} {email:25} {str(age):5} {created_at}"
            )

    except Error as e:
        print("Помилка при виконанні SELECT:")
        print(e)


def insert_client(conn):
    """
    INSERT: Додати нового клієнта.
    """
    name = input("Введіть ім'я: ").strip()
    email = input("Введіть email: ").strip()
    age_str = input("Введіть вік (можна порожньо): ").strip()

    if not name or not email:
        print("Ім'я та email обов'язкові.")
        return

    age = None
    if age_str:
        if not age_str.isdigit():
            print("Вік має бути цілим числом.")
            return
        age = int(age_str)

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO clients (name, email, age)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (name, email, age),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        print(f"Клієнта додано з id = {new_id}")
    except Error as e:
        print("Помилка при виконанні INSERT:")
        print("Код помилки:", e.pgcode)
        print("Текст помилки:", e.pgerror)
        conn.rollback()


def update_client(conn):
    """
    UPDATE: Оновити дані клієнта за id.
    """
    id_str = input("Введіть ID клієнта для оновлення: ").strip()
    if not id_str.isdigit():
        print("ID має бути цілим числом.")
        return
    client_id = int(id_str)

    new_email = input("Новий email (порожньо = не змінювати): ").strip()
    new_age_str = input("Новий вік (порожньо = не змінювати): ").strip()

    fields = []
    params = []

    if new_email:
        fields.append("email = %s")
        params.append(new_email)

    if new_age_str:
        if not new_age_str.isdigit():
            print("Вік має бути цілим числом.")
            return
        fields.append("age = %s")
        params.append(int(new_age_str))

    if not fields:
        print("Немає полів для оновлення.")
        return

    params.append(client_id)
    query = "UPDATE clients SET " + ", ".join(fields) + " WHERE id = %s;"

    try:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            affected = cur.rowcount
        conn.commit()

        if affected == 0:
            print("Клієнта з таким ID не знайдено.")
        else:
            print(f"Оновлено рядків: {affected}")

    except Error as e:
        print("Помилка при виконанні UPDATE:")
        print("Код помилки:", e.pgcode)
        print("Текст помилки:", e.pgerror)
        conn.rollback()


def delete_client(conn):
    """
    DELETE: Видалити клієнта за id.
    """
    id_str = input("Введіть ID клієнта для видалення: ").strip()
    if not id_str.isdigit():
        print("ID має бути цілим числом.")
        return
    client_id = int(id_str)

    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM clients WHERE id = %s;",
                (client_id,),
            )
            affected = cur.rowcount
        conn.commit()

        if affected == 0:
            print("Клієнта з таким ID не знайдено.")
        else:
            print(f"Видалено рядків: {affected}")

    except Error as e:
        print("Помилка при виконанні DELETE:")
        print("Код помилки:", e.pgcode)
        print("Текст помилки:", e.pgerror)
        conn.rollback()


def run_custom_query(conn):
    """
    Виконання довільного SQL‑запиту від користувача
    з перевіркою типу запиту та виводом деталей помилки.
    Дозволені лише SELECT / INSERT / UPDATE / DELETE.
    """
    query = input("Введіть SQL-запит: ").strip()
    if not query:
        print("Запит порожній.")
        return

    first_word = query.split()[0].lower()
    allowed = ("select", "insert", "update", "delete")

    if first_word not in allowed:
        print("Дозволені лише запити SELECT, INSERT, UPDATE, DELETE.")
        return

    try:
        with conn.cursor() as cur:
            cur.execute(query)

            if first_word == "select":
                rows = cur.fetchall()
                print(f"Отримано рядків: {len(rows)}")
                for row in rows:
                    print(row)
            else:
                affected = cur.rowcount
                conn.commit()
                print(f"Запит виконано, змінено рядків: {affected}")

    except Error as e:
        print("Помилка при виконанні запиту!")
        print("Код помилки:", e.pgcode)
        print("Текст помилки:", e.pgerror)
        conn.rollback()


def print_menu():
    """
    Вивід меню на екран.
    """
    print("\n=== Меню клієнта БД ===")
    print("1. Показати список таблиць")
    print("2. Показати структуру таблиці")
    print("3. Показати всі клієнти (SELECT)")
    print("4. Додати клієнта (INSERT)")
    print("5. Оновити клієнта (UPDATE)")
    print("6. Видалити клієнта (DELETE)")
    print("7. Виконати довільний SQL-запит")
    print("0. Вихід")


def main():
    try:
        conn = get_connection()
        print("Підключення до БД успішне.")
    except Error as e:
        print("Не вдалося підключитися до БД.")
        print(e)
        return

    # ініціалізація таблиці (на випадок, якщо її не створили вручну)
    init_db(conn)

    while True:
        print_menu()
        choice = input("Ваш вибір: ").strip()

        if choice == "1":
            list_tables(conn)
        elif choice == "2":
            show_table_structure(conn)
        elif choice == "3":
            select_all_clients(conn)
        elif choice == "4":
            insert_client(conn)
        elif choice == "5":
            update_client(conn)
        elif choice == "6":
            delete_client(conn)
        elif choice == "7":
            run_custom_query(conn)
        elif choice == "0":
            print("Вихід...")
            break
        else:
            print("Невірний пункт меню. Спробуйте ще раз.")

    conn.close()


if __name__ == "__main__":
    main()
