"""Test the Galaxie coordinator."""

import pytest
from unittest.mock import AsyncMock, patch

from custom_components.galaxie.coordinator import GalaxieDataCoordinator


@pytest.mark.asyncio
async def test_coordinator_initialization():
    """Test coordinator initialization."""
    mock_session = AsyncMock()
    mock_hass = AsyncMock()

    coordinator = GalaxieDataCoordinator(mock_hass, mock_session)

    assert coordinator is not None
    assert coordinator.session == mock_session


@pytest.mark.asyncio
async def test_coordinator_update_data():
    """Test coordinator data update."""
    mock_session = AsyncMock()
    mock_hass = AsyncMock()

    # Mock API responses
    mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(
        side_effect=[
            [{"id": 1, "name": "Test Race"}],  # previous_race
            [{"id": 2, "name": "Next Race"}],  # next_race
            [],  # live_race (empty)
        ]
    )
    mock_session.get.return_value.__aenter__.return_value.status = 200

    coordinator = GalaxieDataCoordinator(mock_hass, mock_session)

    # Test data update
    data = await coordinator._async_update_data()

    assert data is not None
    assert "previous_race" in data
    assert "next_race" in data
    assert "live_race" in data
