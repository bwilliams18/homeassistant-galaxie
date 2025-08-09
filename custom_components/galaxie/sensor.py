"""Sensor platform for Galaxie integration."""

import logging
from datetime import datetime
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.helpers.typing import StateType

from .const import DOMAIN, SERIES_MAPPING, FLAG_MAPPING
from .device import get_previous_race_device, get_next_race_device, get_live_race_device

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Galaxie sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    _LOGGER.info("Setting up Galaxie sensors")

    entities = []

    # Add previous race sensors (3 devices - one per series)
    for series_id, series_name in SERIES_MAPPING.items():
        _LOGGER.debug("Creating previous race sensors for series: %s", series_name)
        entities.extend(
            [
                PreviousRaceTrackSensor(coordinator, series_name),
                PreviousRaceDateSensor(coordinator, series_name),
                PreviousRaceScheduledDistanceSensor(coordinator, series_name),
                PreviousRaceScheduledLapsSensor(coordinator, series_name),
                PreviousRaceCarsSensor(coordinator, series_name),
                PreviousRaceTVSensor(coordinator, series_name),
                PreviousRaceRadioSensor(coordinator, series_name),
                PreviousRacePlayoffSensor(coordinator, series_name),
                PreviousRaceWinnerSensor(coordinator, series_name),
                PreviousRaceActualDistanceSensor(coordinator, series_name),
                PreviousRaceActualLapsSensor(coordinator, series_name),
            ]
        )

    # Add next race sensors (3 devices - one per series)
    for series_id, series_name in SERIES_MAPPING.items():
        _LOGGER.debug("Creating next race sensors for series: %s", series_name)
        entities.extend(
            [
                NextRaceTrackSensor(coordinator, series_name),
                NextRaceDateSensor(coordinator, series_name),
                NextRaceScheduledDistanceSensor(coordinator, series_name),
                NextRaceScheduledLapsSensor(coordinator, series_name),
                NextRaceCarsSensor(coordinator, series_name),
                NextRaceTVSensor(coordinator, series_name),
                NextRaceRadioSensor(coordinator, series_name),
                NextRacePlayoffSensor(coordinator, series_name),
            ]
        )

    # Add live race sensors (dynamic - one device per active run)
    _LOGGER.debug("Creating live race sensors")
    entities.extend(
        [
            LiveRaceNameSensor(coordinator),
            LiveRaceTypeSensor(coordinator),
            LiveRaceStartTimeSensor(coordinator),
            LiveRaceEndTimeSensor(coordinator),
            LiveRaceTotalLapsSensor(coordinator),
            LiveRaceActualLapsSensor(coordinator),
            LiveRaceScheduledLapsSensor(coordinator),
            LiveRaceScheduledDistanceSensor(coordinator),
            LiveRaceStageLapsSensor(coordinator),
            LiveRaceStageStartSensor(coordinator),
            LiveRaceStageRemainingSensor(coordinator),
            LiveRaceStageCompletedSensor(coordinator),
            LiveRaceStageEndSensor(coordinator),
            LiveRaceTrackSensor(coordinator),
            LiveRaceTrackTzSensor(coordinator),
            LiveRaceLatSensor(coordinator),
            LiveRaceLngSensor(coordinator),
            LiveRaceTrackTypeSensor(coordinator),
            LiveRaceLapNumberSensor(coordinator),
            LiveRaceFlagSensor(coordinator),
            LiveRaceCurrentStageSensor(coordinator),
            LiveRaceLapsRemainingSensor(coordinator),
            LiveRaceElapsedTimeSensor(coordinator),
            LiveRaceLengthSensor(coordinator),
        ]
    )

    _LOGGER.info("Created %d sensors", len(entities))
    _LOGGER.debug("Sensor entities: %s", [entity._attr_name for entity in entities])
    async_add_entities(entities)


