"""Constants for Smart Lux Control integration."""

DOMAIN = "smart_lux_control"
PLATFORMS = ["sensor", "switch"]

# Configuration keys
CONF_ROOM_NAME = "room_name"
CONF_LIGHT_ENTITY = "light_entity"
CONF_LUX_SENSOR = "lux_sensor"
CONF_MOTION_SENSOR = "motion_sensor"
CONF_HOME_MODE_SELECT = "home_mode_select"

# Lux settings
CONF_LUX_NORMAL_DAY = "lux_normal_day"
CONF_LUX_NORMAL_NIGHT = "lux_normal_night"
CONF_LUX_MODE_NOC = "lux_mode_noc"
CONF_LUX_MODE_IMPREZA = "lux_mode_impreza"
CONF_LUX_MODE_RELAKS = "lux_mode_relaks"
CONF_LUX_MODE_FILM = "lux_mode_film"
CONF_LUX_MODE_SPRZATANIE = "lux_mode_sprzatanie"
CONF_LUX_MODE_DZIECKO_SPI = "lux_mode_dziecko_spi"

# Timing settings
CONF_KEEP_ON_MINUTES = "keep_on_minutes"
CONF_BUFFER_MINUTES = "buffer_minutes"
CONF_DEVIATION_MARGIN = "deviation_margin"
CONF_CHECK_INTERVAL = "check_interval"
CONF_AUTO_CONTROL_ENABLED = "auto_control_enabled"

# Default values
DEFAULT_MIN_REGRESSION_QUALITY = 0.5
DEFAULT_MAX_BRIGHTNESS_CHANGE = 50  
DEFAULT_DEVIATION_MARGIN = 15
DEFAULT_LEARNING_RATE = 0.1

# Storage
STORAGE_VERSION = 1

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
SERVICE_CALCULATE_TARGET_BRIGHTNESS = "calculate_target_brightness"
SERVICE_TEST_LIGHT_CONTROL = "test_light_control"
SERVICE_SYNC_LIGHT_STATES = "sync_light_states"

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
        "name": "Current Lux",
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
    "target_lux": {
        "name": "Target Lux",
        "unit": "lx",
        "icon": "mdi:crosshairs",
        "device_class": "illuminance",
    },
    "automation_status": {
        "name": "Automation Status",
        "unit": None,
        "icon": "mdi:play-circle",
        "device_class": None,
    },
    "last_automation_action": {
        "name": "Last Automation Action",
        "unit": None,
        "icon": "mdi:history",
        "device_class": None,
    },
    "motion_timer": {
        "name": "Motion Timer",
        "unit": "min",
        "icon": "mdi:timer",
        "device_class": None,
    },
    "motion_status": {
        "name": "Motion Detection Status",
        "unit": None,
        "icon": "mdi:motion-sensor",
        "device_class": None,
    },
    "lights_status": {
        "name": "Controlled Lights Status",
        "unit": None,
        "icon": "mdi:lightbulb-group",
        "device_class": None,
    },
}

# Events
EVENT_REGRESSION_UPDATED = f"{DOMAIN}_regression_updated"
EVENT_SMART_MODE_CHANGED = f"{DOMAIN}_smart_mode_changed"
EVENT_SAMPLE_ADDED = f"{DOMAIN}_sample_added" 