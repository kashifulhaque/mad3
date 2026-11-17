"""REST API endpoints for the Examination Management System.

All endpoints live on one Flask Blueprint. A Blueprint is a group of routes
that you define apart from the app and then attach to it in create_app().
This lets you write routes without importing the app object, and it puts the
shared /api prefix in one place instead of on every route.

The endpoints follow API_CONTRACT.md, which the Vue frontend also follows.
"""

import json
import os
from datetime import date

from celery.result import AsyncResult
from flask import Blueprint, jsonify, request, send_from_directory

from config import Config
from extensions import celery, db, redis_client
from models import Exam, Result, Student
from tasks import generate_exam_report, notify_students

api = Blueprint("api", __name__, url_prefix="/api")


def error(message, status):
    """Returns a JSON error body with the given HTTP status code."""
    return jsonify({"error": message}), status


def stats_cache_key(exam_id):
    return f"exam_stats:{exam_id}"


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------


@api.get("/students")
def list_students():
    students = Student.query.order_by(Student.id).all()
    return jsonify([s.to_dict() for s in students])


@api.post("/students")
def create_student():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    roll_no = str(data.get("roll_no", "")).strip()
    email = str(data.get("email", "")).strip()

    if not name or not roll_no or not email:
        return error("name, roll_no and email are required", 400)
    if Student.query.filter_by(roll_no=roll_no).first():
        return error(f"A student with roll_no {roll_no} already exists", 409)

    student = Student(name=name, roll_no=roll_no, email=email)
    db.session.add(student)
    db.session.commit()
    return jsonify(student.to_dict()), 201


@api.delete("/students/<int:student_id>")
def delete_student(student_id):
    student = db.session.get(Student, student_id)
    if student is None:
        return error("Student not found", 404)

    # Deleting the student also deletes their results, which changes the
    # stats of every exam they sat. Remove those cached stats too.
    for result in student.results:
        redis_client.delete(stats_cache_key(result.exam_id))

    db.session.delete(student)
    db.session.commit()
    return "", 204


# ---------------------------------------------------------------------------
# Exams
# ---------------------------------------------------------------------------


@api.get("/exams")
def list_exams():
    exams = Exam.query.order_by(Exam.exam_date).all()
    return jsonify([e.to_dict() for e in exams])


@api.post("/exams")
def create_exam():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    subject = str(data.get("subject", "")).strip()

    if not title or not subject:
        return error("title and subject are required", 400)

    try:
        exam_date = date.fromisoformat(str(data.get("exam_date", "")))
    except ValueError:
        return error("exam_date must be in YYYY-MM-DD format", 400)

    try:
        max_marks = int(data.get("max_marks"))
    except (TypeError, ValueError):
        return error("max_marks must be a whole number", 400)
    if max_marks <= 0:
        return error("max_marks must be greater than 0", 400)

    exam = Exam(title=title, subject=subject, exam_date=exam_date, max_marks=max_marks)
    db.session.add(exam)
    db.session.commit()
    return jsonify(exam.to_dict()), 201


@api.delete("/exams/<int:exam_id>")
def delete_exam(exam_id):
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        return error("Exam not found", 404)

    db.session.delete(exam)
    db.session.commit()
    redis_client.delete(stats_cache_key(exam_id))
    return "", 204


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


@api.get("/results")
def list_results():
    query = Result.query
    # type=int makes Flask convert the value, or ignore it if it isn't a number.
    exam_id = request.args.get("exam_id", type=int)
    if exam_id is not None:
        query = query.filter_by(exam_id=exam_id)
    results = query.order_by(Result.id).all()
    return jsonify([r.to_dict() for r in results])


@api.post("/results")
def create_result():
    data = request.get_json(silent=True) or {}

    try:
        student_id = int(data.get("student_id"))
        exam_id = int(data.get("exam_id"))
        marks = float(data.get("marks"))
    except (TypeError, ValueError):
        return error("student_id, exam_id and marks are required numbers", 400)

    student = db.session.get(Student, student_id)
    if student is None:
        return error("Student not found", 404)
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        return error("Exam not found", 404)

    if marks < 0 or marks > exam.max_marks:
        return error(f"marks must be between 0 and {exam.max_marks}", 400)
    if Result.query.filter_by(student_id=student_id, exam_id=exam_id).first():
        return error("This student already has a result for this exam", 409)

    result = Result(student_id=student_id, exam_id=exam_id, marks=marks)
    db.session.add(result)
    db.session.commit()

    # Cache invalidation: the cached stats for this exam no longer match the
    # database, so delete them. The next GET /stats recomputes fresh numbers.
    redis_client.delete(stats_cache_key(exam_id))

    return jsonify(result.to_dict()), 201


