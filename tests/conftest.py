"""Test configuration for the Galaxie integration."""

import pytest


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator for testing."""
    from unittest.mock import MagicMock

    coordinator = MagicMock()
    coordinator.data = {
        "previous_race": [],
        "next_race": [],
        "live_race": [],
        "config": {"version": "2026.02.25", "environment": "production"},
    }
    coordinator.last_update_success = True
    coordinator.async_add_listener = MagicMock()
    coordinator.backend_version = "2026.02.25"
    return coordinator
