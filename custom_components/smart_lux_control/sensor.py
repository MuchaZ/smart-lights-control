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
    try:
        coordinator = hass.data[DOMAIN][entry.entry_id]
        
        entities = []
        for sensor_type in SENSOR_TYPES:
            entities.append(SmartLuxSensor(coordinator, sensor_type))
        
        async_add_entities(entities)
        _LOGGER.info("Successfully set up %d sensors for %s", len(entities), entry.title)
        
    except Exception as err:
        _LOGGER.error("Error setting up sensors for %s: %s", entry.title, err)
        raise


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
            if predicted is not None:
                return round(predicted, 1)
            # If can't predict, show current sensor reading instead
            lux_state = self._coordinator.hass.states.get(self._coordinator.lux_sensor)
            if lux_state and lux_state.state not in ("unknown", "unavailable"):
                try:
                    return round(float(lux_state.state), 1)
                except ValueError:
                    pass
            return None
        
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
            action = self._coordinator.last_automation_action or "None"
            
            # Show human-readable cooldown status
            if action.startswith("cooldown_wait_"):
                seconds = action.split("_")[-1].replace("s", "")
                try:
                    return f"Cooldown ({float(seconds):.1f}s remaining)"
                except ValueError:
                    return action
            return action
        
        elif self._sensor_type == "motion_timer":
            if not self._coordinator.last_motion_time:
                return None
            
            from homeassistant.util import dt as dt_util
            now = dt_util.now()
            time_since = (now - self._coordinator.last_motion_time).total_seconds() / 60
            return round(self._coordinator.keep_on_minutes - time_since, 1)
        
        elif self._sensor_type == "motion_status":
            motion_state = self._coordinator.hass.states.get(self._coordinator.motion_sensor)
            if not motion_state:
                return "Sensor Unavailable"
            
            if motion_state.state == "on":
                return "Motion Detected"
            elif self._coordinator.should_lights_be_on():
                return "In Timer Period"
            else:
                return "No Motion"
        
        elif self._sensor_type == "lights_status":
            lights_on = 0
            lights_total = len(self._coordinator.light_entities)
            avg_brightness = 0
            
            for light_entity in self._coordinator.light_entities:
                light_state = self._coordinator.hass.states.get(light_entity)
                if light_state and light_state.state == "on":
                    lights_on += 1
                    brightness = light_state.attributes.get("brightness", 255)
                    avg_brightness += brightness
            
            if lights_on == 0:
                return "All Off"
            elif lights_on == lights_total:
                avg_brightness = int(avg_brightness / lights_on)
                return f"All On ({avg_brightness}/255)"
            else:
                avg_brightness = int(avg_brightness / lights_on) if lights_on > 0 else 0
                return f"{lights_on}/{lights_total} On ({avg_brightness}/255)"
        
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
        
        elif self._sensor_type == "predicted_lux":
            # Additional info for predicted lux sensor
            lights_on = sum(1 for light_entity in self._coordinator.light_entities 
                          if self._coordinator.hass.states.get(light_entity) 
                          and self._coordinator.hass.states.get(light_entity).state == "on")
            
            attrs.update({
                "lights_on_count": lights_on,
                "total_lights": len(self._coordinator.light_entities),
                "regression_ready": self._coordinator.regression_quality >= 0.1,
                "learning_phase": self._coordinator.sample_count < 10,
                "fallback_to_sensor": self._coordinator.predicted_lux is None,
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
        
        elif self._sensor_type == "motion_status":
            motion_state = self._coordinator.hass.states.get(self._coordinator.motion_sensor)
            from homeassistant.util import dt as dt_util
            now = dt_util.now()
            
            attrs.update({
                "motion_sensor_entity": self._coordinator.motion_sensor,
                "motion_sensor_state": motion_state.state if motion_state else "unknown",
                "should_lights_be_on": self._coordinator.should_lights_be_on(),
                "auto_control_enabled": self._coordinator.auto_control_enabled,
                "last_motion_trigger": self._coordinator.last_motion_time.isoformat() if self._coordinator.last_motion_time else None,
                "time_since_motion": round((now - self._coordinator.last_motion_time).total_seconds() / 60, 1) if self._coordinator.last_motion_time else None,
            })
        
        elif self._sensor_type == "lights_status":
            lights_info = []
            
            for light_entity in self._coordinator.light_entities:
                light_state = self._coordinator.hass.states.get(light_entity)
                if light_state:
                    brightness = light_state.attributes.get("brightness", 255) if light_state.state == "on" else 0
                    lights_info.append({
                        "entity_id": light_entity,
                        "state": light_state.state,
                        "brightness": brightness,
                        "friendly_name": light_state.attributes.get("friendly_name", light_entity)
                    })
                else:
                    lights_info.append({
                        "entity_id": light_entity,
                        "state": "unavailable",
                        "brightness": 0,
                        "friendly_name": light_entity
                    })
            
            attrs.update({
                "controlled_by_automation": self._coordinator.lights_controlled_by_automation,
                "light_entities": self._coordinator.light_entities,
                "lights_detail": lights_info,
                "auto_control_enabled": self._coordinator.auto_control_enabled,
                "last_action": self._coordinator.last_automation_action,
                "brightness_cooldown_seconds": self._coordinator.brightness_cooldown_seconds,
                "last_brightness_change": self._coordinator.last_brightness_change_time.isoformat() if self._coordinator.last_brightness_change_time else None,
                "last_brightness_value": self._coordinator.last_brightness_change_value,
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