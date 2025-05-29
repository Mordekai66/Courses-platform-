from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)


def get_db_connection():
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/login', methods=['POST'])
def login():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        data = request.json
        student_code = data.get('student_code')

        if not student_code:
            return jsonify({'error': 'يجب إدخال كود الطالب'}), 400

        cursor.execute(
            "SELECT * FROM students WHERE TRIM(LOWER(student_code)) = TRIM(LOWER(?))",
            (student_code,)
        )
        student = cursor.fetchone()

        db.close()

        if student:
            return jsonify({'message': 'تم تسجيل الدخول', 'student': dict(student)})
        else:
            return jsonify({'error': 'كود الطالب غير صحيح'}), 401

    except Exception as e:
        return jsonify({'error': f'خطأ: {e}'}), 500


@app.route('/add_student', methods=['POST'])
def add_student():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        data = request.json
        query = """
            INSERT INTO students 
            (full_name, stage, age, email, phone, guardian_name, guardian_phone, student_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
        db.close()

        return jsonify({'message': 'تمت إضافة الطالب بنجاح'}), 201

    except Exception as e:
        return jsonify({'error': f'خطأ: {e}'}), 500


@app.route('/students', methods=['GET'])
def get_students():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()

        db.close()
        return jsonify([dict(row) for row in students])

    except Exception as e:
        return jsonify({'error': f'خطأ: {e}'}), 500


@app.route('/edit_student/<int:student_id>', methods=['PUT'])
def edit_student(student_id):
    try:
        db = get_db_connection()
        cursor = db.cursor()

        data = request.json
        query = """
            UPDATE students
            SET full_name = ?,
                stage = ?,
                age = ?,
                email = ?,
                phone = ?,
                guardian_name = ?,
                guardian_phone = ?,
                student_code = ?
            WHERE id = ?
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
            db.close()
            return jsonify({'error': 'لا يوجد طالب بهذا الكود'}), 404       

        db.close()
        return jsonify({'message': 'تم تعديل بيانات الطالب بنجاح'})

    except Exception as e:
        return jsonify({'error': f'خطأ: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
