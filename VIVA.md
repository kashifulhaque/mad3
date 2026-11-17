# Viva guide

This guide lists questions examiners often ask about this project, with short
answers and the file to point at. Read the file alongside each answer.

## The big picture

**Explain the project in one minute.**
It's an examination management system with a separate frontend and backend.
The Vue frontend calls a Flask REST API, which stores data in SQLite through
SQLAlchemy. Redis caches exam statistics and acts as the message broker for
Celery, which runs slow jobs like report generation in the background.

**Why separate the frontend and backend?**
Each part has one job and can change on its own. The backend exposes data as
JSON, so a mobile app could use the same API. The two parts agree only on the
URLs and JSON shapes in `API_CONTRACT.md`.

**Walk through what happens when you add a result.**

1.  `ResultsView.vue` calls `createResult()` in `api.js`.
1.  `api.js` sends `POST /api/results` with a JSON body.
1.  `create_result()` in `routes.py` validates the input and checks that the
    student and exam exist.
1.  SQLAlchemy inserts a row into the `results` table.
1.  The route deletes the Redis key `exam_stats:<exam_id>`.
1.  Flask returns the new result as JSON with status `201 Created`.
1.  Vue adds it to the reactive list, and the table re-renders.

## Backend: Flask and REST

**What is REST?**
A style of API design where URLs name resources (`/students`) and HTTP
methods say what to do: `GET` reads, `POST` creates, `DELETE` removes. Each
request carries everything the server needs, so the server keeps no session
state between requests.

**Which HTTP status codes do you use, and why?**

| Code  | Meaning              | Where                                           |
|-------|----------------------|-------------------------------------------------|
| `200` | OK                   | Successful `GET`.                               |
| `201` | Created              | Successful `POST` of a student, exam, or result. |
| `202` | Accepted             | A background job started but hasn't finished.   |
| `204` | No content           | Successful `DELETE`.                            |
| `400` | Bad request          | Missing or invalid fields.                      |
| `404` | Not found            | Unknown ID.                                     |
| `409` | Conflict             | Duplicate roll number or duplicate result.      |

**What is a Blueprint?** (`routes.py`)
A group of routes you define apart from the app and attach later with
`app.register_blueprint()`. It keeps the `/api` prefix in one place and lets
`routes.py` avoid importing the app object.

**What is the application factory pattern?** (`app.py`)
`create_app()` builds and returns the Flask app instead of creating it at
import time. The server, the Celery worker, and `seed.py` each call it to get
the same configured app.

**What is CORS, and why do you need it?** (`app.py`)
Browsers block a page on one origin (`localhost:5173`) from reading responses
from another origin (`127.0.0.1:5000`) unless the server allows it.
Flask-CORS adds the `Access-Control-Allow-Origin` header that allows it.

**What is the application context?** (`celery_worker.py`)
Flask-SQLAlchemy needs to know which app's database to use. During a request,
Flask provides that through the application context. The Celery worker isn't
handling requests, so it pushes a context once at startup.

## Database: SQLite and SQLAlchemy

**What is an ORM?** (`models.py`)
An object-relational mapper lets you work with database rows as Python
objects. You write `Student.query.all()` instead of `SELECT * FROM students`,
and SQLAlchemy generates the SQL.

**Describe the tables and their relationships.**
`students` and `exams` have a many-to-many relationship through `results`.
Each result row has a foreign key to one student and one exam, plus the
marks. A unique constraint on `(student_id, exam_id)` stops a student from
getting two results for the same exam.

**Why SQLite?**
It needs no server. The whole database is one file, `backend/exams.db`, which
suits a college project. To switch to PostgreSQL or MySQL, you change only
`SQLALCHEMY_DATABASE_URI` in `config.py`.

**What happens to results when you delete a student?**
They're deleted too, through a cascade on the relationship in `models.py`.
The route also clears cached stats for every affected exam.

## Redis caching

**What is Redis?**
An in-memory key-value store. Reads are fast because the data lives in RAM.
This project uses one Redis server for three jobs: the stats cache, the
Celery broker, and the Celery result backend.

**Explain the cache-aside pattern.** (`exam_stats()` in `routes.py`)

1.  Look for the key `exam_stats:<id>` in Redis.
1.  On a hit, return it without touching the database.
1.  On a miss, compute the stats from SQLite, store them in Redis for 60
    seconds, and return them.

**What is cache invalidation, and where do you do it?**
Deleting cached data when the source data changes, so readers never see stale
values. `create_result()`, `delete_student()`, and `delete_exam()` each delete
the affected `exam_stats` keys.

**What is TTL?**
Time to live. `redis_client.set(key, value, ex=60)` tells Redis to delete the
key after 60 seconds, even if nothing invalidates it.

**How do you show the cache works?**
The stats response includes `"cached": true` or `false`, and the Exams page
shows it as a badge.

## Celery background jobs

