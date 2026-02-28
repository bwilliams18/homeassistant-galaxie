"""Test the Galaxie WebSocket client."""

import asyncio
import json

import aiohttp
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.galaxie.websocket_client import (
    GalaxieWebSocketClient,
    INITIAL_BACKOFF,
    BACKOFF_MULTIPLIER,
    MAX_BACKOFF,
)


def _make_ws_client(
    on_run_detail=None,
    on_disconnect=None,
):
    """Create a WebSocket client with mock dependencies."""
    session = AsyncMock()
    on_run_detail = on_run_detail or MagicMock()
    on_disconnect = on_disconnect or MagicMock()

    client = GalaxieWebSocketClient(
        session=session,
        ws_url="wss://galaxie.app/ws/runs/test-run-id/",
        run_id="test-run-id",
        on_run_detail=on_run_detail,
        on_disconnect=on_disconnect,
    )
    return client, session, on_run_detail, on_disconnect


def test_initial_state():
    """Test client initial state."""
    client, _, _, _ = _make_ws_client()

    assert client.connected is False
    assert client.run_id == "test-run-id"


def test_handle_run_detail_message():
    """Test that run_detail messages are routed to the callback."""
    client, _, on_run_detail, _ = _make_ws_client()

    run_data = {"id": "test-run-id", "lap_number": 42, "flag": 1}
    raw = json.dumps({"type": "run_detail", "data": run_data})
    client._handle_message(raw)

    on_run_detail.assert_called_once_with(run_data)


def test_handle_run_detail_missing_data():
    """Test that run_detail without data payload is ignored."""
    client, _, on_run_detail, _ = _make_ws_client()

    raw = json.dumps({"type": "run_detail"})
    client._handle_message(raw)

    on_run_detail.assert_not_called()


def test_handle_arrow_messages_ignored():
    """Test that Arrow-encoded message types are silently ignored."""
    client, _, on_run_detail, _ = _make_ws_client()

    for msg_type in ["vehicle_laps", "pit_stops", "driver_results", "lap_time_falloff"]:
        raw = json.dumps({"type": msg_type, "data": "base64arrowdata"})
        client._handle_message(raw)

    on_run_detail.assert_not_called()


def test_handle_unknown_message_type():
    """Test that unknown message types are ignored."""
    client, _, on_run_detail, _ = _make_ws_client()

    raw = json.dumps({"type": "some_future_type", "data": {}})
    client._handle_message(raw)

    on_run_detail.assert_not_called()


def test_handle_invalid_json():
    """Test that non-JSON messages are handled gracefully."""
    client, _, on_run_detail, _ = _make_ws_client()

    client._handle_message("not valid json {{{")

    on_run_detail.assert_not_called()


@pytest.mark.asyncio
async def test_start_creates_task():
    """Test that start() creates a background task."""
    client, session, _, _ = _make_ws_client()

    # Make ws_connect raise immediately so the loop exits on cancel
    def raise_on_connect(*args, **kwargs):
        raise aiohttp.ClientError("test")

    session.ws_connect = raise_on_connect

    client.start()
    assert client._task is not None

    # Clean up
    await client.stop()


@pytest.mark.asyncio
async def test_stop_cancels_task():
    """Test that stop() cancels the background task and resets state."""
    client, session, _, _ = _make_ws_client()

    # Create a task that blocks
    async def block_forever():
        await asyncio.sleep(3600)

    client._task = asyncio.create_task(block_forever())
    client._connected = True

    await client.stop()

    assert client.connected is False
    assert client._closing is True


@pytest.mark.asyncio
async def test_stop_when_not_started():
    """Test that stop() works even if never started."""
    client, _, _, _ = _make_ws_client()

    await client.stop()  # Should not raise
    assert client.connected is False


@pytest.mark.asyncio
async def test_reconnect_backoff_increases():
    """Test that reconnection backoff increases exponentially."""
    client, session, _, on_disconnect = _make_ws_client()

    connect_count = 0
    sleep_durations = []

    def failing_ws_connect(*args, **kwargs):
        nonlocal connect_count
        connect_count += 1
        if connect_count >= 3:
            client._closing = True
        raise aiohttp.ClientError("Connection refused")

    session.ws_connect = failing_ws_connect

    original_sleep = asyncio.sleep

    async def mock_sleep(duration):
        sleep_durations.append(duration)
        await original_sleep(0)

    with patch("custom_components.galaxie.websocket_client.asyncio.sleep", mock_sleep):
        await client._run()

    assert connect_count == 3
    # First backoff: INITIAL_BACKOFF + jitter (jitter <= 0.5 * INITIAL_BACKOFF)
    assert sleep_durations[0] >= INITIAL_BACKOFF
    assert sleep_durations[0] <= INITIAL_BACKOFF * 1.5
    # Second backoff should be larger
    assert sleep_durations[1] >= INITIAL_BACKOFF * BACKOFF_MULTIPLIER


def test_backoff_constants():
    """Test that backoff constants are reasonable."""
    assert INITIAL_BACKOFF == 1.0
    assert MAX_BACKOFF == 60.0
    assert BACKOFF_MULTIPLIER == 2.0
