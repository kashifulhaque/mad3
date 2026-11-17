"""Database tables for students, exams, and results.

Each class maps to one SQLite table through SQLAlchemy. Each class also has a
to_dict() method that turns a row into a plain dictionary, which Flask then
sends to the frontend as JSON.
"""

from extensions import db

# A student passes an exam when their marks reach this share of max_marks.
PASS_PERCENTAGE = 0.40


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)

    # The cascade option deletes a student's results when you delete the
    # student, so no result points at a student who no longer exists.
    results = db.relationship(
        "Result", backref="student", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "roll_no": self.roll_no,
            "email": self.email,
        }


class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)

    results = db.relationship("Result", backref="exam", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "subject": self.subject,
            # isoformat() turns a date into a "YYYY-MM-DD" string.
            "exam_date": self.exam_date.isoformat(),
            "max_marks": self.max_marks,
        }


class Result(db.Model):
    __tablename__ = "results"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    marks = db.Column(db.Float, nullable=False)

    # The database itself rejects a second result for the same student and
    # exam, even if a bug in the route code lets one through.
    __table_args__ = (db.UniqueConstraint("student_id", "exam_id"),)

    def passed(self):
        return self.marks >= PASS_PERCENTAGE * self.exam.max_marks

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "exam_id": self.exam_id,
            "marks": self.marks,
            "student_name": self.student.name,
            "exam_title": self.exam.title,
            "passed": self.passed(),
        }
