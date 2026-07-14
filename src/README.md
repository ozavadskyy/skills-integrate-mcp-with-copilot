# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teacher-only sign up and unregister actions via Admin Mode
- Teacher login/logout endpoints with session token

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
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

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
