"""Entry point for the Celery worker process.

Start the worker with the following command:

    celery -A celery_worker.celery worker --loglevel=info

The worker runs separately from the Flask server. It waits for task messages
on the Redis queue and runs the matching functions from tasks.py.
"""

from app import create_app
from extensions import celery

# Importing tasks registers the task functions with Celery, so the worker
# knows which function to run for each message.
import tasks  # noqa: F401

# Flask-SQLAlchemy only works inside a Flask application context, which tells
# it which app's settings and database to use. During a web request, Flask
# opens that context for you. The worker handles no web requests, so you push
# one context here, once, and it stays open for every task the worker runs.
flask_app = create_app()
flask_app.app_context().push()
