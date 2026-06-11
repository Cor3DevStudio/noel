"""Create database and tables (no MySQL CLI required). Works with empty password."""

import pymysql

from config.settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
from controllers.app_controller import AppController
from database.connection import init_db


def main() -> None:
    print(f"Connecting to MySQL at {DB_HOST}:{DB_PORT} as {DB_USER} (no password)...")
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD or None,
    )
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' ready.")

    init_db()
    controller = AppController()
    controller.initialize_database()
    controller.close()
    print("Tables, roles, admin user, and PhilHealth rates initialized.")
    print("Login: admin / admin123")


if __name__ == "__main__":
    main()
