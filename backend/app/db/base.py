import sqlite3

def get_db():
    # Connect to SQLite database (thread-safe disabled for FastAPI compatibility)
    conn = sqlite3.connect("app/database/data.db", check_same_thread=False)
    try:
        # Yield the connection object for use (e.g., in dependency injection)
        yield conn
    finally:
        # Ensure the connection is closed after use
        conn.close()
