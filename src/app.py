"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from datetime import datetime
from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
from pathlib import Path
import json
import secrets
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.exc import IntegrityError

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


class LoginRequest(BaseModel):
    username: str
    password: str


class Base(DeclarativeBase):
    pass


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    schedule: Mapped[str] = mapped_column(String(300), nullable=False)
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False)
    enrollments: Mapped[list["ActivityEnrollment"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    enrollments: Mapped[list["ActivityEnrollment"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )


class ActivityEnrollment(Base):
    __tablename__ = "activity_enrollments"
    __table_args__ = (
        UniqueConstraint("activity_id", "student_id", name="uq_activity_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    activity: Mapped[Activity] = relationship(back_populates="enrollments")
    student: Mapped[Student] = relationship(back_populates="enrollments")


teachers_file = current_dir / "teachers.json"
with open(teachers_file, "r", encoding="utf-8") as file:
    teacher_credentials = json.load(file)

db_file = current_dir / "activities.db"
seed_file = current_dir / "activities_seed.json"
engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# Simple in-memory sessions for teacher mode.
admin_sessions = {}

def initialize_database() -> None:
    """Create database tables and seed initial data on first run."""
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        has_activities = db.query(Activity.id).first() is not None
        if has_activities:
            return

        with open(seed_file, "r", encoding="utf-8") as file:
            seed_activities = json.load(file)

        for activity_name, details in seed_activities.items():
            activity = Activity(
                name=activity_name,
                description=details["description"],
                schedule=details["schedule"],
                max_participants=details["max_participants"],
            )
            db.add(activity)
            db.flush()

            for email in details.get("participants", []):
                student = db.query(Student).filter(Student.email == email).first()
                if student is None:
                    student = Student(email=email)
                    db.add(student)
                    db.flush()

                db.add(ActivityEnrollment(activity_id=activity.id, student_id=student.id))

        db.commit()


def activity_to_response(db, activity: Activity) -> dict:
    enrollment_rows = (
        db.query(Student.email)
        .join(ActivityEnrollment, ActivityEnrollment.student_id == Student.id)
        .filter(ActivityEnrollment.activity_id == activity.id)
        .order_by(Student.email.asc())
        .all()
    )
    participants = [row[0] for row in enrollment_rows]
    return {
        "description": activity.description,
        "schedule": activity.schedule,
        "max_participants": activity.max_participants,
        "participants": participants,
    }


@app.on_event("startup")
def on_startup() -> None:
    initialize_database()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    with SessionLocal() as db:
        activity_rows = db.query(Activity).order_by(Activity.name.asc()).all()
        response = {}
        for activity in activity_rows:
            response[activity.name] = activity_to_response(db, activity)
        return response


@app.post("/auth/login")
def login(login_request: LoginRequest):
    """Authenticate a teacher and issue a temporary auth token."""
    expected_password = teacher_credentials.get(login_request.username)
    if expected_password is None or expected_password != login_request.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = secrets.token_urlsafe(24)
    admin_sessions[token] = login_request.username
    return {
        "message": f"Logged in as {login_request.username}",
        "token": token,
        "username": login_request.username
    }


@app.post("/auth/logout")
def logout(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    """Invalidate a teacher auth token."""
    if x_admin_token and x_admin_token in admin_sessions:
        admin_sessions.pop(x_admin_token)
    return {"message": "Logged out"}


@app.get("/auth/session")
def get_session(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    """Return current session details for the provided auth token."""
    if not x_admin_token or x_admin_token not in admin_sessions:
        return {"is_admin": False}

    return {"is_admin": True, "username": admin_sessions[x_admin_token]}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")
):
    """Sign up a student for an activity"""
    if not x_admin_token or x_admin_token not in admin_sessions:
        raise HTTPException(
            status_code=403,
            detail="Teacher login required for signup"
        )

    with SessionLocal() as db:
        activity = db.query(Activity).filter(Activity.name == activity_name).first()
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        student = db.query(Student).filter(Student.email == email).first()
        if student is None:
            student = Student(email=email)
            db.add(student)
            db.flush()

        existing = (
            db.query(ActivityEnrollment)
            .filter(
                ActivityEnrollment.activity_id == activity.id,
                ActivityEnrollment.student_id == student.id,
            )
            .first()
        )
        if existing is not None:
            raise HTTPException(
                status_code=400,
                detail="Student is already signed up"
            )

        db.add(ActivityEnrollment(activity_id=activity.id, student_id=student.id))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Student is already signed up"
            )

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")
):
    """Unregister a student from an activity"""
    if not x_admin_token or x_admin_token not in admin_sessions:
        raise HTTPException(
            status_code=403,
            detail="Teacher login required for unregister"
        )

    with SessionLocal() as db:
        activity = db.query(Activity).filter(Activity.name == activity_name).first()
        if activity is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        student = db.query(Student).filter(Student.email == email).first()
        if student is None:
            raise HTTPException(
                status_code=400,
                detail="Student is not signed up for this activity"
            )

        enrollment = (
            db.query(ActivityEnrollment)
            .filter(
                ActivityEnrollment.activity_id == activity.id,
                ActivityEnrollment.student_id == student.id,
            )
            .first()
        )
        if enrollment is None:
            raise HTTPException(
                status_code=400,
                detail="Student is not signed up for this activity"
            )

        db.delete(enrollment)
        db.commit()

    return {"message": f"Unregistered {email} from {activity_name}"}
