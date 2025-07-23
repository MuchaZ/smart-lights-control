"""Switch platform for Smart Lux Control."""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Lux Control switches."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        SmartModeSwitch(coordinator),
        AdaptiveLearningSwitch(coordinator),
    ]
    
    async_add_entities(entities)


class SmartLuxBaseSwitch(SwitchEntity):
    """Base class for Smart Lux Control switches."""

    def __init__(self, coordinator, switch_type: str, name_suffix: str) -> None:
        """Initialize the switch."""
        self._coordinator = coordinator
        self._switch_type = switch_type
        
        self._attr_name = f"{coordinator.room_name} {name_suffix}"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.room_name}_{switch_type}"

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._coordinator.room_name)},
            "name": f"Smart Lux Control - {self._coordinator.room_name}",
            "manufacturer": "Smart Lux Control",
            "model": "Smart Light Controller",
            "sw_version": "1.0.0",
        }


class SmartModeSwitch(SmartLuxBaseSwitch):
    """Switch to enable/disable smart mode."""

    def __init__(self, coordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "smart_mode", "Smart Mode")
        self._attr_icon = "mdi:brain"

    @property
    def is_on(self) -> bool:
        """Return if smart mode is enabled."""
        return (
            self._coordinator.regression_quality >= self._coordinator.min_regression_quality
            and self._coordinator.sample_count >= 5
        )

    @property
    def available(self) -> bool:
        """Return if the switch is available."""
        return self._coordinator.sample_count >= 5

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on smart mode by lowering quality threshold."""
        if self._coordinator.sample_count >= 5:
            self._coordinator.min_regression_quality = max(0.3, self._coordinator.regression_quality - 0.1)
            await self._coordinator._async_save_data()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off smart mode by raising quality threshold."""
        self._coordinator.min_regression_quality = 0.9  # Very high threshold
        await self._coordinator._async_save_data()

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        return {
            "current_quality": round(self._coordinator.regression_quality, 3),
            "required_quality": self._coordinator.min_regression_quality,
            "sample_count": self._coordinator.sample_count,
        }


class AdaptiveLearningSwitch(SmartLuxBaseSwitch):
    """Switch to enable/disable adaptive learning."""

    def __init__(self, coordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, "adaptive_learning", "Adaptive Learning")
        self._attr_icon = "mdi:school"
        self._adaptive_learning_enabled = True

    @property
    def is_on(self) -> bool:
        """Return if adaptive learning is enabled."""
        return self._adaptive_learning_enabled

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on adaptive learning."""
        self._adaptive_learning_enabled = True
        # Run adaptive learning immediately
        if self._coordinator.sample_count >= 15:
            await self._coordinator.async_adaptive_learning()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off adaptive learning."""
        self._adaptive_learning_enabled = False

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        return {
            "learning_rate": self._coordinator.learning_rate,
            "samples_needed": max(0, 15 - self._coordinator.sample_count),
        } 