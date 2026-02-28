"""Test the new Galaxie sensors: position, weather, caution, series, race name, track type."""

from unittest.mock import MagicMock

from custom_components.galaxie.sensor import (
    LiveRaceActualDistanceSensor,
    LiveRaceCautionCountSensor,
    LiveRacePitStopDeltaSensor,
    LiveRaceSeriesSensor,
    NextRaceNameSensor,
    NextRaceTrackTypeSensor,
    PreviousRaceNameSensor,
    PreviousRaceTrackTypeSensor,
    VehiclePositionSensor,
    WeatherConditionsSensor,
    WeatherHumiditySensor,
    WeatherRainChanceSensor,
    WeatherTemperatureSensor,
    WeatherWindDirectionSensor,
    WeatherWindSpeedSensor,
)


def _make_mock_coordinator(data=None, last_update_success=True):
    """Create a mock coordinator with given data."""
    coordinator = MagicMock()
    coordinator.data = data
    coordinator.last_update_success = last_update_success
    coordinator.async_add_listener = MagicMock()
    coordinator.backend_version = "unknown"
    return coordinator


LIVE_RACE_DATA = {
    "id": "abc-123",
    "name": "Daytona 500",
    "series": 1,
    "pit_stop_delta": 12.5,
    "actual_distance": 250.5,
    "flag_periods": [
        {"flag": 1, "start_lap": 1, "end_lap": 30},
        {"flag": 2, "start_lap": 31, "end_lap": 34},
        {"flag": 1, "start_lap": 35, "end_lap": 80},
        {"flag": 2, "start_lap": 81, "end_lap": 85},
        {"flag": 2, "start_lap": 100, "end_lap": 103},
    ],
}

VEHICLE_LIST = [
    {
        "vehicle_id": 1,
        "display_name": "Kyle Larson",
        "vehicle_number": "5",
        "running_position": 1,
        "team_name": "Hendrick Motorsports",
        "manufacturer": "Chevrolet",
        "sponsor": "HendrickCars.com",
    },
    {
        "vehicle_id": 2,
        "display_name": "William Byron",
        "vehicle_number": "24",
        "running_position": 2,
        "team_name": "Hendrick Motorsports",
        "manufacturer": "Chevrolet",
        "sponsor": "Axalta",
    },
    {
        "vehicle_id": 3,
        "display_name": "Denny Hamlin",
        "vehicle_number": "11",
        "running_position": 3,
        "team_name": "Joe Gibbs Racing",
        "manufacturer": "Toyota",
        "sponsor": "FedEx",
    },
    {
        "vehicle_id": 4,
        "display_name": "Chase Elliott",
        "vehicle_number": "9",
        "running_position": 4,
        "team_name": "Hendrick Motorsports",
        "manufacturer": "Chevrolet",
        "sponsor": "NAPA Auto Parts",
    },
    {
        "vehicle_id": 5,
        "display_name": "Martin Truex Jr.",
        "vehicle_number": "19",
        "running_position": 5,
        "team_name": "Joe Gibbs Racing",
        "manufacturer": "Toyota",
        "sponsor": "Bass Pro Shops",
    },
]

WEATHER_DATA = {
    "current": {
        "temp": 78.5,
        "humidity": 65,
        "wind_speed": 12.3,
        "wind_deg": 180,
        "weather": [{"main": "Clouds", "description": "scattered clouds"}],
    },
    "hourly": [
        {"pop": 0.35},
        {"pop": 0.40},
    ],
}

PREVIOUS_RACE = {
    "series_name": "NASCAR Cup Series",
    "name": "Daytona 500",
    "track_type": "Superspeedway",
    "track_name": "Daytona International Speedway",
}

NEXT_RACE = {
    "series_name": "NASCAR Cup Series",
    "name": "Atlanta 400",
    "track_type": "Intermediate",
    "track_name": "Atlanta Motor Speedway",
}


class TestPreviousRaceNameSensor:
    """Test PreviousRaceNameSensor."""

    def test_extracts_race_name(self):
        coordinator = _make_mock_coordinator(
            data={"previous_race": [PREVIOUS_RACE]}
        )
        sensor = PreviousRaceNameSensor(coordinator, "NASCAR Cup Series")
        assert sensor.native_value == "Daytona 500"

    def test_returns_none_when_no_data(self):
        coordinator = _make_mock_coordinator(data=None)
        sensor = PreviousRaceNameSensor(coordinator, "NASCAR Cup Series")
        assert sensor.native_value is None

    def test_unique_id(self):
        coordinator = _make_mock_coordinator()
        sensor = PreviousRaceNameSensor(coordinator, "NASCAR Cup Series")
        assert sensor._attr_unique_id == "previous_race_nascar_cup_series_name"


class TestPreviousRaceTrackTypeSensor:
    """Test PreviousRaceTrackTypeSensor."""

    def test_extracts_track_type(self):
        coordinator = _make_mock_coordinator(
            data={"previous_race": [PREVIOUS_RACE]}
        )
        sensor = PreviousRaceTrackTypeSensor(coordinator, "NASCAR Cup Series")
        assert sensor.native_value == "Superspeedway"


