from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from memory.database import (
    complete_task,
    get_missed_tasks as db_get_missed_tasks,
    get_pending_tasks,
    mark_task_due,
    mark_task_missed,
)


@dataclass
class DueTask:
    """Represents a reminder that is due or has been missed."""

    task_id: int
    title: str
    due_at: str
    status: str


class Scheduler:
    """VYRA's reminder and task timing system."""

    def __init__(
        self,
        timezone: str = "Asia/Kolkata",
    ) -> None:
        self.timezone = timezone

    def get_current_time(self) -> datetime:
        """Return the current time in VYRA's timezone."""
        return datetime.now(
            ZoneInfo(self.timezone)
        )

    def _parse_due_time(
        self,
        due_at: str,
    ) -> datetime | None:
        """Convert stored due time text into a timezone-aware datetime."""

        try:
            due_time = datetime.strptime(
                due_at,
                "%Y-%m-%d %H:%M",
            )

            return due_time.replace(
                tzinfo=ZoneInfo(self.timezone)
            )

        except ValueError:
            return None

    def get_due_tasks(self) -> list[DueTask]:
        """
        Find reminders that are ready to be delivered.

        Scheduled/pending tasks are converted to 'due'.
        Tasks already marked 'due' are also returned so that
        the running VYRA process can deliver them.
        """

        now = self.get_current_time()
        due_tasks: list[DueTask] = []

        for task in get_pending_tasks():
            (
                task_id,
                title,
                due_at,
                status,
                created_at,
                delivered_at,
                completed_at,
                missed_at,
            ) = task

            if not due_at:
                continue

            # Already due: return it so VYRA can deliver it.
            if status == "due":
                due_tasks.append(
                    DueTask(
                        task_id=task_id,
                        title=title,
                        due_at=due_at,
                        status="due",
                    )
                )
                continue

            # Only scheduled/pending tasks can newly become due.
            if status not in {
                "scheduled",
                "pending",
            }:
                continue

            due_time = self._parse_due_time(
                due_at
            )

            if due_time is None:
                continue

            if due_time <= now:
                mark_task_due(
                    task_id
                )

                due_tasks.append(
                    DueTask(
                        task_id=task_id,
                        title=title,
                        due_at=due_at,
                        status="due",
                    )
                )

        return due_tasks
    
    def get_missed_tasks(self) -> list[DueTask]:
        """
        Find newly missed reminders and return all currently
        missed reminders.
        """

        now = self.get_current_time()

        # First, mark newly overdue scheduled/pending tasks as missed.
        for task in get_pending_tasks():
            (
                task_id,
                title,
                due_at,
                status,
                created_at,
                delivered_at,
                completed_at,
                missed_at,
            ) = task

            if not due_at:
                continue

            if status not in {
                "scheduled",
                "pending",
            }:
                continue

            due_time = self._parse_due_time(
                due_at
            )

            if due_time is None:
                continue

            if due_time < now:
                mark_task_missed(
                    task_id
                )

        # Then read all tasks that are already marked missed.
        missed_rows = db_get_missed_tasks()

        return [
            DueTask(
                task_id=row[0],
                title=row[1],
                due_at=row[2],
                status=row[3],
            )
            for row in missed_rows
        ]

    def complete(
        self,
        task_id: int,
    ) -> None:
        """Mark a task as completed."""

        complete_task(task_id)