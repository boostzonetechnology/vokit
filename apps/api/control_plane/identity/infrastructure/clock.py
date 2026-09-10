from __future__ import annotations

from datetime import datetime

from shared_kernel.time import utc_now


class SystemClock:
    def now(self) -> datetime:
        return utc_now()