class TestNextRaceNameSensor:
    """Test NextRaceNameSensor."""

    def test_extracts_race_name(self):
        coordinator = _make_mock_coordinator(data={"next_race": [NEXT_RACE]})
        sensor = NextRaceNameSensor(coordinator, "NASCAR Cup Series")
        assert sensor.native_value == "Atlanta 400"

    def test_unique_id(self):
        coordinator = _make_mock_coordinator()
        sensor = NextRaceNameSensor(coordinator, "NASCAR Cup Series")
        assert sensor._attr_unique_id == "next_race_nascar_cup_series_name"


class TestNextRaceTrackTypeSensor:
    """Test NextRaceTrackTypeSensor."""

    def test_extracts_track_type(self):
        coordinator = _make_mock_coordinator(data={"next_race": [NEXT_RACE]})
        sensor = NextRaceTrackTypeSensor(coordinator, "NASCAR Cup Series")
        assert sensor.native_value == "Intermediate"


class TestLiveRaceSeriesSensor:
    """Test LiveRaceSeriesSensor."""

    def test_maps_series_id_to_name(self):
        coordinator = _make_mock_coordinator(
            data={"live_race": [LIVE_RACE_DATA]}
        )
        sensor = LiveRaceSeriesSensor(coordinator)
        assert sensor.native_value == "NASCAR Cup Series"

    def test_maps_series_id_2(self):
        race = {**LIVE_RACE_DATA, "series": 2}
        coordinator = _make_mock_coordinator(data={"live_race": [race]})
        sensor = LiveRaceSeriesSensor(coordinator)
        assert sensor.native_value == "NASCAR Xfinity Series"

    def test_maps_series_id_3(self):
        race = {**LIVE_RACE_DATA, "series": 3}
        coordinator = _make_mock_coordinator(data={"live_race": [race]})
        sensor = LiveRaceSeriesSensor(coordinator)
        assert sensor.native_value == "NASCAR Craftsman Truck Series"

    def test_unknown_series_id(self):
        race = {**LIVE_RACE_DATA, "series": 99}
        coordinator = _make_mock_coordinator(data={"live_race": [race]})
        sensor = LiveRaceSeriesSensor(coordinator)
        assert sensor.native_value == "Unknown (99)"

    def test_unique_id(self):
        coordinator = _make_mock_coordinator()
        sensor = LiveRaceSeriesSensor(coordinator)
        assert sensor._attr_unique_id == "live_race_series"


class TestLiveRacePitStopDeltaSensor:
    """Test LiveRacePitStopDeltaSensor."""

    def test_extracts_pit_stop_delta(self):
        coordinator = _make_mock_coordinator(
            data={"live_race": [LIVE_RACE_DATA]}
        )
        sensor = LiveRacePitStopDeltaSensor(coordinator)
        assert sensor.native_value == 12.5

    def test_unit_is_seconds(self):
        coordinator = _make_mock_coordinator()
        sensor = LiveRacePitStopDeltaSensor(coordinator)
        assert sensor._attr_native_unit_of_measurement == "s"


class TestLiveRaceActualDistanceSensor:
    """Test LiveRaceActualDistanceSensor."""

    def test_extracts_actual_distance(self):
        coordinator = _make_mock_coordinator(
            data={"live_race": [LIVE_RACE_DATA]}
        )
        sensor = LiveRaceActualDistanceSensor(coordinator)
        assert sensor.native_value == 250.5

    def test_unit_is_miles(self):
        coordinator = _make_mock_coordinator()
        sensor = LiveRaceActualDistanceSensor(coordinator)
        assert sensor._attr_native_unit_of_measurement == "miles"


class TestLiveRaceCautionCountSensor:
    """Test LiveRaceCautionCountSensor."""

    def test_counts_yellow_flags(self):
        coordinator = _make_mock_coordinator(
            data={"live_race": [LIVE_RACE_DATA]}
        )
        sensor = LiveRaceCautionCountSensor(coordinator)
        # 3 entries with flag == 2
        assert sensor.native_value == 3

    def test_zero_cautions(self):
        race = {
            **LIVE_RACE_DATA,
            "flag_periods": [{"flag": 1, "start_lap": 1, "end_lap": 200}],
        }
        coordinator = _make_mock_coordinator(data={"live_race": [race]})
        sensor = LiveRaceCautionCountSensor(coordinator)
        assert sensor.native_value == 0

    def test_empty_flag_periods(self):
        race = {**LIVE_RACE_DATA, "flag_periods": []}
        coordinator = _make_mock_coordinator(data={"live_race": [race]})
        sensor = LiveRaceCautionCountSensor(coordinator)
        assert sensor.native_value == 0

    def test_missing_flag_periods(self):
        race = {"id": "abc-123", "name": "Test Race"}
        coordinator = _make_mock_coordinator(data={"live_race": [race]})
        sensor = LiveRaceCautionCountSensor(coordinator)
        assert sensor.native_value == 0


