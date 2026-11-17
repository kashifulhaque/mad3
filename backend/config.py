"""Settings for the Examination Management System backend.

Every setting lives here so that you can find it in one place. Each value
comes from an environment variable when one is set, and falls back to a
default that works on a local machine.
"""

import os

# BASE_DIR is the folder that holds this file. You build absolute paths from
# it so that the Flask app and the Celery worker find the same database and
# reports folder, whichever directory you start them from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "exams.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # One Redis server does three jobs: Celery message broker, Celery result
    # backend, and cache for exam statistics.
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # How long, in seconds, cached exam statistics stay in Redis.
    STATS_CACHE_SECONDS = int(os.environ.get("STATS_CACHE_SECONDS", "60"))

    # The Celery report task writes CSV files here, and the
    # GET /api/reports/<filename> endpoint serves them from here.
    REPORTS_DIR = os.environ.get("REPORTS_DIR", os.path.join(BASE_DIR, "reports"))
