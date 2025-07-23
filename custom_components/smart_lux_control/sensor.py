"""Sensor platform for Smart Lux Control."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Smart Lux Control sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(SmartLuxSensor(coordinator, sensor_type))
    
    async_add_entities(entities)


class SmartLuxSensor(SensorEntity):
    """Smart Lux Control sensor."""

    def __init__(self, coordinator, sensor_type: str) -> None:
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._sensor_type = sensor_type
        self._config = SENSOR_TYPES[sensor_type]
        
        self._attr_name = f"{coordinator.room_name} {self._config['name']}"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.room_name}_{sensor_type}"
        self._attr_unit_of_measurement = self._config["unit"]
        self._attr_icon = self._config["icon"]
        self._attr_device_class = self._config["device_class"]

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

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self._sensor_type == "regression_quality":
            return round(self._coordinator.regression_quality, 3)
        
        elif self._sensor_type == "sample_count":
            return self._coordinator.sample_count
        
        elif self._sensor_type == "smart_mode_status":
            if self._coordinator.is_smart_mode_active:
                return "Smart Active"
            elif self._coordinator.sample_count >= 5:
                return "Fallback Mode"
            else:
                return "Learning Mode"
        
        elif self._sensor_type == "predicted_lux":
            predicted = self._coordinator.predicted_lux
            return round(predicted, 1) if predicted is not None else None
        
        elif self._sensor_type == "average_error":
            return self._calculate_average_error()
        
        elif self._sensor_type == "target_lux":
            target = self._coordinator.current_target_lux
            return round(target, 1) if target is not None else self._coordinator.get_target_lux()
        
        elif self._sensor_type == "automation_status":
            if not self._coordinator.auto_control_enabled:
                return "Disabled"
            elif self._coordinator.should_lights_be_on():
                return "Active"
            else:
                return "Standby"
        
        elif self._sensor_type == "last_automation_action":
            return self._coordinator.last_automation_action or "None"
        
        elif self._sensor_type == "motion_timer":
            if not self._coordinator.last_motion_time:
                return None
            
            from homeassistant.util import dt as dt_util
            now = dt_util.now()
            time_since = (now - self._coordinator.last_motion_time).total_seconds() / 60
            return round(self._coordinator.keep_on_minutes - time_since, 1)
        
        return None

    def _calculate_average_error(self) -> Optional[float]:
        """Calculate average prediction error."""
        if len(self._coordinator.samples) < 5:
            return None
        
        brightness_vals, lux_vals = self._coordinator._filter_samples()
        if len(brightness_vals) < 5:
            return None
        
        errors = []
        for brightness, lux in zip(brightness_vals[-20:], lux_vals[-20:]):  # Last 20 samples
            predicted_lux = self._coordinator.regression_a * brightness + self._coordinator.regression_b
            error = abs(lux - predicted_lux)
            errors.append(error)
        
        return round(sum(errors) / len(errors), 1) if errors else None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        attrs = {}
        
        if self._sensor_type == "regression_quality":
            attrs.update({
                "regression_a": round(self._coordinator.regression_a, 4),
                "regression_b": round(self._coordinator.regression_b, 1),
                "quality_status": self._get_quality_status(),
            })
        
        elif self._sensor_type == "smart_mode_status":
            attrs.update({
                "regression_quality": round(self._coordinator.regression_quality, 3),
                "min_required_quality": self._coordinator.min_regression_quality,
                "can_use_smart_mode": self._coordinator.is_smart_mode_active,
            })
        
        elif self._sensor_type == "sample_count":
            attrs.update({
                "max_samples": self._coordinator.max_samples,
                "last_regression_update": self._get_last_sample_time(),
            })
        
        elif self._sensor_type == "automation_status":
            attrs.update({
                "motion_detected": self._coordinator.should_lights_be_on(),
                "lights_controlled": self._coordinator.lights_controlled_by_automation,
                "check_interval": self._coordinator.check_interval,
            })
        
        elif self._sensor_type == "target_lux":
            # Get home mode if available
            mode = "normal"
            if self._coordinator.home_mode_select:
                mode_state = self._coordinator.hass.states.get(self._coordinator.home_mode_select)
                if mode_state:
                    mode = mode_state.state
            
            attrs.update({
                "home_mode": mode,
                "lux_settings": self._coordinator.lux_settings,
                "buffer_minutes": self._coordinator.buffer_minutes,
            })
        
        elif self._sensor_type == "motion_timer":
            motion_state = self._coordinator.hass.states.get(self._coordinator.motion_sensor)
            attrs.update({
                "keep_on_minutes": self._coordinator.keep_on_minutes,
                "motion_currently_detected": motion_state.state == "on" if motion_state else False,
                "last_motion_time": self._coordinator.last_motion_time.isoformat() if self._coordinator.last_motion_time else None,
            })
        
        return attrs

    def _get_quality_status(self) -> str:
        """Get quality status description."""
        quality = self._coordinator.regression_quality
        if quality >= 0.8:
            return "Excellent"
        elif quality >= 0.6:
            return "Good"
        elif quality >= 0.4:
            return "Fair"
        else:
            return "Poor"

    def _get_last_sample_time(self) -> Optional[str]:
        """Get timestamp of last sample."""
        if not self._coordinator.samples:
            return None
        
        return self._coordinator.samples[-1][2].isoformat()

    async def async_update(self) -> None:
        """Update the sensor."""
        # The coordinator handles the data updates
        pass 