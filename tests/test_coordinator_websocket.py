"""Test WebSocket integration in the Galaxie coordinator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.galaxie.coordinator import GalaxieDataCoordinator


def _make_mock_session(responses):
    """Create a mock session that returns different responses per call."""
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


LIVE_RACE_DATA = {
    "id": "abc-123",
    "name": "Test Race",
    "lap_number": 42,
    "flag": 1,
    "total_laps": 200,
}

CONFIG_DATA = {"version": "2026.02.25", "environment": "production"}


@pytest.mark.asyncio
async def test_ws_starts_when_live_race_detected():
    """Test that WS connection starts when a live race is discovered via REST."""
    mock_session = _make_mock_session([
        (200, []),  # previous_race
        (200, []),  # next_race
        (200, [LIVE_RACE_DATA]),  # live_race with run id
        (200, CONFIG_DATA),  # config
    ])
    coordinator = _make_coordinator(mock_session)

    with patch.object(
        coordinator, "_manage_ws_connection", new_callable=AsyncMock
    ) as mock_manage:
        await coordinator._async_update_data()
        mock_manage.assert_called_once()
        live_data = mock_manage.call_args[0][0]
        assert len(live_data) == 1
        assert live_data[0]["id"] == "abc-123"


@pytest.mark.asyncio
async def test_manage_ws_starts_client():
    """Test _manage_ws_connection creates and starts a WS client."""
    mock_session = AsyncMock()
    coordinator = _make_coordinator(mock_session)

    assert coordinator._ws_client is None
    assert coordinator._current_run_id is None

    with patch(
        "custom_components.galaxie.coordinator.GalaxieWebSocketClient"
    ) as MockWSClient:
        mock_client = MagicMock()
        MockWSClient.return_value = mock_client

        await coordinator._manage_ws_connection([LIVE_RACE_DATA])

        MockWSClient.assert_called_once()
        mock_client.start.assert_called_once()
        assert coordinator._current_run_id == "abc-123"
        assert coordinator._ws_client is mock_client


@pytest.mark.asyncio
async def test_manage_ws_stops_on_no_live_race():
    """Test WS is stopped when no live race is active."""
    mock_session = AsyncMock()
    coordinator = _make_coordinator(mock_session)

    mock_client = AsyncMock()
    coordinator._ws_client = mock_client
    coordinator._current_run_id = "abc-123"
    coordinator._ws_live_data = LIVE_RACE_DATA

    await coordinator._manage_ws_connection([])

    mock_client.stop.assert_called_once()
    assert coordinator._ws_client is None
    assert coordinator._current_run_id is None
    assert coordinator._ws_live_data is None


@pytest.mark.asyncio
async def test_manage_ws_reconnects_on_run_id_change():
    """Test WS reconnects when a different run becomes live."""
    mock_session = AsyncMock()
    coordinator = _make_coordinator(mock_session)

    old_client = AsyncMock()
    coordinator._ws_client = old_client
    coordinator._current_run_id = "old-run-id"

    new_race = {**LIVE_RACE_DATA, "id": "new-run-id"}

    with patch(
        "custom_components.galaxie.coordinator.GalaxieWebSocketClient"
    ) as MockWSClient:
        new_client = MagicMock()
        MockWSClient.return_value = new_client

        await coordinator._manage_ws_connection([new_race])

        old_client.stop.assert_called_once()
        new_client.start.assert_called_once()
        assert coordinator._current_run_id == "new-run-id"


@pytest.mark.asyncio
async def test_manage_ws_no_op_for_same_run():
    """Test that _manage_ws_connection doesn't reconnect for the same run."""
    mock_session = AsyncMock()
    coordinator = _make_coordinator(mock_session)

    mock_client = MagicMock()
    coordinator._ws_client = mock_client
    coordinator._current_run_id = "abc-123"

    with patch(
        "custom_components.galaxie.coordinator.GalaxieWebSocketClient"
    ) as MockWSClient:
        await coordinator._manage_ws_connection([LIVE_RACE_DATA])

        MockWSClient.assert_not_called()
        mock_client.stop.assert_not_called()


