import sqlite3

conn = sqlite3.connect("doc_sage.sqlite")
cursor = conn.cursor()

# 'source' table
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS source (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        topic TEXT NOT NULL,
        source_text TEXT,
        type TEXT DEFAULT "document"
    )
"""
)

conn.commit()

conn.close()

print("Table created successfuly")