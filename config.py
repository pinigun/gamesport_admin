import os


DB_URL = os.getenv('DB_URL')
HASH_SECRET_KEY = os.getenv("HASH_SECRET_KEY", "PT1bj08S0YAe")
DATE_FORMAT: str = "%d-%m-%Y %H:%M"
GS_DATE_FORMAT: str = "%Y-%m-%d"
FRONT_DATE_FORMAT: str = "%Y-%m-%d"
FRONT_TIME_FORMAT: str = "%H:%M"
