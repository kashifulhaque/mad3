"""Shared objects that the rest of the backend imports.

This module creates the database, Redis, and Celery objects once. Other
modules import them from here instead of creating their own copies. Keeping
them in a separate file also avoids circular imports: `models.py`,
`routes.py`, and `tasks.py` all need these objects, and none of them needs to
import `app.py`.
"""

import redis
from celery import Celery
from flask_sqlalchemy import SQLAlchemy

from config import Config

# The SQLAlchemy object starts unbound. The create_app() function in app.py
# connects it to the Flask app by calling db.init_app(app).
db = SQLAlchemy()

# A plain Redis client for the exam statistics cache. With
# decode_responses=True, reads return Python strings instead of bytes.
redis_client = redis.Redis.from_url(Config.REDIS_URL, decode_responses=True)

# The Celery app. The broker is the queue where Flask drops task messages.
# The backend is where the worker stores each task's state and return value,
# so that GET /api/tasks/<task_id> can read them later.
celery = Celery(
    "exam_system",
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL,
)
# Report STARTED while a task runs, instead of PENDING until it finishes.
celery.conf.task_track_started = True
# Run tasks one at a time inside the worker process itself. Celery's default
# pool starts child processes, which fails on macOS and Windows because they
# start children with "spawn" instead of "fork". The solo pool works
# everywhere, and one task at a time is enough for this project.
celery.conf.worker_pool = "solo"
