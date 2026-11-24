"""Month grid for the signed-in user's leave.

The last day of the month is not included. That boundary is the scheduled
B-007 defect and is corrected in a later change.
"""

import calendar
from datetime import date

from app.models import LeaveRequest


def month_days(year: int, month: int) -> list[date]:
    _weekday, days_in_month = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, days_in_month)]


def month_weeks(year: int, month: int, rows: list[LeaveRequest]) -> list[list[dict[str, object]]]:
    shown = month_days(year, month)
    if not shown:
        return []
    cells: list[date | None] = [None] * shown[0].weekday()
    cells.extend(shown)
    while len(cells) % 7:
        cells.append(None)
    weeks: list[list[dict[str, object]]] = []
    for index in range(0, len(cells), 7):
        week: list[dict[str, object]] = []
        for day in cells[index : index + 7]:
            if day is None:
                week.append({"date": "", "day": "", "requests": []})
                continue
            covering = [
                {"id": row.id, "reason": row.reason}
                for row in rows
                if row.start_date <= day <= row.end_date
            ]
            week.append({"date": day.isoformat(), "day": day.day, "requests": covering})
        weeks.append(week)
    return weeks
