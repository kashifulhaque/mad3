"""Background jobs that the Celery worker runs.

Flask never runs these functions itself. A route calls task.delay(exam_id),
which puts a message on the Redis queue. The Celery worker process, started
from celery_worker.py, reads the message and runs the function. Whatever the
function returns goes to the Celery result backend, where
GET /api/tasks/<task_id> reads it.

These tasks query the database, so they need a Flask application context.
celery_worker.py provides one; see that file for details.
"""

import csv
import os
import time

from celery.utils.log import get_task_logger

from config import Config
from extensions import celery, db
from models import Exam

logger = get_task_logger(__name__)


@celery.task
def generate_exam_report(exam_id):
    """Writes a CSV file with every result for an exam.

    Returns:
        A dictionary with the name of the CSV file in the reports folder.
    """
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        raise ValueError(f"Exam {exam_id} not found")

    os.makedirs(Config.REPORTS_DIR, exist_ok=True)
    filename = f"exam_{exam_id}_report.csv"
    path = os.path.join(Config.REPORTS_DIR, filename)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["roll_no", "name", "email", "marks", "max_marks", "passed"])
        for result in exam.results:
            student = result.student
            writer.writerow([
                student.roll_no,
                student.name,
                student.email,
                result.marks,
                exam.max_marks,
                "yes" if result.passed() else "no",
            ])

    logger.info("Wrote report for exam %s to %s", exam_id, path)
    return {"filename": filename}


@celery.task
def notify_students(exam_id):
    """Pretends to email each student their result for an exam.

    The task logs one line per student instead of sending real email. The
    half-second pause stands in for the time a mail server takes, so you can
    see the request return at once while the worker keeps going.

    Returns:
        A dictionary with the number of students notified.
    """
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        raise ValueError(f"Exam {exam_id} not found")

    for result in exam.results:
        student = result.student
        status = "passed" if result.passed() else "did not pass"
        time.sleep(0.5)
        logger.info(
            "Email to %s: you scored %s/%s in %s and %s.",
            student.email,
            result.marks,
            exam.max_marks,
            exam.title,
            status,
        )

    return {"notified": len(exam.results)}
