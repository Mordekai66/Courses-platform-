import sqlite3

conn = sqlite3.connect("data.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM students")
table = cursor.fetchall()

if not table:
    print("There is no table in the database.")
    cursor.close()
    conn.close()
    exit()

for row in table:
    print(" | ".join(str(item) for item in row))

cursor.close()
conn.close()
