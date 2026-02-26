"""Constants for the Galaxie integration."""

from datetime import timedelta

DOMAIN = "galaxie"
DEFAULT_NAME = "Galaxie NASCAR"

# Series mapping - updated to match actual API response
SERIES_MAPPING = {
    1: "NASCAR Cup Series",
    2: "NASCAR Xfinity Series",
    3: "NASCAR Craftsman Truck Series",
}

# Flag mapping
FLAG_MAPPING = {
    1: "Green",
    2: "Yellow",
    3: "Red",
    4: "Checkered",
    8: "Pre Race",
    9: "Checkered Flag",
}

# API Configuration
BASE_URL = "https://galaxie.app"
API_ENDPOINTS = {
    "previous_race": "/api/previous_race/",
    "next_race": "/api/next_race/",
    "live": "/api/live/",
    "config": "/api/config/",
}

# Update intervals
UPDATE_INTERVAL_PREVIOUS_NEXT = timedelta(minutes=15)
UPDATE_INTERVAL_LIVE = timedelta(seconds=15)
UPDATE_INTERVAL_CONFIG = timedelta(hours=1)

# Device classes
DEVICE_CLASS_LIVE_STATUS = "connectivity"


# Device info templates
def get_previous_race_device_info(series_name: str, sw_version: str = "1.0.0"):
    """Get device info for previous race device."""
    return {
        "identifiers": {
            (DOMAIN, f"previous_race_{series_name.lower().replace(' ', '_')}")
        },
        "name": f"Previous Race {series_name}",
        "manufacturer": "Galaxie",
        "model": "NASCAR Previous Race",
        "sw_version": sw_version,
    }


def get_next_race_device_info(series_name: str, sw_version: str = "1.0.0"):
    """Get device info for next race device."""
    return {
        "identifiers": {(DOMAIN, f"next_race_{series_name.lower().replace(' ', '_')}")},
        "name": f"Next Race {series_name}",
        "manufacturer": "Galaxie",
        "model": "NASCAR Next Race",
        "sw_version": sw_version,
    }


def get_live_race_device_info(run_id: str, run_name: str, sw_version: str = "1.0.0"):
    """Get device info for live race device."""
    return {
        "identifiers": {(DOMAIN, f"live_race_{run_id}")},
        "name": f"Live Race {run_name}",
        "manufacturer": "Galaxie",
        "model": "NASCAR Live Race",
        "sw_version": sw_version,
    }


def get_live_status_device_info(sw_version: str = "1.0.0"):
    """Get device info for live status device."""
    return {
        "identifiers": {(DOMAIN, "live_status")},
        "name": "Galaxie Live Status",
        "manufacturer": "Galaxie",
        "model": "NASCAR Live Status",
        "sw_version": sw_version,
    }