# Previous Race Sensors
class PreviousRaceBaseSensor(SensorEntity):
    """Base class for previous race sensors."""

    def __init__(self, coordinator, series_name: str):
        self.coordinator = coordinator
        self.series_name = series_name
        self._attr_unique_id = (
            f"previous_race_{series_name.lower().replace(' ', '_')}_{self.sensor_type}"
        )
        self._attr_name = f"Previous Race {series_name} {self.sensor_name}"
        self._attr_icon = self.icon
        self._attr_device_info = get_previous_race_device(series_name)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "previous_race" in self.coordinator.data
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.coordinator.async_add_listener(self._handle_coordinator_update)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        await super().async_will_remove_from_hass()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        data = self.coordinator.data
        if not data or "previous_race" not in data:
            _LOGGER.debug(
                "No previous_race data available for sensor %s", self._attr_name
            )
            return None

        previous_races = data["previous_race"]
        if not previous_races or not isinstance(previous_races, list):
            _LOGGER.debug("No valid previous_race list for sensor %s", self._attr_name)
            return None

        # Find race for this series
        for race in previous_races:
            if isinstance(race, dict) and race.get("series_name") == self.series_name:
                value = self._extract_value(race)
                _LOGGER.debug(
                    "Sensor %s found value: %s for series %s",
                    self._attr_name,
                    value,
                    self.series_name,
                )
                return value

        _LOGGER.debug(
            "No race found for series %s in sensor %s. Available series: %s",
            self.series_name,
            self._attr_name,
            [r.get("series_name") for r in previous_races if isinstance(r, dict)],
        )
        return None

    def _extract_value(self, race_data):
        """Extract value from race data - to be implemented by subclasses."""
        raise NotImplementedError


class PreviousRaceTrackSensor(PreviousRaceBaseSensor):
    """Previous race track sensor."""

    sensor_type = "track"
    sensor_name = "Track"
    icon = "mdi:map-marker"

    def _extract_value(self, race_data):
        return race_data.get("track_name")


class PreviousRaceDateSensor(PreviousRaceBaseSensor):
    """Previous race date sensor."""

    sensor_type = "date"
    sensor_name = "Date"
    icon = "mdi:calendar"
    _attr_device_class = SensorDeviceClass.DATE

    def _extract_value(self, race_data):
        date_str = race_data.get("race_date")
        if date_str:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
        return None


class PreviousRaceScheduledDistanceSensor(PreviousRaceBaseSensor):
    """Previous race scheduled distance sensor."""

    sensor_type = "scheduled_distance"
    sensor_name = "Scheduled Distance"
    icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = "miles"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("scheduled_distance")


class PreviousRaceScheduledLapsSensor(PreviousRaceBaseSensor):
    """Previous race scheduled laps sensor."""

    sensor_type = "scheduled_laps"
    sensor_name = "Scheduled Laps"
    icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("scheduled_laps")


class PreviousRaceCarsSensor(PreviousRaceBaseSensor):
    """Previous race cars sensor."""

    sensor_type = "cars"
    sensor_name = "Cars in Field"
    icon = "mdi:car-multiple"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("cars_in_field")


class PreviousRaceTVSensor(PreviousRaceBaseSensor):
    """Previous race TV broadcaster sensor."""

    sensor_type = "tv"
    sensor_name = "TV Broadcaster"
    icon = "mdi:television"

    def _extract_value(self, race_data):
        return race_data.get("television_broadcaster")


class PreviousRaceRadioSensor(PreviousRaceBaseSensor):
    """Previous race radio broadcaster sensor."""

    sensor_type = "radio"
    sensor_name = "Radio Broadcaster"
    icon = "mdi:radio"

    def _extract_value(self, race_data):
        return race_data.get("radio_broadcaster")


class PreviousRacePlayoffSensor(PreviousRaceBaseSensor):
    """Previous race playoff round sensor."""

    sensor_type = "playoff"
    sensor_name = "Playoff Round"
    icon = "mdi:trophy"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("playoff_round")


class PreviousRaceWinnerSensor(PreviousRaceBaseSensor):
    """Previous race winner sensor."""

    sensor_type = "winner"
    sensor_name = "Winner"
    icon = "mdi:trophy-award"

    def _extract_value(self, race_data):
        return race_data.get("winner")


