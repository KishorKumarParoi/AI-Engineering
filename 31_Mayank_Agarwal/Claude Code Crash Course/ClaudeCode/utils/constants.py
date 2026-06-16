from datetime import timedelta

APP_NAME = "Task Manager"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Mayank"

DEBUG = True
LOG_LEVEL = "INFO"

MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 20
MIN_PASSWORD_LENGTH = 8

TIMEOUT_SECONDS = 30
MAX_RETRIES = 3

CACHE_TTL = timedelta(hours=1)
SESSION_TIMEOUT = timedelta(hours=24)

SUCCESS_STATUS = 200
CREATED_STATUS = 201
BAD_REQUEST_STATUS = 400
UNAUTHORIZED_STATUS = 401
NOT_FOUND_STATUS = 404
SERVER_ERROR_STATUS = 500

SUPPORTED_IMAGE_FORMATS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
MAX_FILE_SIZE_MB = 10

TIMEZONE = "UTC"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#52c41a',
    'error': '#ff6b6b',
    'warning': '#faad14',
    'info': '#1890ff',
}

API_BASE_URL = "https://api.example.com"
API_TIMEOUT = 10
API_MAX_REQUESTS_PER_MINUTE = 60
