"""Test configuration for the Galaxie integration."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.galaxie.const import DOMAIN


@pytest.fixture(autouse=True)
async def setup_component(hass: HomeAssistant):
    """Set up the Galaxie component."""
    await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()
