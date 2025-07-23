"""Constants for Smart Lux Control integration."""

DOMAIN = "smart_lux_control"
PLATFORMS = ["sensor", "switch"]

# Configuration keys
CONF_ROOM_NAME = "room_name"
CONF_LIGHT_ENTITY = "light_entity"
CONF_LUX_SENSOR = "lux_sensor"
CONF_MOTION_SENSOR = "motion_sensor"
CONF_HOME_MODE_SELECT = "home_mode_select"

# Default values
DEFAULT_MIN_REGRESSION_QUALITY = 0.5
DEFAULT_MAX_BRIGHTNESS_CHANGE = 50
DEFAULT_DEVIATION_MARGIN = 15
DEFAULT_LEARNING_RATE = 0.1

# Lux levels for different modes
LUX_MODES = {
    "normal_day": 400,
    "normal_night": 150,
    "noc": 10,
    "impreza": 500,
    "relaks": 120,
    "film": 60,
    "sprzatanie": 600,
    "dziecko_spi": 8,
}

# Services
SERVICE_CALCULATE_REGRESSION = "calculate_regression"
SERVICE_CLEAR_SAMPLES = "clear_samples"
SERVICE_ADD_SAMPLE = "add_sample"
SERVICE_ADAPTIVE_LEARNING = "adaptive_learning"

# Sensor types
SENSOR_TYPES = {
    "regression_quality": {
        "name": "Regression Quality",
        "unit": "R²",
        "icon": "mdi:chart-line",
        "device_class": None,
    },
    "sample_count": {
        "name": "Sample Count",
        "unit": "samples",
        "icon": "mdi:database",
        "device_class": None,
    },
    "smart_mode_status": {
        "name": "Smart Mode Status",
        "unit": None,
        "icon": "mdi:brain",
        "device_class": None,
    },
    "predicted_lux": {
        "name": "Predicted Lux",
        "unit": "lx",
        "icon": "mdi:brightness-6",
        "device_class": "illuminance",
    },
    "average_error": {
        "name": "Average Prediction Error",
        "unit": "lx",
        "icon": "mdi:target",
        "device_class": None,
    },
}

# Events
EVENT_REGRESSION_UPDATED = f"{DOMAIN}_regression_updated"
EVENT_SMART_MODE_CHANGED = f"{DOMAIN}_smart_mode_changed"
EVENT_SAMPLE_ADDED = f"{DOMAIN}_sample_added" 