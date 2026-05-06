import sqlite3

DB_PATH = "motion_alerts.db"

# Print verification that this is an SQLite database file (header bytes)
with open(DB_PATH, "rb") as f:
    header = f.read(16)
print(f"Database file: {DB_PATH}")
print(f"Header bytes: {header!r} (should start with b'SQLite format 3')")

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("Tables in database:")
    for t in tables:
        print(" -", t[0])

    print("\nContents of 'alerts' table:")
    cursor.execute("SELECT id, timestamp, photo_path, message FROM alerts ORDER BY id;")
    rows = cursor.fetchall()
    if not rows:
        print(" (no rows found)")
    else:
        print("ID | Timestamp | Photo Path | Message")
        print("-" * 70)
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")

    # optionally write to CSV
    with open("alerts_export.csv", "w", encoding="utf-8") as f:
        f.write("id,timestamp,photo_path,message\n")
        for row in rows:
            # escape commas in fields if needed
            f.write(",".join([str(x).replace(",", "\\,") for x in row]) + "\n")

print("\nExported results to alerts_export.csv")