class TestVehiclePositionSensor:
    """Test VehiclePositionSensor."""

    def test_p1_returns_leader(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "vehicle_list": VEHICLE_LIST,
            }
        )
        sensor = VehiclePositionSensor(coordinator, 1)
        assert sensor.native_value == "Kyle Larson"

    def test_p5_returns_fifth_place(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "vehicle_list": VEHICLE_LIST,
            }
        )
        sensor = VehiclePositionSensor(coordinator, 5)
        assert sensor.native_value == "Martin Truex Jr."

    def test_extra_attributes_include_vehicle_details(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "vehicle_list": VEHICLE_LIST,
            }
        )
        sensor = VehiclePositionSensor(coordinator, 1)
        attrs = sensor.extra_state_attributes
        assert attrs is not None
        assert attrs["vehicle_number"] == "5"
        assert attrs["team_name"] == "Hendrick Motorsports"
        assert attrs["manufacturer"] == "Chevrolet"
        assert attrs["sponsor"] == "HendrickCars.com"

    def test_returns_none_when_no_vehicles(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "vehicle_list": [],
            }
        )
        sensor = VehiclePositionSensor(coordinator, 1)
        assert sensor.native_value is None

    def test_returns_none_when_position_not_found(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "vehicle_list": VEHICLE_LIST,
            }
        )
        sensor = VehiclePositionSensor(coordinator, 99)
        assert sensor.native_value is None

    def test_unavailable_when_no_live_race(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [],
                "vehicle_list": VEHICLE_LIST,
            }
        )
        sensor = VehiclePositionSensor(coordinator, 1)
        assert sensor.available is False

    def test_unavailable_when_no_vehicle_data(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "vehicle_list": [],
            }
        )
        sensor = VehiclePositionSensor(coordinator, 1)
        assert sensor.available is False

    def test_available_with_data(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "vehicle_list": VEHICLE_LIST,
            }
        )
        sensor = VehiclePositionSensor(coordinator, 1)
        assert sensor.available is True

    def test_unique_ids_for_positions(self):
        coordinator = _make_mock_coordinator()
        for pos in range(1, 6):
            sensor = VehiclePositionSensor(coordinator, pos)
            assert sensor._attr_unique_id == f"live_race_position_{pos}"


class TestWeatherTemperatureSensor:
    """Test WeatherTemperatureSensor."""

    def test_extracts_temperature(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "weather": WEATHER_DATA,
            }
        )
        sensor = WeatherTemperatureSensor(coordinator)
        assert sensor.native_value == 78.5

    def test_unavailable_when_no_weather(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "weather": None,
            }
        )
        sensor = WeatherTemperatureSensor(coordinator)
        assert sensor.available is False

    def test_unavailable_when_no_live_race(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [],
                "weather": WEATHER_DATA,
            }
        )
        sensor = WeatherTemperatureSensor(coordinator)
        assert sensor.available is False


class TestWeatherHumiditySensor:
    """Test WeatherHumiditySensor."""

    def test_extracts_humidity(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "weather": WEATHER_DATA,
            }
        )
        sensor = WeatherHumiditySensor(coordinator)
        assert sensor.native_value == 65


class TestWeatherWindSpeedSensor:
    """Test WeatherWindSpeedSensor."""

    def test_extracts_wind_speed(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "weather": WEATHER_DATA,
            }
        )
        sensor = WeatherWindSpeedSensor(coordinator)
        assert sensor.native_value == 12.3


class TestWeatherWindDirectionSensor:
    """Test WeatherWindDirectionSensor."""

    def test_extracts_wind_direction(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "weather": WEATHER_DATA,
            }
        )
        sensor = WeatherWindDirectionSensor(coordinator)
        assert sensor.native_value == 180


class TestWeatherRainChanceSensor:
    """Test WeatherRainChanceSensor."""

    def test_extracts_rain_probability(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "weather": WEATHER_DATA,
            }
        )
        sensor = WeatherRainChanceSensor(coordinator)
        # 0.35 * 100 = 35
        assert sensor.native_value == 35

    def test_empty_hourly(self):
        weather = {**WEATHER_DATA, "hourly": []}
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "weather": weather,
            }
        )
        sensor = WeatherRainChanceSensor(coordinator)
        assert sensor.native_value is None

    def test_missing_hourly(self):
        weather = {"current": WEATHER_DATA["current"]}
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "weather": weather,
            }
        )
        sensor = WeatherRainChanceSensor(coordinator)
        assert sensor.native_value is None


class TestWeatherConditionsSensor:
    """Test WeatherConditionsSensor."""

    def test_extracts_conditions(self):
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "weather": WEATHER_DATA,
            }
        )
        sensor = WeatherConditionsSensor(coordinator)
        assert sensor.native_value == "Clouds"

    def test_empty_weather_list(self):
        weather = {
            "current": {"temp": 78.5, "weather": []},
            "hourly": [],
        }
        coordinator = _make_mock_coordinator(
            data={
                "live_race": [LIVE_RACE_DATA],
                "weather": weather,
            }
        )
        sensor = WeatherConditionsSensor(coordinator)
        assert sensor.native_value is None

    def test_unique_id(self):
        coordinator = _make_mock_coordinator()
        sensor = WeatherConditionsSensor(coordinator)
        assert sensor._attr_unique_id == "live_race_weather_conditions"
