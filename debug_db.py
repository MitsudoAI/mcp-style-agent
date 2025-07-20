#!/usr/bin/env python3

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Enable logging
logging.basicConfig(level=logging.INFO)

from mcps.deep_thinking.data.database import ThinkingDatabase

# Test database creation
print("Testing database creation...")
try:
    db = ThinkingDatabase(':memory:')
    print("Database created successfully")
except Exception as e:
    print(f"Error creating database: {e}")
    import traceback
    traceback.print_exc()

# Test table creation
print("Testing table creation...")
try:
    with db.get_connection() as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables found: {[table[0] for table in tables]}")
except Exception as e:
    print(f"Error checking tables: {e}")
    import traceback
    traceback.print_exc()

# Test session creation
print("Testing session creation...")
try:
    success = db.create_session(
        session_id="test-session",
        topic="Test topic",
        session_type="test_flow"
    )
    print(f"Session creation success: {success}")
except Exception as e:
    print(f"Error creating session: {e}")
    import traceback
    traceback.print_exc()

# Test session retrieval
print("Testing session retrieval...")
try:
    session = db.get_session("test-session")
    print(f"Session retrieved: {session is not None}")
    if session:
        print(f"Session data: {session}")
except Exception as e:
    print(f"Error retrieving session: {e}")
    import traceback
    traceback.print_exc()