"""Smart Lux Control integration for Home Assistant."""
import asyncio
import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    PLATFORMS,
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
    DEFAULT_MIN_REGRESSION_QUALITY,
    DEFAULT_MAX_BRIGHTNESS_CHANGE,
    DEFAULT_DEVIATION_MARGIN,
    DEFAULT_LEARNING_RATE,
    LUX_MODES,
    SERVICE_CALCULATE_REGRESSION,
    SERVICE_CLEAR_SAMPLES,
    SERVICE_ADD_SAMPLE,
    SERVICE_ADAPTIVE_LEARNING,
    STORAGE_VERSION,
    EVENT_REGRESSION_UPDATED,
    EVENT_SMART_MODE_CHANGED,
    EVENT_SAMPLE_ADDED,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Smart Lux Control from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create coordinator for this room
    coordinator = SmartLuxCoordinator(hass, entry)
    await coordinator.async_setup()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    await async_setup_services(hass)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Smart Lux Control config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_unload()
    
    return unload_ok


async def async_setup_services(hass: HomeAssistant) -> None:
    """Setup services for Smart Lux Control."""
    
    async def calculate_regression_service(call: ServiceCall) -> None:
        """Service to calculate regression for a room."""
        room_name = call.data.get("room_name")
        if not room_name:
            _LOGGER.error("Room name is required for calculate_regression service")
            return
            
        coordinator = _get_coordinator_by_room(hass, room_name)
        if coordinator:
            await coordinator.async_calculate_regression()
    
    async def clear_samples_service(call: ServiceCall) -> None:
        """Service to clear samples for a room."""
        room_name = call.data.get("room_name")
        if not room_name:
            _LOGGER.error("Room name is required for clear_samples service")
            return
            
        coordinator = _get_coordinator_by_room(hass, room_name)
        if coordinator:
            await coordinator.async_clear_samples()
    
    async def add_sample_service(call: ServiceCall) -> None:
        """Service to manually add a sample."""
        room_name = call.data.get("room_name")
        brightness = call.data.get("brightness")
        lux = call.data.get("lux")
        
        if not all([room_name, brightness is not None, lux is not None]):
            _LOGGER.error("Room name, brightness, and lux are required for add_sample service")
            return
            
        coordinator = _get_coordinator_by_room(hass, room_name)
        if coordinator:
            await coordinator.async_add_sample(brightness, lux)
    
    async def adaptive_learning_service(call: ServiceCall) -> None:
        """Service to run adaptive learning."""
        room_name = call.data.get("room_name")
        if not room_name:
            _LOGGER.error("Room name is required for adaptive_learning service")
            return
            
        coordinator = _get_coordinator_by_room(hass, room_name)
        if coordinator:
            await coordinator.async_adaptive_learning()
    
    async def calculate_target_brightness_service(call: ServiceCall) -> None:
        """Service to calculate target brightness for desired lux level."""
        room_name = call.data.get("room_name")
        target_lux = call.data.get("target_lux")
        current_brightness = call.data.get("current_brightness", 255)
        
        if not all([room_name, target_lux is not None]):
            _LOGGER.error("Room name and target_lux are required for calculate_target_brightness service")
            return
            
        coordinator = _get_coordinator_by_room(hass, room_name)
        if coordinator:
            brightness = coordinator.calculate_target_brightness(target_lux, current_brightness)
            return {"brightness": brightness}
    
    # Register services
    hass.services.async_register(DOMAIN, SERVICE_CALCULATE_REGRESSION, calculate_regression_service)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_SAMPLES, clear_samples_service)
    hass.services.async_register(DOMAIN, SERVICE_ADD_SAMPLE, add_sample_service)
    hass.services.async_register(DOMAIN, SERVICE_ADAPTIVE_LEARNING, adaptive_learning_service)
    hass.services.async_register(DOMAIN, "calculate_target_brightness", calculate_target_brightness_service)


def _get_coordinator_by_room(hass: HomeAssistant, room_name: str) -> Optional["SmartLuxCoordinator"]:
    """Get coordinator by room name."""
    for coordinator in hass.data[DOMAIN].values():
        if isinstance(coordinator, SmartLuxCoordinator) and coordinator.room_name == room_name:
            return coordinator
    return None


