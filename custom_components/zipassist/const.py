"""Constants for the ZipAssist CMMS integration."""

from __future__ import annotations

DOMAIN = "zipassist"

# Configuration
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_BASE_URL = "base_url"

DEFAULT_BASE_URL = "https://zipassist.zipindustries.com"
DEFAULT_TIMEOUT = 30
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes

# API paths (all under /api/)
API_AUTH_LOGIN = "/api/auth/jwt/login"
API_AUTH_REFRESH = "/api/auth/jwt/refresh"
API_HYDROTAPS = "/api/hydrotaps"
API_OWNERS = "/api/owners"
API_SLEEP_MODES = "/api/sleep-modes"
API_SYSTEM_FAULTS = "/api/system-faults"
API_SYSTEM_EVENTS = "/api/system-events"
API_COUNTRIES = "/api/countries"
API_TIMEZONES = "/api/timezones"

# API sub-paths (appended to /api/hydrotaps/{id}/)
API_SETTINGS = "settings"
API_SETTINGS_OPTIONS = "settings-options"
API_TIMEZONE = "timezone"
API_LOGS_GENERAL = "logs/general"
API_LOGS_SYSTEM_FAULTS = "logs/system-faults"
API_LOGS_FILTER_USAGE = "logs/filter-usage"
API_LOGS_DISPENSE_EVENTS = "logs/dispense-events"
API_LOGS_DAILY_USAGE = "logs/daily-usage"
API_USAGE_WATER = "usage/water"
API_USAGE_ENERGY = "usage/energy"
API_GRAPHS_USAGE = "graphs/usage"
API_GRAPHS_AVERAGE_USAGE = "graphs/average-usage"
API_NOTES = "notes"
API_HYDROTAP_SEARCH_OPTIONS = "/api/hydrotap-search-options"

# Platforms
PLATFORMS = ["sensor", "number", "binary_sensor", "switch", "select", "time"]

# Attributes
ATTR_HYDROTAP_ID = "hydrotap_id"
ATTR_HYDROTAP_NAME = "hydrotap_name"
ATTR_SERIAL_NUMBER = "serial_number"
ATTR_MODULE_NAME = "module_name"
ATTR_FIRMWARE_VERSION = "firmware_version"
ATTR_FILTER_LITRES = "filter_litres_remaining"
ATTR_FILTER_DAYS = "filter_days_remaining"
ATTR_FILTER_ESTIMATED = "filter_estimated_days"
ATTR_AVG_DAILY_USAGE = "average_daily_usage"
ATTR_PEAK_HOURLY_USAGE = "peak_hourly_usage"