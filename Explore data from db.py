import sqlite3

conn = sqlite3.connect(r"D:\projects\Courses\exam system (2)\exam system\data.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

if not tables:
    print("There is no table in the database.")
    cursor.close()
    conn.close()
    exit()

for table_name in tables:
    table_name = table_name[0]
    print(f"\n===== Table: {table_name} =====")

    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    column_names = [description[0] for description in cursor.description]
    print(" | ".join(column_names))
    print("-" * 40)


    for row in rows:
        print(" | ".join(str(item) for item in row))

cursor.close()
conn.close()