class SmartLuxCoordinator:
    """Coordinator for Smart Lux Control."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.room_name = entry.data[CONF_ROOM_NAME]
        
        # Entity IDs - support multiple lights from selector
        light_entity_data = entry.data[CONF_LIGHT_ENTITY]
        if isinstance(light_entity_data, list):
            self.light_entities = light_entity_data
        elif isinstance(light_entity_data, str):
            # Single entity (fallback)
            self.light_entities = [light_entity_data]
        else:
            self.light_entities = [str(light_entity_data)]
        self.lux_sensor = entry.data[CONF_LUX_SENSOR]
        self.motion_sensor = entry.data[CONF_MOTION_SENSOR]
        self.home_mode_select = entry.data.get(CONF_HOME_MODE_SELECT)
        
        # Lux configuration for different modes
        self.lux_settings = {
            "normal_day": entry.data.get(CONF_LUX_NORMAL_DAY, 400),
            "normal_night": entry.data.get(CONF_LUX_NORMAL_NIGHT, 150),
            "noc": entry.data.get(CONF_LUX_MODE_NOC, 10),
            "impreza": entry.data.get(CONF_LUX_MODE_IMPREZA, 500),
            "relaks": entry.data.get(CONF_LUX_MODE_RELAKS, 120),
            "film": entry.data.get(CONF_LUX_MODE_FILM, 60),
            "sprzatanie": entry.data.get(CONF_LUX_MODE_SPRZATANIE, 600),
            "dziecko_spi": entry.data.get(CONF_LUX_MODE_DZIECKO_SPI, 8),
        }
        
        # Timing settings
        self.keep_on_minutes = entry.data.get(CONF_KEEP_ON_MINUTES, 5)
        self.buffer_minutes = entry.data.get(CONF_BUFFER_MINUTES, 30)
        self.check_interval = entry.data.get(CONF_CHECK_INTERVAL, 30)
        
        # Auto control settings
        self.auto_control_enabled = entry.data.get(CONF_AUTO_CONTROL_ENABLED, True)
        
        # Regression data
        self.samples: List[Tuple[float, float, datetime]] = []
        self.regression_a = 1.0
        self.regression_b = 0.0
        self.regression_quality = 0.0
        self.max_samples = 100
        
        # Settings
        self.min_regression_quality = DEFAULT_MIN_REGRESSION_QUALITY
        self.max_brightness_change = DEFAULT_MAX_BRIGHTNESS_CHANGE
        self.deviation_margin = entry.data.get(CONF_DEVIATION_MARGIN, DEFAULT_DEVIATION_MARGIN)
        self.learning_rate = DEFAULT_LEARNING_RATE
        
        # Motion and automation tracking
        self.last_motion_time: Optional[datetime] = None
        self.lights_controlled_by_automation = False
        self.current_target_lux: Optional[float] = None
        self.current_predicted_lux: Optional[float] = None
        self.last_automation_action: Optional[str] = None
        
        # Smart mode settings
        self._smart_mode_enabled = True
        self._adaptive_learning_enabled = True
        
        # Storage
        self.store = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{self.room_name}")
        
        # State tracking
        self._unsub_listeners = []
        self._automation_task: Optional[asyncio.Task] = None
    
    async def async_setup(self) -> None:
        """Set up the coordinator."""
        # Load stored data
        await self._async_load_data()
        
        # Set up state change listeners
        await self._async_setup_listeners()
        
        # Start automation task if auto control is enabled
        if self.auto_control_enabled:
            await self._async_start_automation_task()
        
        _LOGGER.info("Smart Lux Control coordinator set up for room: %s", self.room_name)
    
    async def async_unload(self) -> None:
        """Unload the coordinator."""
        # Cancel automation task
        if self._automation_task:
            self._automation_task.cancel()
            try:
                await self._automation_task
            except asyncio.CancelledError:
                pass
            
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()
    
    async def _async_load_data(self) -> None:
        """Load data from storage."""
        data = await self.store.async_load() or {}
        
        # Load samples
        samples_data = data.get("samples", [])
        self.samples = []
        for sample in samples_data:
            try:
                brightness, lux, timestamp_str = sample
                timestamp = datetime.fromisoformat(timestamp_str)
                self.samples.append((brightness, lux, timestamp))
            except (ValueError, TypeError):
                continue
        
        # Load regression data
        self.regression_a = data.get("regression_a", 1.0)
        self.regression_b = data.get("regression_b", 0.0)
        self.regression_quality = data.get("regression_quality", 0.0)
        
        # Load settings
        self.min_regression_quality = data.get("min_regression_quality", DEFAULT_MIN_REGRESSION_QUALITY)
        self.max_brightness_change = data.get("max_brightness_change", DEFAULT_MAX_BRIGHTNESS_CHANGE)
        self.deviation_margin = data.get("deviation_margin", DEFAULT_DEVIATION_MARGIN)
        self.learning_rate = data.get("learning_rate", DEFAULT_LEARNING_RATE)
    
    async def _async_save_data(self) -> None:
        """Save data to storage."""
        # Prepare samples for storage
        samples_data = []
        for brightness, lux, timestamp in self.samples[-self.max_samples:]:
            samples_data.append([brightness, lux, timestamp.isoformat()])
        
        data = {
            "samples": samples_data,
            "regression_a": self.regression_a,
            "regression_b": self.regression_b,
            "regression_quality": self.regression_quality,
            "min_regression_quality": self.min_regression_quality,
            "max_brightness_change": self.max_brightness_change,
            "deviation_margin": self.deviation_margin,
            "learning_rate": self.learning_rate,
        }
        
        await self.store.async_save(data)
    
    async def _async_setup_listeners(self) -> None:
        """Set up state change listeners."""
        # Listen for light changes from all controlled lights
        self._unsub_listeners.append(
            async_track_state_change_event(
                self.hass, self.light_entities, self._async_light_changed
            )
        )
        
        # Listen for lux sensor changes
        self._unsub_listeners.append(
            async_track_state_change_event(
                self.hass, [self.lux_sensor], self._async_lux_changed
            )
        )
    
    async def _async_light_changed(self, event) -> None:
        """Handle light state changes."""
        new_state = event.data.get("new_state")
        if not new_state or new_state.state != "on":
            return
        
        brightness = new_state.attributes.get("brightness")
        if brightness is None:
            return
        
        # Wait a bit for lux to stabilize, then add sample
        await asyncio.sleep(3)
        
        lux_state = self.hass.states.get(self.lux_sensor)
        if lux_state and lux_state.state not in ("unknown", "unavailable"):
            try:
                lux_value = float(lux_state.state)
                await self.async_add_sample(brightness, lux_value)
            except ValueError:
                pass
    
    async def _async_lux_changed(self, event) -> None:
        """Handle lux sensor changes."""
        # Could be used for future enhancements
        pass
    
    async def async_add_sample(self, brightness: float, lux: float) -> None:
        """Add a sample to the dataset."""
        # Validate data
        if not (0 <= brightness <= 255) or not (0 <= lux <= 10000):
            _LOGGER.warning("Invalid sample data: brightness=%s, lux=%s", brightness, lux)
            return
        
        # Check for duplicates (last 5 samples)
        recent_samples = self.samples[-5:] if len(self.samples) >= 5 else self.samples
        for sample_brightness, sample_lux, _ in recent_samples:
            if abs(sample_brightness - brightness) < 5 and abs(sample_lux - lux) < 10:
                return  # Skip duplicate
        
        # Add sample
        timestamp = datetime.now()
        self.samples.append((brightness, lux, timestamp))
        
        # Keep only recent samples
        if len(self.samples) > self.max_samples:
            self.samples = self.samples[-self.max_samples:]
        
        # Save data
        await self._async_save_data()
        
        # Fire event
        self.hass.bus.async_fire(EVENT_SAMPLE_ADDED, {
            "room_name": self.room_name,
            "brightness": brightness,
            "lux": lux,
            "total_samples": len(self.samples)
        })
        
        _LOGGER.debug("Added sample for %s: brightness=%s, lux=%s", self.room_name, brightness, lux)
        
        # Auto-calculate regression if we have enough samples
        if len(self.samples) >= 10 and len(self.samples) % 5 == 0:
            await self.async_calculate_regression()
    
    async def async_calculate_regression(self) -> None:
        """Calculate linear regression from samples."""
        if len(self.samples) < 5:
            _LOGGER.warning("Not enough samples for regression: %d", len(self.samples))
            return
        
        # Filter outliers and prepare data
        brightness_vals, lux_vals = self._filter_samples()
        
        if len(brightness_vals) < 3:
            _LOGGER.warning("Not enough valid samples after filtering: %d", len(brightness_vals))
            return
        
        # Calculate regression
        n = len(brightness_vals)
        x_avg = sum(brightness_vals) / n
        y_avg = sum(lux_vals) / n
        
        numerator = sum((x - x_avg) * (y - y_avg) for x, y in zip(brightness_vals, lux_vals))
        denominator = sum((x - x_avg) ** 2 for x in brightness_vals)
        
        if denominator == 0:
            _LOGGER.warning("Cannot calculate regression: all brightness values are identical")
            return
        
        self.regression_a = numerator / denominator
        self.regression_b = y_avg - self.regression_a * x_avg
        
        # Calculate R²
        y_pred = [self.regression_a * x + self.regression_b for x in brightness_vals]
        ss_res = sum((y_actual - y_pred) ** 2 for y_actual, y_pred in zip(lux_vals, y_pred))
        ss_tot = sum((y - y_avg) ** 2 for y in lux_vals)
        
        self.regression_quality = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Save data
        await self._async_save_data()
        
        # Fire event
        self.hass.bus.async_fire(EVENT_REGRESSION_UPDATED, {
            "room_name": self.room_name,
            "regression_a": self.regression_a,
            "regression_b": self.regression_b,
            "regression_quality": self.regression_quality,
            "sample_count": n
        })
        
        _LOGGER.info(
            "Regression updated for %s: a=%.4f, b=%.1f, R²=%.3f, samples=%d",
            self.room_name, self.regression_a, self.regression_b, self.regression_quality, n
        )
    
    def _filter_samples(self) -> Tuple[List[float], List[float]]:
        """Filter samples and remove outliers."""
        if not self.samples:
            return [], []
        
        brightness_vals = []
        lux_vals = []
        
        # Extract valid samples
        for brightness, lux, timestamp in self.samples:
            if 0 <= brightness <= 255 and 0 <= lux <= 10000:
                brightness_vals.append(brightness)
                lux_vals.append(lux)
        
        if len(brightness_vals) < 8:
            return brightness_vals, lux_vals
        
        # Remove outliers (more than 2 standard deviations)
        x_mean = sum(brightness_vals) / len(brightness_vals)
        y_mean = sum(lux_vals) / len(lux_vals)
        x_std = math.sqrt(sum((x - x_mean) ** 2 for x in brightness_vals) / len(brightness_vals))
        y_std = math.sqrt(sum((y - y_mean) ** 2 for y in lux_vals) / len(lux_vals))
        
        filtered_brightness = []
        filtered_lux = []
        
        for brightness, lux in zip(brightness_vals, lux_vals):
            if (abs(brightness - x_mean) < 2 * x_std and abs(lux - y_mean) < 2 * y_std):
                filtered_brightness.append(brightness)
                filtered_lux.append(lux)
        
        return filtered_brightness, filtered_lux
    
    async def async_clear_samples(self) -> None:
        """Clear all samples."""
        self.samples.clear()
        self.regression_a = 1.0
        self.regression_b = 0.0
        self.regression_quality = 0.0
        await self._async_save_data()
        
        _LOGGER.info("Cleared all samples for room: %s", self.room_name)
    
    async def async_adaptive_learning(self) -> None:
        """Perform adaptive learning to improve the model."""
        if len(self.samples) < 15:
            _LOGGER.info("Not enough samples for adaptive learning: %d", len(self.samples))
            return
        
        # Analyze prediction errors
        brightness_vals, lux_vals = self._filter_samples()
        if len(brightness_vals) < 10:
            return
        
        errors = []
        for brightness, lux in zip(brightness_vals, lux_vals):
            predicted_lux = self.regression_a * brightness + self.regression_b
            error = abs(lux - predicted_lux)
            errors.append(error)
        
        average_error = sum(errors) / len(errors)
        max_error = max(errors)
        
        # Decide if update is needed
        should_update = False
        if average_error > 20:
            should_update = True
        elif max_error > 50:
            should_update = True
        elif self.regression_quality < 0.7 and len(self.samples) >= 20:
            should_update = True
        
        if not should_update:
            _LOGGER.debug("Model is good enough, no adaptive learning needed for %s", self.room_name)
            return
        
        # Perform weighted regression (newer samples have more weight)
        now = datetime.now()
        weights = []
        for _, _, timestamp in [(brightness_vals[i], lux_vals[i], self.samples[i][2]) for i in range(len(brightness_vals))]:
            age_hours = (now - timestamp).total_seconds() / 3600
            weight = math.exp(-age_hours / 24.0)  # Half-life of 24 hours
            weights.append(weight)
        
        # Calculate weighted regression
        new_a, new_b, new_quality = self._weighted_regression(brightness_vals, lux_vals, weights)
        
        if new_a is None:
            return
        
        # Adaptive update (mix old and new model)
        old_a = self.regression_a
        old_b = self.regression_b
        old_quality = self.regression_quality
        
        self.regression_a = old_a * (1 - self.learning_rate) + new_a * self.learning_rate
        self.regression_b = old_b * (1 - self.learning_rate) + new_b * self.learning_rate
        self.regression_quality = new_quality
        
        # Save data
        await self._async_save_data()
        
        improvement = new_quality - old_quality
        _LOGGER.info(
            "Adaptive learning for %s: a=%.4f→%.4f, b=%.1f→%.1f, R²=%.3f→%.3f (Δ%.3f)",
            self.room_name, old_a, self.regression_a, old_b, self.regression_b,
            old_quality, self.regression_quality, improvement
        )
    
    def _weighted_regression(self, x_vals: List[float], y_vals: List[float], weights: List[float]) -> Tuple[Optional[float], Optional[float], float]:
        """Calculate weighted linear regression."""
        if not x_vals or len(x_vals) != len(y_vals) or len(x_vals) != len(weights):
            return None, None, 0
        
        sum_w = sum(weights)
        if sum_w == 0:
            return None, None, 0
        
        # Weighted averages
        x_avg = sum(w * x for w, x in zip(weights, x_vals)) / sum_w
        y_avg = sum(w * y for w, y in zip(weights, y_vals)) / sum_w
        
        # Calculate coefficients
        numerator = sum(w * (x - x_avg) * (y - y_avg) for w, x, y in zip(weights, x_vals, y_vals))
        denominator = sum(w * (x - x_avg) ** 2 for w, x in zip(weights, x_vals))
        
        if denominator == 0:
            return None, None, 0
        
        a = numerator / denominator
        b = y_avg - a * x_avg
        
        # Calculate weighted R²
        y_pred = [a * x + b for x in x_vals]
        ss_res = sum(w * (y_actual - y_pred) ** 2 for w, y_actual, y_pred in zip(weights, y_vals, y_pred))
        ss_tot = sum(w * (y - y_avg) ** 2 for w, y in zip(weights, y_vals))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return a, b, r_squared
    
    def calculate_target_brightness(self, target_lux: float, current_brightness: float = 255) -> int:
        """Calculate target brightness for desired lux level."""
        if self.regression_quality < self.min_regression_quality or self.regression_a == 0:
            # Fallback: proportional calculation
            current_lux_state = self.hass.states.get(self.lux_sensor)
            if current_lux_state and current_lux_state.state not in ("unknown", "unavailable"):
                try:
                    current_lux = float(current_lux_state.state)
                    if current_lux > 0:
                        ratio = target_lux / current_lux
                        calculated = current_brightness * ratio
                        return max(1, min(int(calculated), 255))
                except ValueError:
                    pass
            return current_brightness
        
        # Use regression: lux = a * brightness + b, so brightness = (lux - b) / a
        calculated = (target_lux - self.regression_b) / self.regression_a
        target = max(1, min(int(calculated), 255))
        
        # Limit change size
        diff = abs(target - current_brightness)
        if diff > self.max_brightness_change:
            if target > current_brightness:
                target = current_brightness + self.max_brightness_change
            else:
                target = current_brightness - self.max_brightness_change
        
        return max(1, min(target, 255))
    
    def get_target_lux(self) -> float:
        """Get target lux based on current home mode and time."""
        if self.home_mode_select:
            mode_state = self.hass.states.get(self.home_mode_select)
            if mode_state and mode_state.state in self.lux_settings:
                return float(self.lux_settings[mode_state.state])
        
        # Default: time-based normal mode with sunrise/sunset logic
        from homeassistant.helpers import sun
        from homeassistant.util import dt as dt_util
        
        now = dt_util.now()
        now_ts = now.timestamp()
        
        # Get sunrise/sunset times
        sun_state = self.hass.states.get("sun.sun")
        if sun_state:
            sunrise = sun_state.attributes.get("next_rising")
            sunset = sun_state.attributes.get("next_setting")
            
            if sunrise and sunset:
                try:
                    sunrise_dt = dt_util.parse_datetime(sunrise)
                    sunset_dt = dt_util.parse_datetime(sunset)
                    if sunrise_dt and sunset_dt:
                        sunrise_ts = sunrise_dt.timestamp() - 86400  # Previous sunrise
                        sunset_ts = sunset_dt.timestamp()
                    else:
                        raise ValueError("Could not parse datetime")
                except (ValueError, AttributeError):
                    # Fallback to simple hour-based logic
                    if 6 <= now.hour <= 22:
                        return float(self.lux_settings["normal_day"])
                    else:
                        return float(self.lux_settings["normal_night"])
                
                # Calculate with buffer
                buffer_seconds = self.buffer_minutes * 60
                
                # Day/night transition logic
                if sunrise_ts <= now_ts < (sunrise_ts + buffer_seconds):
                    # Sunrise transition
                    ratio = (now_ts - sunrise_ts) / buffer_seconds
                    lux_day = float(self.lux_settings["normal_day"])
                    lux_night = float(self.lux_settings["normal_night"])
                    return lux_night + (lux_day - lux_night) * ratio
                elif (sunset_ts - buffer_seconds) < now_ts <= sunset_ts:
                    # Sunset transition
                    ratio = 1 - ((now_ts - (sunset_ts - buffer_seconds)) / buffer_seconds)
                    lux_day = float(self.lux_settings["normal_day"])
                    lux_night = float(self.lux_settings["normal_night"])
                    return lux_night + (lux_day - lux_night) * ratio
                elif sunrise_ts + buffer_seconds <= now_ts < (sunset_ts - buffer_seconds):
                    # Full day
                    return float(self.lux_settings["normal_day"])
                else:
                    # Full night
                    return float(self.lux_settings["normal_night"])
        
        # Fallback: simple hour-based logic
        if 6 <= now.hour <= 22:
            return float(self.lux_settings["normal_day"])
        else:
            return float(self.lux_settings["normal_night"])
    
    @property
    def is_smart_mode_active(self) -> bool:
        """Check if smart mode is active."""
        return self.regression_quality >= self.min_regression_quality
    
    @property
    def sample_count(self) -> int:
        """Get number of samples."""
        return len(self.samples)
    
    @property
    def predicted_lux(self) -> Optional[float]:
        """Get predicted lux for current brightness."""
        # Get average brightness from all controlled lights
        total_brightness = 0
        light_count = 0
        
        for light_entity in self.light_entities:
            light_state = self.hass.states.get(light_entity)
            if light_state and light_state.state == "on":
                brightness = light_state.attributes.get("brightness")
                if brightness is not None:
                    total_brightness += brightness
                    light_count += 1
        
        if light_count == 0:
            return None
        
        avg_brightness = total_brightness / light_count
        return self.regression_a * avg_brightness + self.regression_b
    
    def should_lights_be_on(self) -> bool:
        """Check if lights should be on based on motion and time."""
        if not self.auto_control_enabled:
            return False
        
        # Check motion sensor
        motion_state = self.hass.states.get(self.motion_sensor)
        if not motion_state:
            return False
        
        from homeassistant.util import dt as dt_util
        now = dt_util.now()
        
        # If motion is currently detected
        if motion_state.state == "on":
            self.last_motion_time = now
            return True
        
        # Check if motion was recent enough
        if self.last_motion_time:
            time_since_motion = (now - self.last_motion_time).total_seconds() / 60
            return time_since_motion <= self.keep_on_minutes
        
        return False
    
    def get_current_brightness(self) -> int:
        """Get average current brightness of controlled lights."""
        total_brightness = 0
        light_count = 0
        
        for light_entity in self.light_entities:
            light_state = self.hass.states.get(light_entity)
            if light_state and light_state.state == "on":
                brightness = light_state.attributes.get("brightness", 255)
                total_brightness += brightness
                light_count += 1
        
        return int(total_brightness / light_count) if light_count > 0 else 255
    
    async def async_control_lights(self) -> None:
        """Main automation logic - control lights based on conditions."""
        if not self.auto_control_enabled:
            return
        
        should_be_on = self.should_lights_be_on()
        
        if not should_be_on:
            # Turn off lights if they were controlled by automation
            if self.lights_controlled_by_automation:
                await self._async_turn_off_lights()
                self.lights_controlled_by_automation = False
                self.last_automation_action = "turned_off_no_motion"
            return
        
        # Get current and target lux
        target_lux = self.get_target_lux()
        self.current_target_lux = target_lux
        
        # Get current lux reading
        lux_state = self.hass.states.get(self.lux_sensor)
        if not lux_state or lux_state.state in ("unknown", "unavailable"):
            return
        
        try:
            current_lux = float(lux_state.state)
        except ValueError:
            return
        
        deviation = target_lux - current_lux
        
        # Check if adjustment is needed
        if abs(deviation) <= self.deviation_margin:
            self.last_automation_action = "within_tolerance"
            return
        
        # Calculate target brightness
        current_brightness = self.get_current_brightness()
        
        if self._smart_mode_enabled and self.is_smart_mode_active:
            # Smart mode: use regression
            target_brightness = self.calculate_target_brightness(target_lux, current_brightness)
            mode = "smart"
        else:
            # Fallback mode: step adjustment
            if deviation > 0:
                target_brightness = min(current_brightness + 30, 255)
            else:
                target_brightness = max(current_brightness - 30, 1)
            mode = "fallback"
        
        # Apply brightness change
        await self._async_set_brightness(target_brightness)
        self.lights_controlled_by_automation = True
        
        # Update predicted lux for sensors
        self.current_predicted_lux = self.regression_a * target_brightness + self.regression_b
        
        # Log action
        self.last_automation_action = f"{mode}_{current_brightness}→{target_brightness}_for_{target_lux:.1f}lx"
        
        _LOGGER.info(
            "Smart Lux Control [%s]: %s mode, target: %.1flx, current: %.1flx, "
            "brightness: %d→%d, quality: %.2f",
            self.room_name, mode, target_lux, current_lux, 
            current_brightness, target_brightness, self.regression_quality
        )
    
    async def _async_turn_off_lights(self) -> None:
        """Turn off controlled lights."""
        for light_entity in self.light_entities:
            await self.hass.services.async_call(
                "light", "turn_off",
                {"entity_id": light_entity},
                blocking=True
            )
    
    async def _async_set_brightness(self, brightness: int) -> None:
        """Set brightness for controlled lights."""
        for light_entity in self.light_entities:
            await self.hass.services.async_call(
                "light", "turn_on",
                {
                    "entity_id": light_entity,
                    "brightness": brightness,
                    "transition": 2
                },
                blocking=True
            )
    
    async def _async_start_automation_task(self) -> None:
        """Start the automation background task."""
        if self._automation_task and not self._automation_task.done():
            return
        
        _LOGGER.info("Starting automation task for room: %s", self.room_name)
        self._automation_task = asyncio.create_task(self._async_automation_loop())
    
    async def _async_automation_loop(self) -> None:
        """Background task that runs light control automation."""
        while True:
            try:
                if self.auto_control_enabled:
                    await self.async_control_lights()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                _LOGGER.info("Automation task cancelled for room: %s", self.room_name)
                break
            except Exception as err:
                _LOGGER.error(
                    "Error in automation loop for room %s: %s", 
                    self.room_name, err
                )
                # Wait a bit before retrying
                await asyncio.sleep(30)
    
    def enable_auto_control(self, enabled: bool) -> None:
        """Enable or disable auto control."""
        self.auto_control_enabled = enabled
        
        if enabled and (not self._automation_task or self._automation_task.done()):
            # Start task if it's not running
            asyncio.create_task(self._async_start_automation_task())
        elif not enabled and self._automation_task and not self._automation_task.done():
            # Cancel task if it's running
            self._automation_task.cancel()
    
    @property
    def smart_mode_enabled(self) -> bool:
        """Get smart mode status."""
        return self._smart_mode_enabled
    
    def set_smart_mode(self, enabled: bool) -> None:
        """Enable or disable smart mode."""
        self._smart_mode_enabled = enabled
    
    @property 
    def adaptive_learning_enabled(self) -> bool:
        """Get adaptive learning status."""
        return self._adaptive_learning_enabled
    
    def set_adaptive_learning(self, enabled: bool) -> None:
        """Enable or disable adaptive learning."""
        self._adaptive_learning_enabled = enabled 