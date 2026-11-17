# Image for the Flask API and the Celery worker. Both run the same code, so
# compose.yaml builds this image once and starts it with different commands.
FROM python:3.12-slim

WORKDIR /app

# Copy requirements.txt on its own first. Docker caches each step, so when you
# change only your code, the next build skips reinstalling the packages.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
