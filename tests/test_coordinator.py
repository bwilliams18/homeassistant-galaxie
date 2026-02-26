"""Test the Galaxie coordinator."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from custom_components.galaxie.coordinator import GalaxieDataCoordinator


def _make_mock_session(responses):
    """Create a mock session that returns different responses per call.

    Args:
        responses: list of (status, json_data) tuples.
    """
    mock_session = AsyncMock()
    call_count = 0

    def make_context_manager(*args, **kwargs):
        nonlocal call_count
        idx = min(call_count, len(responses) - 1)
        status, json_data = responses[idx]
        call_count += 1

        mock_response = AsyncMock()
        mock_response.status = status
        mock_response.json = AsyncMock(return_value=json_data)

        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(return_value=mock_response)
        cm.__aexit__ = AsyncMock(return_value=False)
        return cm

    mock_session.get = MagicMock(side_effect=make_context_manager)
    return mock_session


def _make_coordinator(mock_session):
    """Create a coordinator with mocked HA internals."""
    mock_hass = AsyncMock()
    with patch(
        "homeassistant.helpers.frame.report_usage",
        MagicMock(),
    ):
        coordinator = GalaxieDataCoordinator(mock_hass, mock_session)
    return coordinator


@pytest.mark.asyncio
async def test_coordinator_initialization():
    """Test coordinator initialization."""
    mock_session = AsyncMock()
    coordinator = _make_coordinator(mock_session)

    assert coordinator is not None
    assert coordinator.session == mock_session
    assert coordinator._config_data is None
    assert coordinator._last_config_fetch is None
    assert coordinator.backend_version == "unknown"


@pytest.mark.asyncio
async def test_coordinator_update_data():
    """Test coordinator data update includes config on first call."""
    mock_session = _make_mock_session([
        (200, [{"id": 1, "name": "Test Race"}]),  # previous_race
        (200, [{"id": 2, "name": "Next Race"}]),  # next_race
        (200, []),  # live_race (empty)
        (200, {"version": "2026.02.25", "environment": "production"}),  # config
    ])

    coordinator = _make_coordinator(mock_session)

    data = await coordinator._async_update_data()

    assert data is not None
    assert "previous_race" in data
    assert "next_race" in data
    assert "live_race" in data
    assert "config" in data
    assert data["config"]["version"] == "2026.02.25"
    assert coordinator.backend_version == "2026.02.25"


@pytest.mark.asyncio
async def test_coordinator_config_cached():
    """Test that config is cached and not re-fetched on subsequent calls."""
    mock_session = _make_mock_session([
        # First call: 4 endpoints (including config)
        (200, []),  # previous_race
        (200, []),  # next_race
        (200, []),  # live_race
        (200, {"version": "2026.02.25", "environment": "production"}),  # config
        # Second call: only 3 endpoints (config cached)
        (200, []),  # previous_race
        (200, []),  # next_race
        (200, []),  # live_race
    ])

    coordinator = _make_coordinator(mock_session)

    # First update: should fetch config
    data1 = await coordinator._async_update_data()
    assert data1["config"]["version"] == "2026.02.25"
    first_call_count = mock_session.get.call_count
    assert first_call_count == 4  # 3 race endpoints + config

    # Second update: should NOT fetch config (cached)
    data2 = await coordinator._async_update_data()
    assert data2["config"]["version"] == "2026.02.25"
    assert mock_session.get.call_count == 7  # 4 + 3 (no config re-fetch)


@pytest.mark.asyncio
async def test_coordinator_config_refetch_after_expiry():
    """Test that config is re-fetched after the cache interval expires."""
    mock_session = _make_mock_session([
        # First call
        (200, []),  # previous_race
        (200, []),  # next_race
        (200, []),  # live_race
        (200, {"version": "2026.02.25", "environment": "production"}),  # config
        # Second call (after expiry): 4 endpoints again
        (200, []),  # previous_race
        (200, []),  # next_race
        (200, []),  # live_race
        (200, {"version": "2026.02.26", "environment": "production"}),  # config (new)
    ])

    coordinator = _make_coordinator(mock_session)

    # First update
    await coordinator._async_update_data()
    assert coordinator.backend_version == "2026.02.25"

    # Simulate cache expiry by backdating the timestamp
    coordinator._last_config_fetch = datetime.now() - timedelta(hours=2)

    # Second update: should re-fetch config
    data2 = await coordinator._async_update_data()
    assert data2["config"]["version"] == "2026.02.26"
    assert coordinator.backend_version == "2026.02.26"
    assert mock_session.get.call_count == 8  # 4 + 4


@pytest.mark.asyncio
async def test_coordinator_config_failure_graceful():
    """Test that config fetch failure doesn't break the coordinator."""
    mock_session = _make_mock_session([
        (200, [{"id": 1}]),  # previous_race
        (200, []),  # next_race
        (200, []),  # live_race
        (500, None),  # config (error)
    ])

    coordinator = _make_coordinator(mock_session)

    data = await coordinator._async_update_data()

    assert data is not None
    assert data["previous_race"] == [{"id": 1}]
    assert data["config"] is None
    assert coordinator.backend_version == "unknown"
