import mysql.connector

# الاتصال بقاعدة البيانات
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="abdo.123",  # ← غيّرها
    database="courses_db"
)
cursor = db.cursor()

def add_student():
    student_code = input("enter student code :").strip()
    name = input("enter student name :").strip()
    email = input("enter student email :").strip()
    course = input("enter student course :").strip()

    try:
        cursor.execute("""
            INSERT INTO students (student_code, name, email, course)
            VALUES (%s, %s, %s, %s)
        """, (student_code, name, email if email else None, course))
        db.commit()
        print(f"✅ تم إضافة {name}")
    except mysql.connector.Error as err:
        print(f"❌ خطأ: {err}")

while True:
    add_student()
    if input("هل تريد إضافة طالب آخر؟ (نعم/لا): ").strip().lower() != 'نعم':
        break

cursor.close()
db.close()