**Why use Celery?**
Some work is slow, like writing a report or emailing every student. If the
web request did it, the browser would wait. Celery moves that work to a
separate worker process, so the API responds at once.

**How does a job flow through the system?**

1.  The route calls `generate_exam_report.delay(exam_id)`.
1.  Celery puts a message on the Redis queue and returns a task ID.
1.  Flask returns `{"task_id": ...}` with status `202 Accepted`.
1.  The worker takes the message from the queue and runs the function.
1.  The worker stores the return value in Redis (the result backend).
1.  `TaskStatus.vue` calls `GET /api/tasks/<id>` every second until the state
    is `SUCCESS` or `FAILURE`.

**What is a broker? What is a result backend?**
The broker is the queue that carries job messages from Flask to the worker.
The result backend stores each job's state and return value. Redis does both
here.

**What are the task states?**
`PENDING` (queued or unknown), `STARTED` (running), `SUCCESS`, and `FAILURE`.
`task_track_started = True` in `extensions.py` turns on `STARTED`.

**Why poll instead of pushing the result to the browser?**
Polling needs only plain HTTP and fits in a few lines. WebSockets or
server-sent events would push updates instantly but add complexity.

**What is the `solo` pool?**
The worker runs jobs one at a time in its own process. The default pool forks
child processes, which fails on macOS and Windows. For this project, one job
at a time is enough.

## Frontend: Vue, Vite, and Bootstrap

**What is Vite?**
A build tool and dev server. In development, it serves files as native ES
modules and reloads the page instantly when you save. `npm run build` bundles
the app for production.

**What does `ref()` do?**
It makes a value reactive. When you change `students.value`, Vue re-renders
every part of the template that uses `students`.

**What is `onMounted()`?**
A lifecycle hook that runs after Vue puts the component on the page. Each
view loads its data from the API there.

**What's the difference between `ref()` and `computed()`?**
You set a `ref` yourself. A `computed` value derives from other reactive
values, and Vue recalculates it when they change. For example, the student
search box in `StudentsView.vue` updates `search`, and `filteredStudents`
recalculates on its own.

**How does dark mode work?** (`App.vue`)
Bootstrap 5.3 has a built-in dark theme. The toggle button sets
`data-bs-theme="dark"` on the `<html>` element, and every Bootstrap
component switches its colors.

**Explain `v-model`, `v-for`, and `v-if`.**

- `v-model` keeps a form input and a variable in sync, both ways.
- `v-for` repeats an element for each item in a list. `:key` gives each item
  a stable identity so Vue updates the right row.
- `v-if` adds or removes an element based on a condition.

**What is `<script setup>`?**
A shorter way to write a component with the Composition API. Variables and
functions you declare there are available in the template directly.

**Why put every API call in `api.js`?**
The base URL and error handling live in one place. Views call named
functions like `getStudents()` instead of repeating `fetch` code.

**What does vue-router do?** (`router.js`)
It maps URLs like `/students` to view components and swaps them into
`<router-view>` in `App.vue` without reloading the page. That makes the app a
single-page application (SPA).

**What does Bootstrap provide?**
Ready-made CSS classes for layout (`container`, `row`, `col`), tables, forms,
buttons, badges, cards, and the navbar. The project uses only the CSS, with
no Bootstrap JavaScript.

## Docker

**What does `docker compose up` do?** (`compose.yaml`)
It builds an image for each service that has a `Dockerfile`, then starts one
container per service: `redis`, `backend`, `worker`, and `frontend`. Compose
puts them on a private network where each container reaches another by its
service name, such as `redis:6379`.

**What's the difference between an image and a container?**
An image is a read-only template with the OS, packages, and code. A container
is a running instance of an image. The `backend` and `worker` services start
two containers from the same image with different commands.

**How do the backend and worker share the SQLite database?**
Both mount the named volume `app-data` at `/data`. The volume also keeps
the data when containers stop. `docker compose down -v` deletes it.

**Why doesn't the browser call the backend directly in Docker?**
The browser runs on your computer, outside the Docker network, so it can't
resolve the name `backend`. Instead, it calls `/api` on the frontend, and the
Vite dev server forwards those requests to `http://backend:5000`. Because the
browser sees only one origin, CORS doesn't apply.

## Limitations and improvements

Examiners often ask what you'd add next. Good answers include the following:

- **Authentication:** add login with JWT tokens, and roles for admins and
  students.
- **Real email:** replace the simulated notification with Flask-Mail or an
  email service.
- **Migrations:** use Flask-Migrate (Alembic) to change tables without losing
  data.
- **Scheduled jobs:** use Celery Beat to send exam reminders automatically.
- **Tests:** add `pytest` tests for the API and Vitest tests for components.
- **Deployment:** run Flask with Gunicorn, serve the built frontend with
  Nginx instead of the Vite dev server, and use PostgreSQL instead of SQLite.
