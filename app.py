from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="abdo.123",
        database="courses_db"
    )

# تسجيل الدخول
@app.route('/login', methods=['POST'])
def login():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        data = request.json
        student_code = data.get('student_code')

        if not student_code:
            return jsonify({'error': 'يجب إدخال كود الطالب'}), 400

        # تعديل هنا: المقارنة بدون مسافات وبـ lowercase
        cursor.execute(
            "SELECT * FROM students WHERE TRIM(LOWER(student_code)) = TRIM(LOWER(%s))",
            (student_code,)
        )
        student = cursor.fetchone()

        cursor.close()
        db.close()

        if student:
            return jsonify({'message': 'تم تسجيل الدخول', 'student': student})
        else:
            return jsonify({'error': 'كود الطالب غير صحيح'}), 401

    except mysql.connector.Error as err:
        return jsonify({'error': f'خطأ في قاعدة البيانات: {err}'}), 500
    except Exception as e:
        return jsonify({'error': f'خطأ غير متوقع: {e}'}), 500

# إضافة طالب
@app.route('/add_student', methods=['POST'])
def add_student():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        data = request.json
        query = """
            INSERT INTO students 
            (full_name, stage, age, email, phone, guardian_name, guardian_phone, student_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data.get('full_name'),
            data.get('stage'),
            data.get('age'),
            data.get('email'),
            data.get('phone'),
            data.get('guardian_name'),
            data.get('guardian_phone'),
            data.get('student_code')
        )

        cursor.execute(query, values)
        db.commit()

        cursor.close()
        db.close()

        return jsonify({'message': 'تمت إضافة الطالب بنجاح'}), 201

    except mysql.connector.Error as err:
        return jsonify({'error': f'خطأ في قاعدة البيانات: {err}'}), 500
    except Exception as e:
        return jsonify({'error': f'خطأ غير متوقع: {e}'}), 500

# عرض كل الطلاب
@app.route('/students', methods=['GET'])
def get_students():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()

        cursor.close()
        db.close()

        return jsonify(students)

    except mysql.connector.Error as err:
        return jsonify({'error': f'خطأ في قاعدة البيانات: {err}'}), 500
    except Exception as e:
        return jsonify({'error': f'خطأ غير متوقع: {e}'}), 500

# تعديل بيانات طالب
@app.route('/edit_student/<int:student_id>', methods=['PUT'])
def edit_student(student_id):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        data = request.json
        query = """
            UPDATE students
            SET full_name = %s,
                stage = %s,
                age = %s,
                email = %s,
                phone = %s,
                guardian_name = %s,
                guardian_phone = %s,
                student_code = %s
            WHERE id = %s
        """
        values = (
            data.get('full_name'),
            data.get('stage'),
            data.get('age'),
            data.get('email'),
            data.get('phone'),
            data.get('guardian_name'),
            data.get('guardian_phone'),
            data.get('student_code'),
            student_id
        )

        cursor.execute(query, values)
        db.commit()

        if cursor.rowcount == 0:
            cursor.close()
            db.close()
            return jsonify({'error': 'لا يوجد طالب بهذا الكود'}), 404       

        cursor.close()
        db.close()

        return jsonify({'message': 'تم تعديل بيانات الطالب بنجاح'})

    except mysql.connector.Error as err:
        return jsonify({'error': f'خطأ في قاعدة البيانات: {err}'}), 500
    except Exception as e:
        return jsonify({'error': f'خطأ غير متوقع: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