@pytest.mark.asyncio
async def test_rest_live_fetch_skipped_when_ws_active():
    """Test that REST /api/live/ is skipped when WebSocket is delivering data."""
    mock_session = _make_mock_session([
        (200, []),  # previous_race
        (200, []),  # next_race
        # No live_race call expected!
        (200, CONFIG_DATA),  # config
        (200, {"current": {"temp": 75}}),  # weather (live race active)
    ])
    coordinator = _make_coordinator(mock_session)

    # Simulate active WS
    mock_client = MagicMock()
    mock_client.connected = True
    coordinator._ws_client = mock_client
    coordinator._current_run_id = "abc-123"
    coordinator._ws_live_data = LIVE_RACE_DATA

    with patch.object(
        coordinator, "_manage_ws_connection", new_callable=AsyncMock
    ):
        data = await coordinator._async_update_data()

    # Should use WS data instead of REST
    assert data["live_race"] == [LIVE_RACE_DATA]
    # 4 REST calls: previous, next, config, weather (no live)
    assert mock_session.get.call_count == 4


@pytest.mark.asyncio
async def test_rest_fallback_when_ws_disconnected():
    """Test that REST polling resumes when WS is not connected."""
    mock_session = _make_mock_session([
        (200, []),  # previous_race
        (200, []),  # next_race
        (200, [LIVE_RACE_DATA]),  # live_race via REST
        (200, CONFIG_DATA),  # config
        (200, {"current": {"temp": 75}}),  # weather (live race active)
    ])
    coordinator = _make_coordinator(mock_session)

    # WS client exists but is disconnected
    mock_client = MagicMock()
    mock_client.connected = False
    coordinator._ws_client = mock_client
    coordinator._current_run_id = "abc-123"

    with patch.object(
        coordinator, "_manage_ws_connection", new_callable=AsyncMock
    ):
        data = await coordinator._async_update_data()

    # Should fetch live data via REST
    assert data["live_race"] == [LIVE_RACE_DATA]
    # 5 REST calls: previous, next, live, config, weather
    assert mock_session.get.call_count == 5


@pytest.mark.asyncio
async def test_ws_on_run_detail_updates_data():
    """Test that WS run_detail callback updates coordinator data."""
    mock_session = AsyncMock()
    coordinator = _make_coordinator(mock_session)
    coordinator.data = {
        "previous_race": [],
        "next_race": [],
        "live_race": [],
        "config": None,
    }

    updated_race = {**LIVE_RACE_DATA, "lap_number": 50}

    with patch.object(coordinator, "async_set_updated_data") as mock_set:
        coordinator._ws_on_run_detail(updated_race)

    assert coordinator._ws_live_data == updated_race
    assert coordinator.data["live_race"] == [updated_race]
    mock_set.assert_called_once_with(coordinator.data)


@pytest.mark.asyncio
async def test_ws_on_disconnect_clears_state():
    """Test that WS disconnect callback clears WS-related state."""
    mock_session = AsyncMock()
    coordinator = _make_coordinator(mock_session)

    coordinator._ws_client = MagicMock()
    coordinator._current_run_id = "abc-123"
    coordinator._ws_live_data = LIVE_RACE_DATA
    coordinator._ws_vehicle_data = [{"display_name": "Driver A"}]

    coordinator._ws_on_disconnect()

    assert coordinator._ws_client is None
    assert coordinator._current_run_id is None
    assert coordinator._ws_live_data is None
    assert coordinator._ws_vehicle_data is None


@pytest.mark.asyncio
async def test_async_shutdown_stops_ws():
    """Test that async_shutdown stops the WS client."""
    mock_session = AsyncMock()
    coordinator = _make_coordinator(mock_session)

    mock_client = AsyncMock()
    coordinator._ws_client = mock_client
    coordinator._current_run_id = "abc-123"

    await coordinator.async_shutdown()

    mock_client.stop.assert_called_once()
    assert coordinator._ws_client is None
    assert coordinator._current_run_id is None


@pytest.mark.asyncio
async def test_async_shutdown_no_op_without_ws():
    """Test that async_shutdown is safe when no WS client exists."""
    mock_session = AsyncMock()
    coordinator = _make_coordinator(mock_session)

    await coordinator.async_shutdown()  # Should not raise


