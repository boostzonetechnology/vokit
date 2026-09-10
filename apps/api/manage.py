#!/usr/bin/env python
"""Django entrypoint. Bind production HTTP to 0.0.0.0:$PORT via gunicorn, not this file."""

from __future__ import annotations

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
