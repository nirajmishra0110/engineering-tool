import sqlite3

# Connect to SQLite database
def connect_db():
    return sqlite3.connect("doc_sage.sqlite")


def create_source(name, source_text, topic, source_type="document"):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO source (name, source_text, topic, type) VALUES (?, ?, ?, ?)",
        (name, source_text, topic, source_type),
    )
    conn.commit()
    conn.close()


def read_source(source_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM source WHERE id = ?", (source_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_source(source_id, new_name, new_source_text):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE source SET name = ?, source_text = ? WHERE id = ?",
        (new_name, new_source_text, source_id),
    )
    conn.commit()
    conn.close()


def list_sources(topic, source_type=None):
    conn = connect_db()
    cursor = conn.cursor()
    if source_type:
        cursor.execute(
            "SELECT * FROM source WHERE topic = ? AND type = ?",
            (topic, source_type),
        )
    else:
        cursor.execute("SELECT * FROM source WHERE topic = ?", (topic,))
    source = cursor.fetchall()
    conn.close()
    return source


def delete_source(source_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM source WHERE id = ?", (source_id,))
    conn.commit()
    conn.close()