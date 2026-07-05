"""MCP Server for medication interaction checking and drug info lookup.

Runs as a stdio-based MCP server using the official mcp SDK.
Exposes tools: check_interactions, lookup_drug_info
"""

import json
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("medmate-mcp")

# Load the interactions dataset
INTERACTIONS_PATH = Path(__file__).parent.parent / "medmate" / "data" / "interactions.json"


def load_interactions():
    """Load drug interactions from the dataset."""
    try:
        with open(INTERACTIONS_PATH) as f:
            return json.load(f)["interactions"]
    except Exception as e:
        logging.error(f"Failed to load interactions: {e}")
        return []


@mcp.tool()
def check_interactions(drugs: list[str]) -> dict:
    """Check for drug-drug interactions among a list of medications.

    Args:
        drugs: List of drug names (case-insensitive)

    Returns:
        Dictionary with interaction pairs and severity levels
    """
    interactions = load_interactions()
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
        "drugs_checked": drugs,
        "interaction_count": len(found_interactions),
        "interactions": found_interactions,
        "disclaimer": "This is for informational purposes only. Consult your pharmacist or doctor for medical advice.",
    }


@mcp.tool()
def lookup_drug_info(drug_name: str) -> dict:
    """Look up basic information about a drug.

    This is a stub that returns data from the local dataset.
    In production, this could call openFDA or other external APIs.

    Args:
        drug_name: The name of the drug

    Returns:
        Dictionary with drug information
    """
    interactions = load_interactions()
    drug_lower = drug_name.lower()

    # Find all interactions involving this drug
    related_interactions = [
        i for i in interactions
        if i["drug_a"].lower() == drug_lower or i["drug_b"].lower() == drug_lower
    ]

    return {
        "drug_name": drug_name,
        "known_interactions_count": len(related_interactions),
        "related_interactions": related_interactions,
        "disclaimer": "This is for informational purposes only. Consult your pharmacist or doctor for medical advice.",
    }


if __name__ == "__main__":
    # Run the stdio-based MCP server
    mcp.run()
