# API contract

Shared agreement between `backend/` (Flask) and `frontend/` (Vue). Base URL: `http://127.0.0.1:5000/api`.
All bodies are JSON. Errors return `{"error": "<message>"}` with a 4xx status.

## Data model (SQLite via SQLAlchemy)

| Table    | Columns                                                              |
|----------|----------------------------------------------------------------------|
| students | id (PK), name, roll_no (unique), email                               |
| exams    | id (PK), title, subject, exam_date (YYYY-MM-DD), max_marks (int)     |
| results  | id (PK), student_id (FK), exam_id (FK), marks (float); unique (student_id, exam_id) |

A student passes an exam when `marks >= 40% of max_marks`.

## Endpoints

| Method | Path                         | Body / query                                   | Returns |
|--------|------------------------------|------------------------------------------------|---------|
| GET    | /students                    |                                                | `[Student]` |
| POST   | /students                    | `{name, roll_no, email}`                       | `Student`, 201 |
| DELETE | /students/<id>               |                                                | 204 |
| GET    | /exams                       |                                                | `[Exam]` |
| POST   | /exams                       | `{title, subject, exam_date, max_marks}`       | `Exam`, 201 |
| DELETE | /exams/<id>                  |                                                | 204 |
| GET    | /results                     | optional `?exam_id=`                           | `[Result]` |
| POST   | /results                     | `{student_id, exam_id, marks}`                 | `Result`, 201 |
| GET    | /exams/<id>/stats            |                                                | `Stats` (cached in Redis 60 s) |
| POST   | /exams/<id>/report           |                                                | `{task_id}`, 202 (starts Celery job) |
| POST   | /exams/<id>/notify           |                                                | `{task_id}`, 202 (starts Celery job) |
| GET    | /tasks/<task_id>             |                                                | `{task_id, state, result}` |
| GET    | /reports/<filename>          |                                                | CSV file download |

## Shapes

```json
Student: {"id": 1, "name": "Asha", "roll_no": "CS001", "email": "asha@college.edu"}
Exam:    {"id": 1, "title": "Mid-term", "subject": "DBMS", "exam_date": "2026-12-01", "max_marks": 100}
Result:  {"id": 1, "student_id": 1, "exam_id": 1, "marks": 72.5,
          "student_name": "Asha", "exam_title": "Mid-term", "passed": true}
Stats:   {"exam_id": 1, "count": 10, "average": 61.2, "highest": 95, "lowest": 20,
          "pass_count": 8, "fail_count": 2, "cached": false}
Task:    {"task_id": "abc", "state": "SUCCESS", "result": {"filename": "exam_1_report.csv"}}
```

`state` is one of Celery's states: `PENDING`, `STARTED`, `SUCCESS`, `FAILURE`.
For the report task, `result.filename` is passed to `GET /reports/<filename>`.
For the notify task, `result` is `{"notified": <count>}`.

## Caching rule

`GET /exams/<id>/stats` reads Redis key `exam_stats:<id>` first. On a miss it computes
from SQLite, stores the result for 60 seconds, and returns `"cached": false`.
`POST /results` deletes `exam_stats:<exam_id>` so stats never go stale.
