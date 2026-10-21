"""Validated weekday/time selections and the appendix's schedule display format."""

from collections import defaultdict
from datetime import time

DAY_CODES = {1: "M", 2: "T", 3: "W", 4: "Th", 5: "F", 6: "S", 7: "Su"}


def normalize_meetings(meetings):
    if not isinstance(meetings, (list, tuple)) or not meetings:
        raise ValueError("Select at least one meeting day and its start/end time.")
    normalized = []
    for row in meetings:
        try:
            day = int(row["weekday"])
            start = row["start_time"]
            end = row["end_time"]
            start = start if isinstance(start, time) else time.fromisoformat(start)
            end = end if isinstance(end, time) else time.fromisoformat(end)
        except (TypeError, KeyError, ValueError) as error:
            raise ValueError("Select valid meeting days and times.") from error
        if day not in DAY_CODES or start.tzinfo or end.tzinfo:
            raise ValueError("Select valid local weekdays and times.")
        if start >= end:
            raise ValueError(
                "Meeting end time must be after its start time; overnight classes need separate meetings."
            )
        if start.second or start.microsecond or end.second or end.microsecond:
            raise ValueError("Choose times to the nearest minute.")
        if any(
            r["weekday"] == day and start < r["end_time"] and r["start_time"] < end
            for r in normalized
        ):
            raise ValueError("Selected meeting times overlap on the same day.")
        normalized.append(dict(weekday=day, start_time=start, end_time=end))
    return sorted(normalized, key=lambda r: (r["weekday"], r["start_time"]))


def format_schedule(meetings):
    groups = defaultdict(list)
    for row in normalize_meetings(meetings):
        groups[(row["start_time"], row["end_time"])].append(row["weekday"])

    def clock(value):
        return f"{value.hour % 12 or 12}:{value.minute:02d}"

    return "; ".join(
        "".join(DAY_CODES[d] for d in sorted(days))
        + " "
        + clock(start)
        + "–"
        + clock(end)
        for (start, end), days in sorted(
            groups.items(), key=lambda item: (min(item[1]), item[0])
        )
    )
