"""Durable local worker for the first deployment profile.

The API persists jobs before this process sees them. A worker restart therefore
does not lose queued jobs. The production profile can replace this polling
loop with Celery/Redis without changing the API contract.
"""

from __future__ import annotations

import asyncio
import time

from .main import DB_LOCK, db, run_job, utc_now


def claim_one() -> tuple[str, str, str, str] | None:
    with DB_LOCK, db() as conn:
        row = conn.execute("SELECT id, user_id, project_id, kind FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
        if not row:
            return None
        changed = conn.execute("UPDATE jobs SET status='running', message=?, updated_at=? WHERE id=? AND status='queued'", ("Worker 已领取", utc_now(), row["id"])).rowcount
        conn.commit()
        return (row["id"], row["user_id"], row["project_id"], row["kind"]) if changed else None


def main() -> None:
    print("HBG worker started")
    while True:
        claimed = claim_one()
        if claimed:
            asyncio.run(run_job(*claimed))
        else:
            time.sleep(0.5)


if __name__ == "__main__":
    main()
