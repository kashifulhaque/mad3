"""Fills the database with sample data for a demo.

Run `python seed.py` once before you start the server. The script deletes all
existing students, exams, and results, then inserts a fresh sample set. It
also clears cached exam stats in Redis so they match the new data.
"""

from datetime import date

from app import create_app
from extensions import db, redis_client
from models import Exam, Result, Student

STUDENTS = [
    ("Asha Verma", "CS001", "asha@college.edu"),
    ("Rahul Mehta", "CS002", "rahul@college.edu"),
    ("Priya Nair", "CS003", "priya@college.edu"),
    ("Arjun Singh", "CS004", "arjun@college.edu"),
    ("Fatima Khan", "CS005", "fatima@college.edu"),
    ("Daniel Joseph", "CS006", "daniel@college.edu"),
]

# Marks for each student, in the same order as STUDENTS.
MIDTERM_MARKS = [72.5, 35, 88, 54, 91, 20]
QUIZ_MARKS = [18, 9, 15, 7, 20]  # Daniel hasn't taken the quiz yet.


def seed():
    app = create_app()
    # Database queries outside a request need an application context.
    with app.app_context():
        # Delete results first, because they point at students and exams.
        Result.query.delete()
        Student.query.delete()
        Exam.query.delete()

        students = [Student(name=n, roll_no=r, email=e) for n, r, e in STUDENTS]
        midterm = Exam(
            title="Mid-term",
            subject="DBMS",
            exam_date=date(2026, 12, 1),
            max_marks=100,
        )
        quiz = Exam(
            title="Quiz 1",
            subject="Operating Systems",
            exam_date=date(2026, 12, 10),
            max_marks=20,
        )
        db.session.add_all(students + [midterm, quiz])
        # flush() sends the inserts to the database so each row gets its id,
        # which the results need, without ending the transaction yet.
        db.session.flush()

        for student, marks in zip(students, MIDTERM_MARKS):
            db.session.add(Result(student_id=student.id, exam_id=midterm.id, marks=marks))
        for student, marks in zip(students, QUIZ_MARKS):
            db.session.add(Result(student_id=student.id, exam_id=quiz.id, marks=marks))

        db.session.commit()

        for key in redis_client.scan_iter("exam_stats:*"):
            redis_client.delete(key)

        print(f"Seeded {len(students)} students, 2 exams, and "
              f"{len(MIDTERM_MARKS) + len(QUIZ_MARKS)} results.")


if __name__ == "__main__":
    seed()