class PreviousRaceActualDistanceSensor(PreviousRaceBaseSensor):
    """Previous race actual distance sensor."""

    sensor_type = "actual_distance"
    sensor_name = "Actual Distance"
    icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = "miles"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("actual_distance")


class PreviousRaceActualLapsSensor(PreviousRaceBaseSensor):
    """Previous race actual laps sensor."""

    sensor_type = "actual_laps"
    sensor_name = "Actual Laps"
    icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("actual_laps")


# Next Race Sensors
class NextRaceBaseSensor(SensorEntity):
    """Base class for next race sensors."""

    def __init__(self, coordinator, series_name: str):
        self.coordinator = coordinator
        self.series_name = series_name
        self._attr_unique_id = (
            f"next_race_{series_name.lower().replace(' ', '_')}_{self.sensor_type}"
        )
        self._attr_name = f"Next Race {series_name} {self.sensor_name}"
        self._attr_icon = self.icon
        self._attr_device_info = get_next_race_device(series_name)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "next_race" in self.coordinator.data
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.coordinator.async_add_listener(self._handle_coordinator_update)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        await super().async_will_remove_from_hass()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        data = self.coordinator.data
        if not data or "next_race" not in data:
            _LOGGER.debug("No next_race data available for sensor %s", self._attr_name)
            return None

        next_races = data["next_race"]
        if not next_races or not isinstance(next_races, list):
            _LOGGER.debug("No valid next_race list for sensor %s", self._attr_name)
            return None

        # Find race for this series
        for race in next_races:
            if isinstance(race, dict) and race.get("series_name") == self.series_name:
                value = self._extract_value(race)
                _LOGGER.debug(
                    "Sensor %s found value: %s for series %s",
                    self._attr_name,
                    value,
                    self.series_name,
                )
                return value

        _LOGGER.debug(
            "No race found for series %s in sensor %s. Available series: %s",
            self.series_name,
            self._attr_name,
            [r.get("series_name") for r in next_races if isinstance(r, dict)],
        )
        return None

    def _extract_value(self, race_data):
        """Extract value from race data - to be implemented by subclasses."""
        raise NotImplementedError


class NextRaceTrackSensor(NextRaceBaseSensor):
    """Next race track sensor."""

    sensor_type = "track"
    sensor_name = "Track"
    icon = "mdi:map-marker"

    def _extract_value(self, race_data):
        return race_data.get("track_name")


class NextRaceDateSensor(NextRaceBaseSensor):
    """Next race date sensor."""

    sensor_type = "date"
    sensor_name = "Date"
    icon = "mdi:calendar"
    _attr_device_class = SensorDeviceClass.DATE

    def _extract_value(self, race_data):
        date_str = race_data.get("scheduled_date")
        if date_str:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
        return None


class NextRaceScheduledDistanceSensor(NextRaceBaseSensor):
    """Next race scheduled distance sensor."""

    sensor_type = "scheduled_distance"
    sensor_name = "Scheduled Distance"
    icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = "miles"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("scheduled_distance")


class NextRaceScheduledLapsSensor(NextRaceBaseSensor):
    """Next race scheduled laps sensor."""

    sensor_type = "scheduled_laps"
    sensor_name = "Scheduled Laps"
    icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("scheduled_laps")


class NextRaceCarsSensor(NextRaceBaseSensor):
    """Next race cars sensor."""

    sensor_type = "cars"
    sensor_name = "Cars in Field"
    icon = "mdi:car-multiple"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("cars_in_field")


class NextRaceTVSensor(NextRaceBaseSensor):
    """Next race TV broadcaster sensor."""

    sensor_type = "tv"
    sensor_name = "TV Broadcaster"
    icon = "mdi:television"

    def _extract_value(self, race_data):
        return race_data.get("television_broadcaster")


class NextRaceRadioSensor(NextRaceBaseSensor):
    """Next race radio broadcaster sensor."""

    sensor_type = "radio"
    sensor_name = "Radio Broadcaster"
    icon = "mdi:radio"

    def _extract_value(self, race_data):
        return race_data.get("radio_broadcaster")


