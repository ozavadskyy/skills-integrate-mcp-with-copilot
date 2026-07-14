"""Initialize local SQLite database and seed activity data."""

from app import initialize_database


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")
