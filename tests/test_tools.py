"""Tests for medication tools."""

import pytest
import tempfile
import os
from medmate.memory.store import MemoryStore
from medmate.tools import profile_tools, schedule_tools
from medmate.mcp_interaction_handler import check_interactions_local


@pytest.fixture
def temp_store():
    """Create a temporary store for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = os.path.join(tmpdir, "profile.json")
        # Override the default store path
        original_init = MemoryStore.__init__

        def new_init(self):
            original_init(self, store_path)

        MemoryStore.__init__ = new_init
        yield
        MemoryStore.__init__ = original_init


def test_add_medication(temp_store):
    """Test adding a medication."""
    result = profile_tools.add_medication("lisinopril", "10mg", "once daily", "blood pressure")
    assert result["status"] == "success"
    assert "Added" in result["message"]


def test_list_medications_empty(temp_store):
    """Test listing empty medications."""
    result = profile_tools.list_medications()
    assert result["status"] == "success"
    assert len(result["medications"]) == 0


def test_list_medications_with_data(temp_store):
    """Test listing medications after adding some."""
    profile_tools.add_medication("lisinopril", "10mg", "once daily")
    profile_tools.add_medication("metformin", "500mg", "twice daily")
    result = profile_tools.list_medications()
    assert result["status"] == "success"
    assert len(result["medications"]) == 2


def test_remove_medication(temp_store):
    """Test removing a medication."""
    profile_tools.add_medication("lisinopril", "10mg", "once daily")
    result = profile_tools.remove_medication("lisinopril")
    assert result["status"] == "success"
    assert "Removed" in result["message"]


def test_check_interactions():
    """Test drug interaction checking."""
    result = check_interactions_local(["ibuprofen", "lisinopril"])
    assert result["status"] == "success"
    assert result["interaction_count"] > 0
    assert len(result["interactions"]) > 0


def test_no_interactions():
    """Test when no interactions exist."""
    result = check_interactions_local(["lisinopril", "metformin"])
    assert result["status"] == "success"
    assert result["interaction_count"] == 0


def test_build_schedule(temp_store):
    """Test building a medication schedule."""
    profile_tools.add_medication("lisinopril", "10mg", "once daily")
    profile_tools.add_medication("metformin", "500mg", "twice daily")
    result = schedule_tools.build_medication_schedule()
    assert result["status"] == "success"
    assert len(result["schedule"]) > 0


def test_get_next_doses(temp_store):
    """Test getting next doses."""
    profile_tools.add_medication("lisinopril", "10mg", "once daily")
    result = schedule_tools.get_next_doses(hours_ahead=24)
    assert result["status"] == "success"


def test_add_allergy(temp_store):
    """Test adding an allergy."""
    result = profile_tools.add_allergy("penicillin")
    assert result["status"] == "success"
    assert "Added" in result["message"]


def test_list_allergies(temp_store):
    """Test listing allergies."""
    profile_tools.add_allergy("penicillin")
    profile_tools.add_allergy("sulfa")
    result = profile_tools.list_allergies()
    assert result["status"] == "success"
    assert len(result["allergies"]) == 2


def test_add_condition(temp_store):
    """Test adding a medical condition."""
    result = profile_tools.add_condition("hypertension")
    assert result["status"] == "success"
    assert "Added" in result["message"]
