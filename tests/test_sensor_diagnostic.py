"""Test the Galaxie backend version diagnostic sensor."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from homeassistant.helpers.entity import EntityCategory

from custom_components.galaxie.sensor import BackendVersionSensor


def _make_mock_coordinator(data=None, last_update_success=True):
    """Create a mock coordinator with given data."""
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.last_update_success = last_update_success
    coordinator.async_add_listener = MagicMock()
    coordinator.backend_version = "unknown"
    if data and data.get("config"):
        coordinator.backend_version = data["config"].get("version", "unknown")
    return coordinator


class TestBackendVersionSensor:
    """Test the BackendVersionSensor."""

    def test_entity_category_is_diagnostic(self):
        """Test that the sensor has diagnostic entity category."""
        coordinator = _make_mock_coordinator()
        sensor = BackendVersionSensor(coordinator)
        assert sensor._attr_entity_category == EntityCategory.DIAGNOSTIC

    def test_unique_id(self):
        """Test unique ID is set correctly."""
        coordinator = _make_mock_coordinator()
        sensor = BackendVersionSensor(coordinator)
        assert sensor._attr_unique_id == "galaxie_backend_version"

    def test_native_value_returns_version(self):
        """Test that native_value returns the backend version."""
        coordinator = _make_mock_coordinator(data={
            "config": {"version": "2026.02.25", "environment": "production"},
            "previous_race": [],
            "next_race": [],
            "live_race": [],
        })
        sensor = BackendVersionSensor(coordinator)
        assert sensor.native_value == "2026.02.25"

    def test_native_value_returns_none_when_no_config(self):
        """Test that native_value returns None when config is missing."""
        coordinator = _make_mock_coordinator(data={
            "config": None,
            "previous_race": [],
            "next_race": [],
            "live_race": [],
        })
        sensor = BackendVersionSensor(coordinator)
        assert sensor.native_value is None

    def test_native_value_returns_none_when_no_data(self):
        """Test that native_value returns None when coordinator has no data."""
        coordinator = _make_mock_coordinator(data=None)
        sensor = BackendVersionSensor(coordinator)
        assert sensor.native_value is None

    def test_extra_state_attributes(self):
        """Test extra state attributes include environment info."""
        coordinator = _make_mock_coordinator(data={
            "config": {
                "version": "2026.02.25",
                "environment": "production",
                "timezone": "US/Eastern",
                "websockets_enabled": True,
            },
            "previous_race": [],
            "next_race": [],
            "live_race": [],
        })
        sensor = BackendVersionSensor(coordinator)
        attrs = sensor.extra_state_attributes

        assert attrs is not None
        assert attrs["environment"] == "production"
        assert attrs["timezone"] == "US/Eastern"
        assert attrs["websockets_enabled"] is True

    def test_extra_state_attributes_none_when_no_config(self):
        """Test extra attributes are None when config is missing."""
        coordinator = _make_mock_coordinator(data={"config": None})
        sensor = BackendVersionSensor(coordinator)
        assert sensor.extra_state_attributes is None

    def test_available_when_config_present(self):
        """Test sensor is available when config data exists."""
        coordinator = _make_mock_coordinator(
            data={"config": {"version": "2026.02.25"}},
            last_update_success=True,
        )
        sensor = BackendVersionSensor(coordinator)
        assert sensor.available is True

    def test_unavailable_when_config_missing(self):
        """Test sensor is unavailable when config data is None."""
        coordinator = _make_mock_coordinator(
            data={"config": None},
            last_update_success=True,
        )
        sensor = BackendVersionSensor(coordinator)
        assert sensor.available is False

    def test_unavailable_when_update_failed(self):
        """Test sensor is unavailable when last update failed."""
        coordinator = _make_mock_coordinator(
            data={"config": {"version": "2026.02.25"}},
            last_update_success=False,
        )
        sensor = BackendVersionSensor(coordinator)
        assert sensor.available is False

    def test_icon(self):
        """Test the sensor icon."""
        coordinator = _make_mock_coordinator()
        sensor = BackendVersionSensor(coordinator)
        assert sensor._attr_icon == "mdi:information-outline"
