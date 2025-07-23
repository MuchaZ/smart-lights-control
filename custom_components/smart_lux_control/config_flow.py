"""Config flow for Smart Lux Control integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_ROOM_NAME,
    CONF_LIGHT_ENTITY,
    CONF_LUX_SENSOR,
    CONF_MOTION_SENSOR,
    CONF_HOME_MODE_SELECT,
    CONF_LUX_NORMAL_DAY,
    CONF_LUX_NORMAL_NIGHT,
    CONF_LUX_MODE_NOC,
    CONF_LUX_MODE_IMPREZA,
    CONF_LUX_MODE_RELAKS,
    CONF_LUX_MODE_FILM,
    CONF_LUX_MODE_SPRZATANIE,
    CONF_LUX_MODE_DZIECKO_SPI,
    CONF_KEEP_ON_MINUTES,
    CONF_BUFFER_MINUTES,
    CONF_DEVIATION_MARGIN,
    CONF_CHECK_INTERVAL,
    CONF_AUTO_CONTROL_ENABLED,
)

_LOGGER = logging.getLogger(__name__)

# Step 1: Basic Configuration  
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_ROOM_NAME, default="salon"): str,
    vol.Required(CONF_LIGHT_ENTITY): selector.EntitySelector(
        selector.EntitySelectorConfig(domain="light", multiple=True)
    ),
    vol.Required(CONF_LUX_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor", device_class="illuminance")
    ),
    vol.Required(CONF_MOTION_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(domain="binary_sensor", device_class="motion")
    ),
    vol.Optional(CONF_HOME_MODE_SELECT): selector.EntitySelector(
        selector.EntitySelectorConfig(domain="input_select")
    ),
    vol.Optional(CONF_AUTO_CONTROL_ENABLED, default=True): bool,
})

# Step 2: Lux Settings
STEP_LUX_DATA_SCHEMA = vol.Schema({
    vol.Optional(CONF_LUX_NORMAL_DAY, default=400): vol.All(vol.Coerce(int), vol.Range(min=50, max=2000)),
    vol.Optional(CONF_LUX_NORMAL_NIGHT, default=150): vol.All(vol.Coerce(int), vol.Range(min=10, max=1000)),
    vol.Optional(CONF_LUX_MODE_NOC, default=10): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
    vol.Optional(CONF_LUX_MODE_IMPREZA, default=500): vol.All(vol.Coerce(int), vol.Range(min=100, max=2000)),
    vol.Optional(CONF_LUX_MODE_RELAKS, default=120): vol.All(vol.Coerce(int), vol.Range(min=20, max=1000)),
    vol.Optional(CONF_LUX_MODE_FILM, default=60): vol.All(vol.Coerce(int), vol.Range(min=5, max=500)),
    vol.Optional(CONF_LUX_MODE_SPRZATANIE, default=600): vol.All(vol.Coerce(int), vol.Range(min=200, max=2000)),
    vol.Optional(CONF_LUX_MODE_DZIECKO_SPI, default=8): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
})

# Step 3: Timing Settings  
STEP_TIMING_DATA_SCHEMA = vol.Schema({
    vol.Optional(CONF_KEEP_ON_MINUTES, default=5): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
    vol.Optional(CONF_BUFFER_MINUTES, default=30): vol.All(vol.Coerce(int), vol.Range(min=0, max=90)),
    vol.Optional(CONF_DEVIATION_MARGIN, default=15): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
    vol.Optional(CONF_CHECK_INTERVAL, default=30): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Lux Control."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self.data = {}

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Validate the input
            errors = await self._async_validate_basic_input(user_input)
            
            if not errors:
                self.data.update(user_input)
                return await self.async_step_lux_settings()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_lux_settings(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the lux settings step."""
        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_timing_settings()

        return self.async_show_form(
            step_id="lux_settings",
            data_schema=STEP_LUX_DATA_SCHEMA,
            description_placeholders={
                "room_name": self.data[CONF_ROOM_NAME]
            }
        )

    async def async_step_timing_settings(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the timing settings step."""
        if user_input is not None:
            self.data.update(user_input)
            
            # Create entry
            return self.async_create_entry(
                title=f"Smart Lux Control - {self.data[CONF_ROOM_NAME]}",
                data=self.data,
            )

        return self.async_show_form(
            step_id="timing_settings",
            data_schema=STEP_TIMING_DATA_SCHEMA,
            description_placeholders={
                "room_name": self.data[CONF_ROOM_NAME]
            }
        )

    async def _async_validate_basic_input(self, user_input: Dict[str, Any]) -> Dict[str, str]:
        """Validate the basic user input."""
        errors = {}

        # Check if entities exist
        light_entities = user_input[CONF_LIGHT_ENTITY]
        lux_sensor = user_input[CONF_LUX_SENSOR]
        motion_sensor = user_input[CONF_MOTION_SENSOR]
        home_mode_select = user_input.get(CONF_HOME_MODE_SELECT)

        # Validate light entities (now can be list from selector)
        if isinstance(light_entities, list):
            for light_entity in light_entities:
                if not self.hass.states.get(light_entity):
                    errors[CONF_LIGHT_ENTITY] = "entity_not_found"
                    break
        elif isinstance(light_entities, str):
            if not self.hass.states.get(light_entities):
                errors[CONF_LIGHT_ENTITY] = "entity_not_found"

        if not self.hass.states.get(lux_sensor):
            errors[CONF_LUX_SENSOR] = "entity_not_found"

        if not self.hass.states.get(motion_sensor):
            errors[CONF_MOTION_SENSOR] = "entity_not_found"

        if home_mode_select and not self.hass.states.get(home_mode_select):
            errors[CONF_HOME_MODE_SELECT] = "entity_not_found"

        # Check if room name is unique
        room_name = user_input[CONF_ROOM_NAME]
        for entry in self._async_current_entries():
            if entry.data.get(CONF_ROOM_NAME) == room_name:
                errors[CONF_ROOM_NAME] = "room_already_configured"
                break

        return errors

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Smart Lux Control."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current coordinator
        coordinator = self.hass.data[DOMAIN].get(self.config_entry.entry_id)
        
        options_schema = vol.Schema({
            vol.Optional(
                "min_regression_quality",
                default=coordinator.min_regression_quality if coordinator else 0.5,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=1.0)),
            vol.Optional(
                "max_brightness_change",
                default=coordinator.max_brightness_change if coordinator else 50,
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=100)),
            vol.Optional(
                "learning_rate",
                default=coordinator.learning_rate if coordinator else 0.1,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.01, max=1.0)),
            vol.Optional(
                CONF_AUTO_CONTROL_ENABLED,
                default=self.config_entry.data.get(CONF_AUTO_CONTROL_ENABLED, True),
            ): bool,
        })

        return self.async_show_form(step_id="init", data_schema=options_schema) 