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
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_ROOM_NAME): str,
    vol.Required(CONF_LIGHT_ENTITY): selector.EntitySelector(
        selector.EntitySelectorConfig(domain="light")
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
})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Lux Control."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Validate the input
            errors = await self._async_validate_input(user_input)
            
            if not errors:
                # Create entry
                return self.async_create_entry(
                    title=f"Smart Lux Control - {user_input[CONF_ROOM_NAME]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _async_validate_input(self, user_input: Dict[str, Any]) -> Dict[str, str]:
        """Validate the user input."""
        errors = {}

        # Check if entities exist
        light_entity = user_input[CONF_LIGHT_ENTITY]
        lux_sensor = user_input[CONF_LUX_SENSOR]
        motion_sensor = user_input[CONF_MOTION_SENSOR]
        home_mode_select = user_input.get(CONF_HOME_MODE_SELECT)

        if not self.hass.states.get(light_entity):
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
                "deviation_margin",
                default=coordinator.deviation_margin if coordinator else 15,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
            vol.Optional(
                "learning_rate",
                default=coordinator.learning_rate if coordinator else 0.1,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.01, max=1.0)),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema) 