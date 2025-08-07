"""The Galaxie integration."""

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .coordinator import GalaxieDataCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Galaxie from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create aiohttp session
    session = aiohttp.ClientSession()

    # Create coordinator
    coordinator = GalaxieDataCoordinator(hass, session)

    # Store coordinator in hass data
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "session": session,
    }

    # Start coordinator
    await coordinator.async_config_entry_first_refresh()

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Clean up session
        session = hass.data[DOMAIN][entry.entry_id]["session"]
        await session.close()

        # Remove from hass data
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
