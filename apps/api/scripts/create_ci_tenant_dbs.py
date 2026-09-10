from __future__ import annotations

import os

import pymysql


def _ident(value: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned or not all(ch.isalnum() or ch in {"_", "-"} for ch in cleaned):
        raise SystemExit("invalid identifier")
    return cleaned


def main() -> None:
    conn = pymysql.connect(
        host=os.environ.get("TENANT_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("TENANT_DB_PORT", "3306")),
        user=os.environ.get("MYSQL_ROOT_USER", "root"),
        password=os.environ.get("MYSQL_ROOT_PASSWORD", "vokit_ci"),
        autocommit=True,
    )
    names = (
        os.environ.get("TENANT_DB_NAME_A", "vokit_tenant_a"),
        os.environ.get("TENANT_DB_NAME_B", "vokit_tenant_b"),
    )
    user = _ident(os.environ.get("TENANT_DB_USER", "vokit"))
    with conn.cursor() as cursor:
        for raw_name in names:
            name = _ident(raw_name)
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cursor.execute(f"GRANT ALL PRIVILEGES ON `{name}`.* TO '{user}'@'%%'")
        cursor.execute("FLUSH PRIVILEGES")
    conn.close()


if __name__ == "__main__":
    main()