class NextRacePlayoffSensor(NextRaceBaseSensor):
    """Next race playoff round sensor."""

    sensor_type = "playoff"
    sensor_name = "Playoff Round"
    icon = "mdi:trophy"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("playoff_round")


# Live Race Sensors
class LiveRaceBaseSensor(SensorEntity):
    """Base class for live race sensors."""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_unique_id = f"live_race_{self.sensor_type}"
        self._attr_name = f"Live Race {self.sensor_name}"
        self._attr_icon = self.icon
        # Always use a single live race device
        self._attr_device_info = get_live_race_device("live_race", "Live Race")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and "live_race" in self.coordinator.data
            and isinstance(self.coordinator.data["live_race"], list)
            and len(self.coordinator.data["live_race"]) > 0
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.coordinator.async_add_listener(self._handle_coordinator_update)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        await super().async_will_remove_from_hass()

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        data = self.coordinator.data
        if not data or "live_race" not in data:
            _LOGGER.debug("No live_race data available for sensor %s", self._attr_name)
            return STATE_UNAVAILABLE

        live_races = data["live_race"]
        if not live_races or not isinstance(live_races, list) or len(live_races) == 0:
            _LOGGER.debug(
                "No valid live_race data for sensor %s (empty or invalid)",
                self._attr_name,
            )
            return STATE_UNAVAILABLE

        # Get the first live race (assuming one active race at a time)
        race = live_races[0]
        if not isinstance(race, dict):
            _LOGGER.debug("Live race data is not a dict for sensor %s", self._attr_name)
            return STATE_UNAVAILABLE

        value = self._extract_value(race)
        _LOGGER.debug("Live sensor %s found value: %s", self._attr_name, value)
        return value

    def _extract_value(self, race_data):
        """Extract value from race data - to be implemented by subclasses."""
        raise NotImplementedError


class LiveRaceNameSensor(LiveRaceBaseSensor):
    """Live race name sensor."""

    sensor_type = "name"
    sensor_name = "Name"
    icon = "mdi:flag-checkered"

    def _extract_value(self, race_data):
        return race_data.get("name")


class LiveRaceTypeSensor(LiveRaceBaseSensor):
    """Live race type sensor."""

    sensor_type = "type"
    sensor_name = "Type"
    icon = "mdi:flag-checkered"

    def _extract_value(self, race_data):
        return race_data.get("type")


class LiveRaceStartTimeSensor(LiveRaceBaseSensor):
    """Live race start time sensor."""

    sensor_type = "start_time"
    sensor_name = "Start Time"
    icon = "mdi:clock-start"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def _extract_value(self, race_data):
        time_str = race_data.get("start_time")
        if time_str:
            return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        return None


class LiveRaceEndTimeSensor(LiveRaceBaseSensor):
    """Live race end time sensor."""

    sensor_type = "end_time"
    sensor_name = "End Time"
    icon = "mdi:clock-end"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def _extract_value(self, race_data):
        time_str = race_data.get("end_time")
        if time_str:
            return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        return None


class LiveRaceTotalLapsSensor(LiveRaceBaseSensor):
    """Live race total laps sensor."""

    sensor_type = "total_laps"
    sensor_name = "Total Laps"
    icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("total_laps")


class LiveRaceActualLapsSensor(LiveRaceBaseSensor):
    """Live race actual laps sensor."""

    sensor_type = "actual_laps"
    sensor_name = "Actual Laps"
    icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("actual_laps")


class LiveRaceScheduledLapsSensor(LiveRaceBaseSensor):
    """Live race scheduled laps sensor."""

    sensor_type = "scheduled_laps"
    sensor_name = "Scheduled Laps"
    icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("scheduled_laps")


class LiveRaceScheduledDistanceSensor(LiveRaceBaseSensor):
    """Live race scheduled distance sensor."""

    sensor_type = "scheduled_distance"
    sensor_name = "Scheduled Distance"
    icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = "miles"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("scheduled_distance")


class LiveRaceStageLapsSensor(LiveRaceBaseSensor):
    """Live race stage laps sensor."""

    sensor_type = "stage_laps"
    sensor_name = "Stage Laps"
    icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("stage_laps")


