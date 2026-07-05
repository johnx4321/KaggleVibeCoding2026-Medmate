"""Optional tool for looking up real drug information via openFDA API."""

import httpx
from typing import Any, Optional


async def lookup_drug_label(drug_name: str) -> dict[str, Any]:
    """Look up a drug's label from the public openFDA API.

    This is a real external API (free, no key) with graceful fallback.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # openFDA API endpoint for drug labeling info
            url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{drug_name}"
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

            if "results" in data and data["results"]:
                result = data["results"][0]
                label_info = {
                    "drug_name": drug_name,
                    "purpose": result.get("purpose", ["Unknown"])[0] if result.get("purpose") else "Unknown",
                    "dosage_and_administration": result.get("dosage_and_administration", ["Consult label"])[0] if result.get("dosage_and_administration") else "Consult label",
                    "warnings": result.get("warnings", [])[:3],  # first 3 warnings
                    "source": "openFDA",
                }
                return {
                    "status": "success",
                    "data": label_info,
                }
    except Exception as e:
        # Graceful fallback on any error
        pass

    return {
        "status": "success",
        "data": {
            "drug_name": drug_name,
            "note": "Label data not available. Please consult your pharmacist or doctor.",
            "source": "offline",
        },
    }


# Sync wrapper for use in non-async contexts
def lookup_drug_label_sync(drug_name: str) -> dict[str, Any]:
    """Synchronous wrapper for drug label lookup."""
    try:
        with httpx.Client(timeout=5.0) as client:
            url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{drug_name}"
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()

            if "results" in data and data["results"]:
                result = data["results"][0]
                label_info = {
                    "drug_name": drug_name,
                    "purpose": result.get("purpose", ["Unknown"])[0] if result.get("purpose") else "Unknown",
                    "source": "openFDA",
                }
                return {
                    "status": "success",
                    "data": label_info,
                }
    except Exception:
        pass

    return {
        "status": "success",
        "data": {
            "drug_name": drug_name,
            "note": "Label data not available. Please consult your pharmacist or doctor.",
            "source": "offline",
        },
    }
