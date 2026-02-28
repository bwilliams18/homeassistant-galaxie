"""Device for Galaxie integration."""

from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    get_live_race_device_info,
    get_live_status_device_info,
    get_next_race_device_info,
    get_previous_race_device_info,
)


def get_previous_race_device(series_name: str, sw_version: str = "1.0.0") -> DeviceInfo:
    """Get device info for previous race device."""
    device_info = get_previous_race_device_info(series_name, sw_version=sw_version)
    return DeviceInfo(
        identifiers=device_info["identifiers"],
        name=device_info["name"],
        manufacturer=device_info["manufacturer"],
        model=device_info["model"],
        sw_version=device_info["sw_version"],
    )


def get_next_race_device(series_name: str, sw_version: str = "1.0.0") -> DeviceInfo:
    """Get device info for next race device."""
    device_info = get_next_race_device_info(series_name, sw_version=sw_version)
    return DeviceInfo(
        identifiers=device_info["identifiers"],
        name=device_info["name"],
        manufacturer=device_info["manufacturer"],
        model=device_info["model"],
        sw_version=device_info["sw_version"],
    )


def get_live_race_device(
    run_id: str, run_name: str, sw_version: str = "1.0.0"
) -> DeviceInfo:
    """Get device info for live race device."""
    device_info = get_live_race_device_info(run_id, run_name, sw_version=sw_version)
    return DeviceInfo(
        identifiers=device_info["identifiers"],
        name=device_info["name"],
        manufacturer=device_info["manufacturer"],
        model=device_info["model"],
        sw_version=device_info["sw_version"],
    )


def get_live_status_device(sw_version: str = "1.0.0") -> DeviceInfo:
    """Get device info for live status device."""
    device_info = get_live_status_device_info(sw_version=sw_version)
    return DeviceInfo(
        identifiers=device_info["identifiers"],
        name=device_info["name"],
        manufacturer=device_info["manufacturer"],
        model=device_info["model"],
        sw_version=device_info["sw_version"],
    )
