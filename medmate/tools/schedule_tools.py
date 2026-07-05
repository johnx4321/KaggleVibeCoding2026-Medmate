"""Tools for building medication schedules and reminders."""

from medmate.memory.store import MemoryStore
from datetime import datetime, timedelta
from typing import Any


def build_medication_schedule() -> dict[str, Any]:
    """Build a daily schedule from the user's medications.

    Analyzes medication frequencies and creates a timeline.
    """
    store = MemoryStore()
    meds = store.get_medications()

    if not meds:
        return {
            "status": "success",
            "schedule": [],
            "message": "No medications to schedule.",
        }

    schedule = []
    for med in meds:
        frequency = med.get("frequency", "unknown").lower()
        times = []

        # Parse frequency to suggested times
        if "once" in frequency or "daily" in frequency:
            times = ["08:00"]
        elif "twice" in frequency or "every 12" in frequency:
            times = ["08:00", "20:00"]
        elif "three times" in frequency or "every 8" in frequency:
            times = ["08:00", "14:00", "20:00"]
        elif "four times" in frequency or "every 6" in frequency:
            times = ["06:00", "12:00", "18:00", "00:00"]
        else:
            times = ["08:00"]

        for time in times:
            schedule.append({
                "time": time,
                "medication": med["name"],
                "dosage": med["dosage"],
                "reminder": f"Take {med['dosage']} of {med['name']} at {time}",
            })

    schedule.sort(key=lambda x: x["time"])
    return {
        "status": "success",
        "schedule": schedule,
        "message": f"Built schedule for {len(meds)} medication(s).",
    }


def get_next_doses(hours_ahead: int = 24) -> dict[str, Any]:
    """Get upcoming doses in the next N hours."""
    result = build_medication_schedule()
    if not result["schedule"]:
        return result

    now = datetime.now()
    cutoff = now + timedelta(hours=hours_ahead)

    upcoming = []
    for item in result["schedule"]:
        try:
            dose_time = datetime.strptime(item["time"], "%H:%M").time()
            dose_dt = datetime.combine(now.date(), dose_time)
            if dose_dt < now:
                dose_dt += timedelta(days=1)
            if now <= dose_dt <= cutoff:
                upcoming.append({
                    **item,
                    "scheduled_for": dose_dt.isoformat(),
                })
        except Exception:
            pass

    return {
        "status": "success",
        "upcoming_doses": upcoming,
        "message": f"{len(upcoming)} dose(s) in the next {hours_ahead} hours.",
    }


def export_schedule_ics() -> dict[str, Any]:
    """Export schedule as iCalendar format (stub for demo)."""
    result = build_medication_schedule()
    if not result["schedule"]:
        return {
            "status": "success",
            "ical": "",
            "message": "No medications to export.",
        }

    # Minimal iCal stub (production would use icalendar library)
    ical_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MedMate//Medication Reminders//EN",
    ]

    for item in result["schedule"]:
        ical_lines.append("BEGIN:VEVENT")
        ical_lines.append(f"SUMMARY:{item['reminder']}")
        ical_lines.append(f"DESCRIPTION:Take {item['dosage']} of {item['medication']}")
        ical_lines.append("RRULE:FREQ=DAILY")
        ical_lines.append("END:VEVENT")

    ical_lines.append("END:VCALENDAR")

    return {
        "status": "success",
        "ical": "\n".join(ical_lines),
        "message": "Schedule exported as iCalendar format.",
    }
