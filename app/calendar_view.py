"""Month grid for the signed-in user's leave.

The last day of the month is not included. That boundary is the scheduled
B-007 defect and is corrected in a later change.
"""

import calendar
from datetime import date, timedelta

from app.models import LeaveRequest


def month_days(year: int, month: int) -> list[date]:
    _weekday, days_in_month = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, days_in_month)]


def week_days(anchor: date) -> list[date]:
    start = anchor - timedelta(days=anchor.weekday())
    return [start + timedelta(days=offset) for offset in range(7)]


def shift_month(year: int, month: int, steps: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + steps
    return index // 12, index % 12 + 1


def _cells(
    days: list[date | None],
    rows: list[LeaveRequest],
    today: date | None,
) -> list[dict[str, object]]:
    cells: list[dict[str, object]] = []
    for day in days:
        if day is None:
            cells.append({"date": "", "day": "", "requests": [], "today": False})
            continue
        covering = [
            {"id": row.id, "reason": row.reason}
            for row in rows
            if row.start_date <= day <= row.end_date
        ]
        cells.append(
            {
                "date": day.isoformat(),
                "day": day.day,
                "requests": covering,
                "today": today is not None and day == today,
            }
        )
    return cells


def month_weeks(
    year: int,
    month: int,
    rows: list[LeaveRequest],
    today: date | None = None,
) -> list[list[dict[str, object]]]:
    shown = month_days(year, month)
    if not shown:
        return []
    cells: list[date | None] = [None] * shown[0].weekday()
    cells.extend(shown)
    while len(cells) % 7:
        cells.append(None)
    return [_cells(cells[index : index + 7], rows, today) for index in range(0, len(cells), 7)]


def week_row(anchor: date, rows: list[LeaveRequest], today: date | None = None) -> list[dict[str, object]]:
    return _cells(list(week_days(anchor)), rows, today)


def adjacent_weeks(anchor: date) -> tuple[date, date]:
    start = week_days(anchor)[0]
    return start - timedelta(days=7), start + timedelta(days=7)