class LiveRaceStageStartSensor(LiveRaceBaseSensor):
    """Live race stage start sensor."""

    sensor_type = "stage_start"
    sensor_name = "Stage Start"
    icon = "mdi:flag-checkered"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("stage_start")


class LiveRaceStageRemainingSensor(LiveRaceBaseSensor):
    """Live race stage remaining sensor."""

    sensor_type = "stage_remaining"
    sensor_name = "Stage Remaining"
    icon = "mdi:flag-checkered"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("stage_remaining")


class LiveRaceStageCompletedSensor(LiveRaceBaseSensor):
    """Live race stage completed sensor."""

    sensor_type = "stage_completed"
    sensor_name = "Stage Completed"
    icon = "mdi:flag-checkered"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("stage_completed")


class LiveRaceStageEndSensor(LiveRaceBaseSensor):
    """Live race stage end sensor."""

    sensor_type = "stage_end"
    sensor_name = "Stage End"
    icon = "mdi:flag-checkered"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("stage_end")


class LiveRaceTrackSensor(LiveRaceBaseSensor):
    """Live race track sensor."""

    sensor_type = "track"
    sensor_name = "Track"
    icon = "mdi:map-marker"

    def _extract_value(self, race_data):
        return race_data.get("track")


class LiveRaceTrackTzSensor(LiveRaceBaseSensor):
    """Live race track timezone sensor."""

    sensor_type = "track_tz"
    sensor_name = "Track Timezone"
    icon = "mdi:clock-outline"

    def _extract_value(self, race_data):
        return race_data.get("track_tz")


class LiveRaceLatSensor(LiveRaceBaseSensor):
    """Live race latitude sensor."""

    sensor_type = "lat"
    sensor_name = "Latitude"
    icon = "mdi:map-marker"
    _attr_native_unit_of_measurement = "°"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("lat")


class LiveRaceLngSensor(LiveRaceBaseSensor):
    """Live race longitude sensor."""

    sensor_type = "lng"
    sensor_name = "Longitude"
    icon = "mdi:map-marker"
    _attr_native_unit_of_measurement = "°"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("lng")


class LiveRaceTrackTypeSensor(LiveRaceBaseSensor):
    """Live race track type sensor."""

    sensor_type = "track_type"
    sensor_name = "Track Type"
    icon = "mdi:map-marker"

    def _extract_value(self, race_data):
        return race_data.get("track_type")


class LiveRaceLapNumberSensor(LiveRaceBaseSensor):
    """Live race lap number sensor."""

    sensor_type = "lap_number"
    sensor_name = "Lap Number"
    icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("lap_number")


class LiveRaceFlagSensor(LiveRaceBaseSensor):
    """Live race flag sensor."""

    sensor_type = "flag"
    sensor_name = "Flag"
    icon = "mdi:flag"

    def _extract_value(self, race_data):
        flag_code = race_data.get("flag")
        return FLAG_MAPPING.get(flag_code, f"Unknown ({flag_code})")


class LiveRaceCurrentStageSensor(LiveRaceBaseSensor):
    """Live race current stage sensor."""

    sensor_type = "current_stage"
    sensor_name = "Current Stage"
    icon = "mdi:flag-checkered"

    def _extract_value(self, race_data):
        return race_data.get("current_stage")


class LiveRaceLapsRemainingSensor(LiveRaceBaseSensor):
    """Live race laps remaining sensor."""

    sensor_type = "laps_remaining"
    sensor_name = "Laps Remaining"
    icon = "mdi:counter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("laps_remaining")


class LiveRaceElapsedTimeSensor(LiveRaceBaseSensor):
    """Live race elapsed time sensor."""

    sensor_type = "elapsed_time"
    sensor_name = "Elapsed Time"
    icon = "mdi:timer"
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("elapsed_time")


class LiveRaceLengthSensor(LiveRaceBaseSensor):
    """Live race length sensor."""

    sensor_type = "length"
    sensor_name = "Length"
    icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = "miles"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def _extract_value(self, race_data):
        return race_data.get("scheduled_distance")
