# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teacher-only sign up and unregister actions via Admin Mode
- Teacher login/logout endpoints with session token
- SQLite persistence for activities, students, and enrollments (SQLAlchemy)

## Getting Started

1. Install the dependencies:

   ```
   pip install -r ../requirements.txt
   ```

2. Run the application:

   ```
   uvicorn app:app --reload
   ```

3. Optional: initialize database manually (normally auto-runs on startup):

   ```
   python init_db.py
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister from an activity (teacher login required)               |
| POST   | `/auth/login`                                                     | Log in as teacher and get token                                     |
| POST   | `/auth/logout`                                                    | Log out and invalidate token                                        |
| GET    | `/auth/session`                                                   | Validate current teacher session token                              |

For signup/unregister requests, include the token in header `X-Admin-Token`.

## Teacher Accounts

Teacher usernames and passwords are stored in `teachers.json` and checked by the backend.

Default credentials:

- `ms.smith` / `smith-2026`
- `mr.johnson` / `johnson-2026`

## Data Model

The application uses SQLite via SQLAlchemy with these tables:

1. **activities**

   - Name (unique)
   - Description
   - Schedule
   - Maximum number of participants

2. **students**

   - Email (unique)
   - Optional name and grade fields

3. **activity_enrollments**

   - Activity and student references
   - Enrollment timestamp
   - Unique constraint to prevent duplicate enrollment

## Initialization and Seed Data

- Database file: `activities.db`
- Seed fixture: `activities_seed.json`
- On first run, the app creates tables and seeds initial activities/participants.