@pytest.mark.asyncio
async def test_ws_on_vehicle_list_updates_data():
    """Test that WS vehicle_list callback updates coordinator data."""
    mock_session = AsyncMock()
    coordinator = _make_coordinator(mock_session)
    coordinator.data = {
        "previous_race": [],
        "next_race": [],
        "live_race": [],
        "config": None,
        "vehicle_list": [],
        "weather": None,
    }

    vehicle_data = [
        {"vehicle_id": 1, "display_name": "Driver A", "running_position": 1},
        {"vehicle_id": 2, "display_name": "Driver B", "running_position": 2},
    ]

    with patch.object(coordinator, "async_set_updated_data") as mock_set:
        coordinator._ws_on_vehicle_list(vehicle_data)

    assert coordinator._ws_vehicle_data == vehicle_data
    assert coordinator.data["vehicle_list"] == vehicle_data
    mock_set.assert_called_once_with(coordinator.data)


@pytest.mark.asyncio
async def test_vehicle_list_in_update_data():
    """Test that vehicle_list appears in coordinator data output."""
    mock_session = _make_mock_session([
        (200, []),  # previous_race
        (200, []),  # next_race
        (200, [LIVE_RACE_DATA]),  # live_race
        (200, CONFIG_DATA),  # config
    ])
    coordinator = _make_coordinator(mock_session)

    vehicle_data = [{"display_name": "Driver A", "running_position": 1}]
    coordinator._ws_vehicle_data = vehicle_data

    with patch.object(
        coordinator, "_manage_ws_connection", new_callable=AsyncMock
    ):
        data = await coordinator._async_update_data()

    assert data["vehicle_list"] == vehicle_data


@pytest.mark.asyncio
async def test_manage_ws_clears_vehicle_and_weather_on_no_live():
    """Test that vehicle and weather data are cleared when no live race."""
    mock_session = AsyncMock()
    coordinator = _make_coordinator(mock_session)

    mock_client = AsyncMock()
    coordinator._ws_client = mock_client
    coordinator._current_run_id = "abc-123"
    coordinator._ws_vehicle_data = [{"display_name": "Driver A"}]
    coordinator._weather_data = {"current": {"temp": 75}}
    coordinator._last_weather_fetch = MagicMock()

    await coordinator._manage_ws_connection([])

    assert coordinator._ws_vehicle_data is None
    assert coordinator._weather_data is None
    assert coordinator._last_weather_fetch is None


@pytest.mark.asyncio
async def test_weather_fetched_when_live_race():
    """Test that weather is fetched when a live race is active."""
    mock_session = _make_mock_session([
        (200, []),  # previous_race
        (200, []),  # next_race
        (200, [LIVE_RACE_DATA]),  # live_race
        (200, CONFIG_DATA),  # config
        (200, {"current": {"temp": 75}}),  # weather
    ])
    coordinator = _make_coordinator(mock_session)

    with patch.object(
        coordinator,
        "_manage_ws_connection",
        new_callable=AsyncMock,
        side_effect=lambda data: setattr(coordinator, "_current_run_id", "abc-123")
        if data
        else None,
    ):
        data = await coordinator._async_update_data()

    assert data["weather"] == {"current": {"temp": 75}}
    assert coordinator._weather_data == {"current": {"temp": 75}}
    assert coordinator._last_weather_fetch is not None


@pytest.mark.asyncio
async def test_weather_not_fetched_when_no_live_race():
    """Test that weather is not fetched when no live race."""
    mock_session = _make_mock_session([
        (200, []),  # previous_race
        (200, []),  # next_race
        (200, []),  # live_race (empty)
        (200, CONFIG_DATA),  # config
    ])
    coordinator = _make_coordinator(mock_session)

    with patch.object(
        coordinator, "_manage_ws_connection", new_callable=AsyncMock
    ):
        data = await coordinator._async_update_data()

    assert data["weather"] is None
    # Only 4 REST calls (no weather fetch)
    assert mock_session.get.call_count == 4


@pytest.mark.asyncio
async def test_async_shutdown_clears_weather():
    """Test that async_shutdown clears weather data."""
    mock_session = AsyncMock()
    coordinator = _make_coordinator(mock_session)

    coordinator._weather_data = {"current": {"temp": 75}}
    coordinator._last_weather_fetch = MagicMock()

    await coordinator.async_shutdown()

    assert coordinator._weather_data is None
    assert coordinator._last_weather_fetch is None
