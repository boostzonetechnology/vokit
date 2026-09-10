import os
import pymysql


def get_db_connection():
    db_host = os.getenv("TENANT_DB_HOST", "127.0.0.1")
    db_port = int(os.getenv("TENANT_DB_PORT", "3306"))

    # Prefer TENANT_DB_USER if explicitly set; otherwise use root
    db_user = os.getenv("TENANT_DB_USER") or "root"

    # Prefer TENANT_DB_PASSWORD if provided; fall back to MYSQL_ROOT_PASSWORD
    db_password = os.getenv("TENANT_DB_PASSWORD") or os.getenv("MYSQL_ROOT_PASSWORD")

    if not db_password:
        raise RuntimeError("No DB password provided (TENANT_DB_PASSWORD or MYSQL_ROOT_PASSWORD must be set)")

    conn = pymysql.connect(host=db_host, port=db_port, user=db_user, password=db_password)
    return conn


if __name__ == "__main__":
    # example usage for the CI script
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION()")
        print(cur.fetchone())
