"""Handler for drug interactions - uses local data as fallback."""

import json
from pathlib import Path
from typing import Any


def check_interactions_local(drugs: list[str]) -> dict[str, Any]:
    """Check for drug interactions using local dataset.

    This is a local implementation that can work without MCP server.
    Can be wrapped with McpToolset in the future for full MCP integration.
    """
    interactions_path = Path(__file__).parent / "data" / "interactions.json"

    try:
        with open(interactions_path) as f:
            data = json.load(f)
            interactions = data.get("interactions", [])
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to load interactions: {e}",
            "interactions": [],
        }

    drugs_lower = [d.lower() for d in drugs]
    found_interactions = []

    for interaction in interactions:
        drug_a = interaction["drug_a"].lower()
        drug_b = interaction["drug_b"].lower()

        # Check if both drugs are in the user's list
        if drug_a in drugs_lower and drug_b in drugs_lower:
            found_interactions.append({
                "drug_a": interaction["drug_a"],
                "drug_b": interaction["drug_b"],
                "severity": interaction["severity"],
                "note": interaction["note"],
            })

    return {
        "status": "success",
        "drugs_checked": drugs,
        "interaction_count": len(found_interactions),
        "interactions": found_interactions,
        "disclaimer": "This is for informational purposes only. Consult your pharmacist or doctor for medical advice.",
    }
