"""Tools for managing user medication profile."""

from medmate.memory.store import MemoryStore
from typing import Any


def add_medication(name: str, dosage: str, frequency: str, reason: str = "", notes: str = "") -> dict[str, Any]:
    """Add a medication to the user's profile.

    Args:
        name: Medication name (e.g., 'lisinopril')
        dosage: Dosage amount (e.g., '10mg')
        frequency: How often (e.g., 'once daily')
        reason: Why it's prescribed
        notes: Additional notes
    """
    store = MemoryStore()
    success = store.add_medication(name, dosage, frequency, reason, notes)
    if success:
        return {
            "status": "success",
            "message": f"Added {name} {dosage} ({frequency}) to your medications.",
        }
    return {"status": "error", "message": f"{name} is already in your medications."}


def remove_medication(name: str) -> dict[str, Any]:
    """Remove a medication from the user's profile."""
    store = MemoryStore()
    success = store.remove_medication(name)
    if success:
        return {
            "status": "success",
            "message": f"Removed {name} from your medications.",
        }
    return {"status": "error", "message": f"{name} not found in your medications."}


def list_medications() -> dict[str, Any]:
    """List all medications currently in the user's profile."""
    store = MemoryStore()
    meds = store.get_medications()
    if not meds:
        return {
            "status": "success",
            "medications": [],
            "message": "You have no medications on record.",
        }
    return {
        "status": "success",
        "medications": meds,
        "message": f"You have {len(meds)} medication(s) on record.",
    }


def add_allergy(allergy: str) -> dict[str, Any]:
    """Record an allergy."""
    store = MemoryStore()
    success = store.add_allergy(allergy)
    if success:
        return {
            "status": "success",
            "message": f"Added allergy: {allergy}",
        }
    return {"status": "error", "message": f"Allergy '{allergy}' is already recorded."}


def list_allergies() -> dict[str, Any]:
    """List all recorded allergies."""
    store = MemoryStore()
    allergies = store.get_allergies()
    if not allergies:
        return {"status": "success", "allergies": [], "message": "No allergies recorded."}
    return {
        "status": "success",
        "allergies": allergies,
        "message": f"You have {len(allergies)} allergy/allergies recorded.",
    }


def add_condition(condition: str) -> dict[str, Any]:
    """Record a medical condition."""
    store = MemoryStore()
    success = store.add_condition(condition)
    if success:
        return {
            "status": "success",
            "message": f"Added condition: {condition}",
        }
    return {"status": "error", "message": f"Condition '{condition}' is already recorded."}


def get_profile() -> dict[str, Any]:
    """Get the full user profile."""
    store = MemoryStore()
    profile = store.get_profile()
    return {
        "status": "success",
        "profile": profile,
    }
