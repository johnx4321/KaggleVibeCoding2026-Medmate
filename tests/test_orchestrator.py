"""Tests for the demo orchestrator."""

import pytest
import tempfile
import os
from app.orchestrator_demo import DemoOrchestrator
from medmate.memory.store import MemoryStore


@pytest.fixture
def temp_store():
    """Create a temporary store for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = os.path.join(tmpdir, "profile.json")
        original_init = MemoryStore.__init__

        def new_init(self):
            original_init(self, store_path)

        MemoryStore.__init__ = new_init
        yield
        MemoryStore.__init__ = original_init


def test_orchestrator_help(temp_store):
    """Test orchestrator help command."""
    orch = DemoOrchestrator()
    response = orch.process("help")
    assert "manage" in response.lower() or "medication" in response.lower()


def test_orchestrator_list_medications(temp_store):
    """Test orchestrator lists empty medications."""
    orch = DemoOrchestrator()
    response = orch.process("list medications")
    assert "no medications" in response.lower()


def test_orchestrator_interactions_check(temp_store):
    """Test orchestrator checks interactions with test data."""
    orch = DemoOrchestrator()
    # Add test meds
    orch.store.add_medication("ibuprofen", "200mg", "every 8 hours")
    orch.store.add_medication("lisinopril", "10mg", "once daily")

    response = orch.process("check interactions")
    assert "found" in response.lower() or "interaction" in response.lower()


def test_orchestrator_schedule_empty(temp_store):
    """Test orchestrator shows schedule message when empty."""
    orch = DemoOrchestrator()
    response = orch.process("show schedule")
    assert "no medications" in response.lower()


def test_orchestrator_profile_summary(temp_store):
    """Test orchestrator shows profile summary."""
    orch = DemoOrchestrator()
    orch.store.add_medication("lisinopril", "10mg", "once daily")
    orch.store.add_allergy("penicillin")

    response = orch.process("show my profile")
    assert "lisinopril" in response.lower() or "medication" in response.lower()
