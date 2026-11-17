# Examination management system

A small full-stack app for managing students, exams, and results. It's built
to be read: every file is short and has comments that explain why the code
looks the way it does.

With this app, you can do the following:

- Add and delete students and exams.
- Record marks and see whether each student passed. A student passes when
  their marks are at least 40% of the exam's maximum marks.
- View exam statistics, cached in Redis.
- Generate a CSV report and send simulated result emails as background jobs
  with Celery.

## Architecture

The app has four running parts. The following diagram shows how they connect:

```
 Browser                Flask API                     SQLite
┌──────────────┐ HTTP  ┌───────────────────┐  SQL    ┌────────────┐
│ Vue 3 + Vite │──────▶│ routes.py         │────────▶│ exams.db   │
│ Bootstrap    │◀──────│ (REST, JSON)      │         └────────────┘
│ :5173        │ JSON  │ :5000             │               ▲
└──────────────┘       └───┬───────────┬───┘               │ SQL
                           │ cache     │ .delay()          │
                           ▼           ▼                   │
                       ┌──────────────────────┐    ┌───────┴───────┐
                       │ Redis :6379          │◀──▶│ Celery worker │
                       │ • stats cache        │    │ tasks.py      │
                       │ • task queue (broker)│    └───────────────┘
                       │ • task results       │
                       └──────────────────────┘
```

| Part          | Technology                      | Job                                                      |
|---------------|---------------------------------|----------------------------------------------------------|
| Frontend      | Vue 3, Vite, Bootstrap 5        | Shows pages and calls the REST API with `fetch`.         |
| Backend       | Flask, Flask-SQLAlchemy         | Validates input, reads and writes the database.          |
| Database      | SQLite                          | Stores students, exams, and results in one file.         |
| Cache, broker | Redis                           | Caches exam stats and carries Celery job messages.       |
| Worker        | Celery                          | Runs slow jobs (reports, emails) outside the web request. |

The frontend and backend agree on every URL and JSON shape in
[API_CONTRACT.md](API_CONTRACT.md).

## Project structure

```
compose.yaml        runs all four parts with Docker
backend/
  Dockerfile        image for the API and the worker
  app.py            create_app() factory; starts the Flask server
  config.py         every setting in one place
  extensions.py     shared db, redis_client, and celery objects
  models.py         Student, Exam, Result tables
  routes.py         all REST endpoints (one Blueprint)
  tasks.py          Celery background jobs
  celery_worker.py  entry point for the Celery worker
  seed.py           demo data
frontend/
  Dockerfile        image for the Vite dev server
  vite.config.js    forwards /api to the backend in Docker
frontend/src/
  main.js           creates the Vue app, loads Bootstrap and the router
  api.js            one function per backend endpoint
  utils.js          date, initials, and percentage helpers for display
  router.js         URL-to-page mapping
  App.vue           navbar and page outlet
  views/            Dashboard, Students, Exams, Results pages
  components/
    TaskStatus.vue  polls a Celery job until it finishes
```

## Run with Docker

If you have [Docker Desktop](https://docs.docker.com/get-started/get-docker/)
installed, you can start everything with one command:

```bash
docker compose up --build
```

Open `http://localhost:5173`. Compose starts Redis, the Flask API, the Celery
worker, and the Vite dev server, and adds demo data on the first run.

The following commands are also useful:

- To stop the app, press `Ctrl+C`, or run `docker compose down`.
- To start over with fresh demo data, run `docker compose down -v`. The `-v`
  flag deletes the volume that holds the database and reports.
- To see the worker's log lines while a job runs, run
  `docker compose logs -f worker`.

The containers copy your code when Docker builds them. After you edit a
file, run `docker compose up --build` again to see the change.

In Docker, the browser talks only to the frontend on port 5173. Vite
forwards each `/api` request to the backend container. For details, see the
comments in `compose.yaml` and `frontend/vite.config.js`.

### Run in production

The `compose.prod.yaml` file layers production settings on top of
`compose.yaml`: Gunicorn runs the API, nginx serves the built frontend, and
containers restart on their own. To start it, run the following command:

```bash
docker compose -f compose.yaml -f compose.prod.yaml up -d --build
```

The frontend container, `mad3-frontend`, publishes no port. It joins an
external Docker network called `edge`, where a reverse proxy such as Caddy
reaches it on port 80 and adds HTTPS. If the network doesn't exist, create it
with `docker network create edge`.

## Run without Docker

### Before you begin

Install the following:

- Python 3.11 or later, and [uv](https://docs.astral.sh/uv/) (or plain `pip`).
- Node.js 20 or later.
- Redis. On macOS, run `brew install redis`. On Ubuntu, run
  `sudo apt install redis-server`.

### Start each part

You need four terminals, one for each running part.

1.  Start Redis:

    ```bash
    redis-server
    ```

1.  Set up and start the backend:

    ```bash
    cd backend
    uv venv && uv pip install -r requirements.txt
    .venv/bin/python seed.py
    .venv/bin/python app.py
    ```

    The API runs at `http://127.0.0.1:5000/api`. To check it, open
    `http://127.0.0.1:5000/api/students`.

1.  Start the Celery worker:

    ```bash
    cd backend
    .venv/bin/celery -A celery_worker.celery worker --loglevel=info
    ```

1.  Start the frontend:

    ```bash
    cd frontend
    npm install
    npm run dev
    ```

    Open `http://localhost:5173`.

If you use `pip` instead of `uv`, create the environment with
`python3 -m venv .venv` and install with `.venv/bin/pip install -r requirements.txt`.

## Demo for the viva

The following steps show each technology doing its job:

1.  **REST and the database:** on the **Students** page, add a student.
    Then try to add the same roll number again. The API returns `409 Conflict`
    and the page shows the error.
1.  **Redis cache:** on the **Exams** page, click **Stats** twice. The first
    time, the badge says "Computed from DB". The second time, it says
    "From Redis cache".
1.  **Cache invalidation:** on the **Results** page, add a result for that
    exam. Go back and click **Stats**. The badge says "Computed from DB"
    again, because adding a result deleted the cached stats.
1.  **Celery background job:** click **Notify students**. The page responds
    at once, while the worker terminal prints one line every half second.
    When the worker finishes, the badge turns to `SUCCESS`.
1.  **Report download:** click **Generate report**, then click the download
    link when it appears.

## Troubleshooting

- **Requests to port 5000 fail with an empty 403 on macOS.** AirPlay Receiver
  also listens on port 5000. The frontend calls `127.0.0.1` to avoid it. You
  can also turn off AirPlay Receiver in **System Settings > General >
  AirDrop & Handoff**.
- **Background jobs stay `PENDING`.** The Celery worker isn't running, or
  Redis isn't running. Check both terminals.
- **Celery uses the `solo` pool.** The worker runs one job at a time. The
  default pool starts child processes, which fails on macOS and Windows. For
  details, see the comment in `backend/extensions.py`.

## Learn more

For likely viva questions with short answers, see [VIVA.md](VIVA.md).
