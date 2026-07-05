"""Deterministic demo orchestrator - works without Gemini API key.

Routes user messages to the appropriate tools based on keywords.
"""

import logging
from typing import Optional
from medmate.memory.store import MemoryStore
from medmate.tools import profile_tools, schedule_tools
from medmate.mcp_interaction_handler import check_interactions_local

logger = logging.getLogger(__name__)


class DemoOrchestrator:
    """Routes messages to demo handlers without LLM."""

    @property
    def store(self) -> MemoryStore:
        # Fresh instance per access: profile_tools.* also open their own
        # MemoryStore per call, so a cached instance here would go stale
        # the moment any tool call writes to the underlying file.
        return MemoryStore()

    def process(self, user_input: str) -> str:
        """Process a user message and return a response."""
        user_lower = user_input.lower()

        # Profile management
        if "add" in user_lower and "medication" in user_lower:
            return self._handle_add_medication(user_input)

        if ("remove" in user_lower or "stop" in user_lower) and "medication" in user_lower:
            return self._handle_remove_medication(user_input)

        if ("list" in user_lower or "show" in user_lower) and "medication" in user_lower:
            return self._handle_list_medications()

        if "allerg" in user_lower:
            return self._handle_allergy(user_input)

        if any(kw in user_lower for kw in ["condition", "disease", "i have", "i've been diagnosed"]):
            return self._handle_condition(user_input)

        # Interaction checking
        if "interact" in user_lower or "check" in user_lower:
            return self._handle_interactions()

        # Scheduling
        if "schedule" in user_lower or "when" in user_lower and "take" in user_lower:
            return self._handle_schedule()

        if "next dose" in user_lower or "upcoming" in user_lower:
            return self._handle_next_doses()

        # Profile summary
        if "profile" in user_lower or "summary" in user_lower:
            return self._handle_profile_summary()

        # Default helpful response
        return self._handle_help(user_input)

    def _handle_add_medication(self, user_input: str) -> str:
        """Parse and add a medication from user input."""
        # Simple parsing for demo
        parts = user_input.lower().split()

        # Look for medication name after "add" or "add medication"
        med_name = None
        dosage = None
        frequency = "once daily"

        try:
            if "add" in parts:
                idx = parts.index("add")
                if idx + 2 < len(parts):
                    # Simple heuristic: next words are name, then look for dosage pattern
                    for i in range(idx + 1, len(parts)):
                        if parts[i] in ["medication", "med"]:
                            continue
                        med_name = parts[i]
                        break

            # If we couldn't extract, ask for details
            if not med_name:
                return "I can help you add a medication. Please provide: medication name, dosage (e.g., 10mg), and frequency (e.g., twice daily). Example: 'Add lisinopril 10mg twice daily for blood pressure'"

            # For demo, use a simple extraction
            result = profile_tools.add_medication(
                name=med_name,
                dosage="as specified",
                frequency=frequency,
                reason="user entered",
                notes="Demo entry",
            )

            if result["status"] == "success":
                return f"✓ {result['message']}\nYour current medications: {', '.join([m['name'] for m in self.store.get_medications()])}"
            else:
                return f"⚠️ {result['message']}"

        except Exception as e:
            logger.error(f"Error adding medication: {e}")
            return "I had trouble adding that medication. Please try again with: 'Add [medication name] [dosage] [frequency]'"

    def _handle_remove_medication(self, user_input: str) -> str:
        """Remove a medication."""
        # Extract medication name
        for med in self.store.get_medications():
            if med["name"].lower() in user_input.lower():
                result = profile_tools.remove_medication(med["name"])
                if result["status"] == "success":
                    return f"✓ {result['message']}\nRemaining medications: {', '.join([m['name'] for m in self.store.get_medications()]) or 'None'}"
                else:
                    return f"⚠️ {result['message']}"

        return "I couldn't find that medication in your profile. Current medications: " + (
            ", ".join([m["name"] for m in self.store.get_medications()]) or "None"
        )

    def _handle_list_medications(self) -> str:
        """List all medications."""
        result = profile_tools.list_medications()
        if not result["medications"]:
            return "📋 You have no medications on record. You can add medications with 'Add [medication name] [dosage]'"

        meds_text = "\n".join(
            [f"  • {m['name']} {m['dosage']} - {m['frequency']}" for m in result["medications"]]
        )
        return f"📋 Your medications:\n{meds_text}"

    def _extract_after_keyword(self, user_input: str, keywords: list[str]) -> Optional[str]:
        """Extract the phrase following the first matching keyword (e.g. 'to', 'have', 'add')."""
        words = user_input.split()
        lower_words = [w.lower().strip(".,!?") for w in words]
        for keyword in keywords:
            if keyword in lower_words:
                idx = lower_words.index(keyword)
                if idx + 1 < len(words):
                    value = " ".join(words[idx + 1 :]).strip(".,!?")
                    if value:
                        return value
        return None

    def _handle_allergy(self, user_input: str) -> str:
        """Handle allergy questions/additions."""
        lower = user_input.lower()
        is_query = any(w in lower for w in ["what", "list", "show"])

        if not is_query and "allerg" in lower:
            # Prefer "allergic/allergy TO <name>" phrasing, then fall back to "have/add <name>"
            allergy = self._extract_after_keyword(user_input, ["to", "have", "add"])
            if allergy:
                result = profile_tools.add_allergy(allergy)
                return f"✓ {result['message']}"

        result = profile_tools.list_allergies()
        if not result["allergies"]:
            return "⚠️ No allergies recorded. You can add one with 'I'm allergic to [substance]'"
        allergies_text = "\n".join([f"  • {a}" for a in result["allergies"]])
        return f"⚠️ Your allergies:\n{allergies_text}"

    def _handle_condition(self, user_input: str) -> str:
        """Handle medical condition questions."""
        lower = user_input.lower()
        is_query = any(w in lower for w in ["what", "list", "show"])

        if not is_query:
            condition = self._extract_after_keyword(user_input, ["have", "with", "add"])
            if condition:
                result = profile_tools.add_condition(condition)
                return f"✓ {result['message']}"

        conditions = self.store.get_conditions()
        if not conditions:
            return "🏥 No medical conditions recorded. Say 'I have [condition]' to record one."
        conditions_text = "\n".join([f"  • {c}" for c in conditions])
        return f"🏥 Your medical conditions:\n{conditions_text}"

    def _handle_interactions(self) -> str:
        """Check for interactions among current medications."""
        meds = self.store.get_medications()
        if len(meds) < 2:
            return "You need at least 2 medications to check for interactions. Current: " + (
                ", ".join([m["name"] for m in meds]) or "None"
            )

        med_names = [m["name"] for m in meds]
        result = check_interactions_local(med_names)

        if result["interaction_count"] == 0:
            return f"✅ No known interactions found among: {', '.join(med_names)}\n\n⚠️ Always consult your pharmacist for medical guidance."

        interactions_text = "\n".join(
            [
                f"  ⚠️ {i['drug_a']} + {i['drug_b']} (Severity: {i['severity'].upper()})\n     → {i['note']}"
                for i in result["interactions"]
            ]
        )
        return f"🚨 Found {result['interaction_count']} interaction(s):\n{interactions_text}\n\n⚠️ Please consult your pharmacist or doctor immediately."

    def _handle_schedule(self) -> str:
        """Build and show medication schedule."""
        meds = self.store.get_medications()
        if not meds:
            return "You have no medications scheduled. Add medications first with 'Add [medication name]'"

        result = schedule_tools.build_medication_schedule()
        if not result["schedule"]:
            return "No medications to schedule."

        schedule_text = "\n".join([f"  {s['time']} - {s['medication']} {s['dosage']}" for s in result["schedule"]])
        return f"📅 Your medication schedule:\n{schedule_text}\n\nSet alarms or calendar reminders for each time."

    def _handle_next_doses(self) -> str:
        """Show next doses due."""
        result = schedule_tools.get_next_doses(hours_ahead=24)
        if not result["upcoming_doses"]:
            return "No doses scheduled for the next 24 hours."

        doses_text = "\n".join(
            [f"  {d['time']} - {d['medication']} {d['dosage']}" for d in result["upcoming_doses"]]
        )
        return f"⏰ Next doses (24 hours):\n{doses_text}"

    def _handle_profile_summary(self) -> str:
        """Show full profile summary."""
        profile = self.store.get_profile()
        meds = profile.get("medications", [])
        allergies = profile.get("allergies", [])
        conditions = profile.get("conditions", [])

        summary = "📋 **Your Health Profile:**\n"
        if meds:
            summary += f"\n💊 Medications ({len(meds)}):\n"
            summary += "\n".join([f"  • {m['name']} {m['dosage']}" for m in meds])
        else:
            summary += "\n💊 No medications recorded."

        if allergies:
            summary += f"\n\n⚠️ Allergies ({len(allergies)}):\n"
            summary += "\n".join([f"  • {a}" for a in allergies])

        if conditions:
            summary += f"\n\n🏥 Conditions ({len(conditions)}):\n"
            summary += "\n".join([f"  • {c}" for c in conditions])

        return summary

    def _handle_help(self, user_input: str) -> str:
        """Handle unknown input with helpful guidance."""
        return """I'm MedMate, your personal medication organizer. I can help you:

📝 **Manage Medications:**
  • "Add [medication name] [dosage]" - Add a medication
  • "List medications" - Show all your meds
  • "Remove [medication name]" - Stop tracking a medication

⚠️ **Check Safety:**
  • "Check interactions" - Look for drug-drug interactions
  • "Show my profile" - See your full health summary

📅 **Schedule & Reminders:**
  • "Show my schedule" - Build a daily medication timeline
  • "Next doses" - See what's due in the next 24 hours

🏥 **Record Health Info:**
  • "I'm allergic to [substance]" - Record an allergy
  • "I have [condition]" - Record a medical condition

**⚠️ Important:** I'm a personal organizer, not a doctor. Always consult healthcare professionals for medical decisions."""