# ---------------------------------------------------------------------------
# Exam statistics (cached in Redis)
# ---------------------------------------------------------------------------


def compute_exam_stats(exam):
    """Calculates exam statistics from the results stored in SQLite."""
    results = exam.results
    marks = [r.marks for r in results]
    pass_count = sum(1 for r in results if r.passed())

    return {
        "exam_id": exam.id,
        "count": len(marks),
        # An exam with no results reports 0 instead of failing on an empty list.
        "average": round(sum(marks) / len(marks), 2) if marks else 0,
        "highest": max(marks) if marks else 0,
        "lowest": min(marks) if marks else 0,
        "pass_count": pass_count,
        "fail_count": len(marks) - pass_count,
    }


@api.get("/exams/<int:exam_id>/stats")
def exam_stats(exam_id):
    # This endpoint uses the cache-aside pattern:
    #   1. Look in the cache (Redis) first.
    #   2. On a hit, return the cached value and skip the database.
    #   3. On a miss, compute the value from the database, store it in the
    #      cache for next time, and return it.
    # Redis keeps data in memory, so a hit is much cheaper than querying and
    # aggregating every result row in SQLite.
    key = stats_cache_key(exam_id)

    cached = redis_client.get(key)
    if cached is not None:
        stats = json.loads(cached)
        stats["cached"] = True
        return jsonify(stats)

    exam = db.session.get(Exam, exam_id)
    if exam is None:
        return error("Exam not found", 404)

    stats = compute_exam_stats(exam)
    # Redis stores strings, so you store the dictionary as JSON text. The ex
    # argument makes Redis delete the key on its own after 60 seconds.
    redis_client.set(key, json.dumps(stats), ex=Config.STATS_CACHE_SECONDS)

    stats["cached"] = False
    return jsonify(stats)


# ---------------------------------------------------------------------------
# Background tasks (Celery)
# ---------------------------------------------------------------------------
# Writing a report or emailing every student can take a long time. If the
# request did that work itself, the browser would wait until it finished.
# Instead, the route calls .delay(), which puts a message on the Redis queue
# and returns at once with a task ID. A separate Celery worker process picks
# up the message and does the work. The frontend polls GET /tasks/<task_id>
# to find out when the work is done.


@api.post("/exams/<int:exam_id>/report")
def start_report(exam_id):
    if db.session.get(Exam, exam_id) is None:
        return error("Exam not found", 404)
    task = generate_exam_report.delay(exam_id)
    # 202 Accepted means the server accepted the job but hasn't finished it.
    return jsonify({"task_id": task.id}), 202


@api.post("/exams/<int:exam_id>/notify")
def start_notify(exam_id):
    if db.session.get(Exam, exam_id) is None:
        return error("Exam not found", 404)
    task = notify_students.delay(exam_id)
    return jsonify({"task_id": task.id}), 202


@api.get("/tasks/<task_id>")
def task_status(task_id):
    # AsyncResult reads the task's state and return value from the Celery
    # result backend (Redis). Celery reports PENDING for any ID it doesn't
    # know yet, so this endpoint never returns 404.
    task = AsyncResult(task_id, app=celery)

    if task.state == "SUCCESS":
        result = task.result
    elif task.state == "FAILURE":
        # On failure, task.result holds the exception. Send its message.
        result = {"error": str(task.result)}
    else:
        result = None

    return jsonify({"task_id": task_id, "state": task.state, "result": result})


# ---------------------------------------------------------------------------
# Report downloads
# ---------------------------------------------------------------------------


@api.get("/reports/<filename>")
def download_report(filename):
    # The <filename> part of the URL can't contain a slash, and
    # send_from_directory also refuses paths that leave REPORTS_DIR. Together
    # they stop a request like /reports/../config.py from reading other files.
    if not os.path.isfile(os.path.join(Config.REPORTS_DIR, filename)):
        return error("Report not found", 404)
    return send_from_directory(Config.REPORTS_DIR, filename, as_attachment=True)
