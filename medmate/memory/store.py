import json
import os
from pathlib import Path
from typing import Optional, Any, Dict, List
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class Medication:
    name: str
    dosage: str
    frequency: str  # e.g., "twice daily", "every 8 hours"
    start_date: str  # ISO format
    reason: str = ""
    notes: str = ""


@dataclass
class UserProfile:
    user_id: str = "demo_user"
    name: str = "Demo Patient"
    age: int = 0
    medications: List[Dict[str, str]] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class MemoryStore:
    """Persistent profile store for user data across sessions."""

    def __init__(self, store_path: Optional[str] = None):
        if store_path is None:
            store_path = os.path.expanduser("~/.medmate/profile.json")
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._profile = self._load_or_init()

    def _load_or_init(self) -> UserProfile:
        if self.store_path.exists():
            try:
                with open(self.store_path) as f:
                    data = json.load(f)
                    return UserProfile(**data)
            except Exception:
                pass
        now = datetime.utcnow().isoformat()
        return UserProfile(created_at=now, updated_at=now)

    def _save(self):
        self._profile.updated_at = datetime.utcnow().isoformat()
        with open(self.store_path, "w") as f:
            json.dump(asdict(self._profile), f, indent=2)

    def get_profile(self) -> Dict[str, Any]:
        return asdict(self._profile)

    def add_medication(self, name: str, dosage: str, frequency: str, reason: str = "", notes: str = "") -> bool:
        med = {
            "name": name,
            "dosage": dosage,
            "frequency": frequency,
            "reason": reason,
            "notes": notes,
            "added_at": datetime.utcnow().isoformat(),
        }
        # Avoid duplicates
        if any(m["name"].lower() == name.lower() for m in self._profile.medications):
            return False
        self._profile.medications.append(med)
        self._save()
        return True

    def remove_medication(self, name: str) -> bool:
        original_len = len(self._profile.medications)
        self._profile.medications = [m for m in self._profile.medications if m["name"].lower() != name.lower()]
        if len(self._profile.medications) < original_len:
            self._save()
            return True
        return False

    def get_medications(self) -> List[Dict[str, str]]:
        return self._profile.medications

    def add_allergy(self, allergy: str) -> bool:
        if allergy.lower() in [a.lower() for a in self._profile.allergies]:
            return False
        self._profile.allergies.append(allergy)
        self._save()
        return True

    def get_allergies(self) -> List[str]:
        return self._profile.allergies

    def add_condition(self, condition: str) -> bool:
        if condition.lower() in [c.lower() for c in self._profile.conditions]:
            return False
        self._profile.conditions.append(condition)
        self._save()
        return True

    def get_conditions(self) -> List[str]:
        return self._profile.conditions

    def update_user_info(self, name: str = "", age: int = 0):
        if name:
            self._profile.name = name
        if age:
            self._profile.age = age
        self._save()
