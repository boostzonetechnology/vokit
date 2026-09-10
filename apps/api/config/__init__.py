"""Django project package. PyMySQL stands in for mysqlclient on Windows/Linux CI."""

from __future__ import annotations

import pymysql

pymysql.install_as_MySQLdb()
