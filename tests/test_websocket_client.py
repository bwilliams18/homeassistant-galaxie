"""Tests for the Galaxie Centrifugo WebSocket client."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from centrifuge import UnauthorizedError

from custom_components.galaxie.const import (
    BASE_URL,
    CENTRIFUGO_TOKEN_PATH,
    CENTRIFUGO_WS_PATH,
    WS_BASE_URL,
)
from custom_components.galaxie.websocket_client import GalaxieWebSocketClient


def _make_ws_client(
    on_run_detail=None,
    on_vehicle_list=None,
    on_disconnect=None,
):
    """Create a GalaxieWebSocketClient with mocked dependencies."""
    session = AsyncMock()
    on_run_detail = on_run_detail or MagicMock()
    on_vehicle_list = on_vehicle_list or MagicMock()
    on_disconnect = on_disconnect or MagicMock()

    client = GalaxieWebSocketClient(
        session=session,
        run_id="test-run-id",
        on_run_detail=on_run_detail,
        on_vehicle_list=on_vehicle_list,
        on_disconnect=on_disconnect,
    )
    return client, session, on_run_detail, on_vehicle_list, on_disconnect


def _pub_ctx(data):
    """Build a minimal object shaped like centrifuge PublicationContext."""
    return SimpleNamespace(pub=SimpleNamespace(data=data))


def test_initial_state():
    """Client starts disconnected and knows its run id/channel URLs."""
    client, _, _, _, _ = _make_ws_client()

    assert client.connected is False
    assert client.run_id == "test-run-id"
    assert client._channel == "run:test-run-id"
    assert client._ws_url == f"{WS_BASE_URL}{CENTRIFUGO_WS_PATH}"
    assert client._token_url == f"{BASE_URL}{CENTRIFUGO_TOKEN_PATH}"


def test_handle_run_detail_publication():
    """run_detail publications are routed to on_run_detail."""
    client, _, on_run_detail, _, _ = _make_ws_client()

    run_data = {"id": "test-run-id", "lap_number": 42, "flag": 1}
    client._handle_publication_data({"type": "run_detail", "data": run_data})

    on_run_detail.assert_called_once_with(run_data)


def test_handle_run_detail_missing_data():
    """run_detail envelope without a data payload is ignored."""
    client, _, on_run_detail, _, _ = _make_ws_client()

    client._handle_publication_data({"type": "run_detail"})

    on_run_detail.assert_not_called()


def test_handle_run_detail_wrong_payload_type():
    """run_detail with non-dict data payload is ignored."""
    client, _, on_run_detail, _, _ = _make_ws_client()

    client._handle_publication_data({"type": "run_detail", "data": "not-a-dict"})

    on_run_detail.assert_not_called()


def test_handle_vehicle_list_publication():
    """vehicle_list publications are routed to on_vehicle_list."""
    client, _, _, on_vehicle_list, _ = _make_ws_client()

    vehicle_data = [
        {"vehicle_id": 1, "display_name": "Driver A", "running_position": 1},
        {"vehicle_id": 2, "display_name": "Driver B", "running_position": 2},
    ]
    client._handle_publication_data({"type": "vehicle_list", "data": vehicle_data})

    on_vehicle_list.assert_called_once_with(vehicle_data)


def test_handle_vehicle_list_missing_data():
    """vehicle_list envelope without data is ignored."""
    client, _, _, on_vehicle_list, _ = _make_ws_client()

    client._handle_publication_data({"type": "vehicle_list"})

    on_vehicle_list.assert_not_called()


def test_handle_vehicle_list_wrong_payload_type():
    """vehicle_list with non-list data payload is ignored."""
    client, _, _, on_vehicle_list, _ = _make_ws_client()

    client._handle_publication_data({"type": "vehicle_list", "data": {"x": 1}})

    on_vehicle_list.assert_not_called()


def test_handle_arrow_messages_ignored():
    """Arrow-encoded broadcast types are silently ignored."""
    client, _, on_run_detail, on_vehicle_list, _ = _make_ws_client()

    for msg_type in [
        "vehicle_laps",
        "pit_stops",
        "driver_results",
        "lap_time_falloff",
        "g_rating_forecast",
        "grcup_telemetry",
    ]:
        client._handle_publication_data({"type": msg_type, "data": "base64arrowdata"})

    on_run_detail.assert_not_called()
    on_vehicle_list.assert_not_called()


def test_handle_unknown_message_type():
    """Unknown envelope types are ignored."""
    client, _, on_run_detail, on_vehicle_list, _ = _make_ws_client()

    client._handle_publication_data({"type": "some_future_type", "data": {"x": 1}})

    on_run_detail.assert_not_called()
    on_vehicle_list.assert_not_called()


def test_handle_non_dict_publication():
    """Non-dict publication data is ignored gracefully."""
    client, _, on_run_detail, on_vehicle_list, _ = _make_ws_client()

    client._handle_publication_data("not a dict")
    client._handle_publication_data(None)
    client._handle_publication_data([])

    on_run_detail.assert_not_called()
    on_vehicle_list.assert_not_called()


@pytest.mark.asyncio
async def test_subscription_event_handler_routes_publication():
    """SubscriptionEventHandler.on_publication forwards to _handle_publication_data."""
    client, _, on_run_detail, _, _ = _make_ws_client()
    handler = client._build_subscription_events()

    run_data = {"id": "test-run-id", "lap_number": 5, "flag": 1}
    await handler.on_publication(
        _pub_ctx({"type": "run_detail", "data": run_data})
    )

    on_run_detail.assert_called_once_with(run_data)


@pytest.mark.asyncio
async def test_client_event_handler_tracks_connection_state():
    """on_connected/on_disconnected toggle the connected flag."""
    client, _, _, _, _ = _make_ws_client()
    handler = client._build_client_events()

    assert client.connected is False
    await handler.on_connected(SimpleNamespace(client="c"))
    assert client.connected is True
    await handler.on_disconnected(SimpleNamespace(reason="server closed"))
    assert client.connected is False


@pytest.mark.asyncio
async def test_get_token_success():
    """_get_token returns the JWT from the token endpoint."""
    client, session, _, _, _ = _make_ws_client()

    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={"token": "jwt-abc"})
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=response)
    cm.__aexit__ = AsyncMock(return_value=False)
    session.post = MagicMock(return_value=cm)

    token = await client._get_token()

    assert token == "jwt-abc"
    session.post.assert_called_once_with(client._token_url)


@pytest.mark.asyncio
async def test_get_token_unauthorized():
    """_get_token raises UnauthorizedError on 401."""
    client, session, _, _, _ = _make_ws_client()

    response = AsyncMock()
    response.status = 401
    response.json = AsyncMock(return_value={})
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=response)
    cm.__aexit__ = AsyncMock(return_value=False)
    session.post = MagicMock(return_value=cm)

    with pytest.raises(UnauthorizedError):
        await client._get_token()


@pytest.mark.asyncio
async def test_get_token_empty_token():
    """_get_token raises when the server returns an empty token."""
    client, session, _, _, _ = _make_ws_client()

    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={"token": ""})
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=response)
    cm.__aexit__ = AsyncMock(return_value=False)
    session.post = MagicMock(return_value=cm)

    with pytest.raises(RuntimeError):
        await client._get_token()


@pytest.mark.asyncio
async def test_start_creates_client_and_subscription():
    """start() instantiates a centrifuge Client and schedules connect/subscribe."""
    client, _, _, _, _ = _make_ws_client()

    with patch(
        "custom_components.galaxie.websocket_client.Client"
    ) as MockClient, patch(
        "custom_components.galaxie.websocket_client.asyncio.create_task"
    ) as mock_create_task:
        mock_cent = MagicMock()
        mock_sub = MagicMock()
        mock_sub.subscribe = MagicMock(return_value="subscribe-coro")
        mock_cent.new_subscription = MagicMock(return_value=mock_sub)
        mock_cent.connect = MagicMock(return_value="connect-coro")
        MockClient.return_value = mock_cent

        client.start()

        MockClient.assert_called_once()
        _, kwargs = MockClient.call_args
        assert kwargs["get_token"].__func__ is GalaxieWebSocketClient._get_token
        assert kwargs["use_protobuf"] is False
        mock_cent.new_subscription.assert_called_once()
        args, _ = mock_cent.new_subscription.call_args
        assert args[0] == "run:test-run-id"
        # Both subscribe() and connect() should have been scheduled as tasks.
        assert mock_create_task.call_count == 2


def test_start_is_idempotent():
    """Calling start() twice is a no-op."""
    client, _, _, _, _ = _make_ws_client()
    client._client = MagicMock()  # pretend already started

    with patch("custom_components.galaxie.websocket_client.Client") as MockClient:
        client.start()
        MockClient.assert_not_called()


@pytest.mark.asyncio
async def test_stop_tears_down_client_and_fires_disconnect():
    """stop() disconnects the client and fires on_disconnect exactly once."""
    client, _, _, _, on_disconnect = _make_ws_client()

    mock_cent = MagicMock()
    mock_cent.disconnect = AsyncMock()
    mock_sub = MagicMock()
    mock_sub.unsubscribe = AsyncMock()
    client._client = mock_cent
    client._sub = mock_sub
    client._connected = True

    await client.stop()

    mock_sub.unsubscribe.assert_awaited_once()
    mock_cent.disconnect.assert_awaited_once()
    on_disconnect.assert_called_once()
    assert client._client is None
    assert client._sub is None
    assert client.connected is False
    assert client._closing is True


@pytest.mark.asyncio
async def test_stop_when_not_started():
    """stop() is safe when start() was never called."""
    client, _, _, _, on_disconnect = _make_ws_client()

    await client.stop()

    assert client.connected is False
    on_disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_stop_swallows_teardown_errors():
    """Teardown errors from unsubscribe/disconnect are swallowed."""
    client, _, _, _, on_disconnect = _make_ws_client()

    mock_cent = MagicMock()
    mock_cent.disconnect = AsyncMock(side_effect=RuntimeError("boom"))
    mock_sub = MagicMock()
    mock_sub.unsubscribe = AsyncMock(side_effect=RuntimeError("boom"))
    client._client = mock_cent
    client._sub = mock_sub

    await client.stop()  # Must not raise.

    on_disconnect.assert_called_once()
