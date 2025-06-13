from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS
import json
import logging
from datetime import datetime


app = Flask(__name__)
CORS(app, 
     resources={
         r"/*": {
             "origins": ["http://127.0.0.1:5500", "http://localhost:5500"],
             "methods": ["POST", "OPTIONS"],
             "allow_headers": ["Content-Type"]
         }
     },
     supports_credentials=False,  # Set to True only if you need cookies/auth
     expose_headers=None,
     max_age=None
)


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="abdo.123",
        database="courses_db"
    )

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or 'student_code' not in data:
            return jsonify({'error': 'كود الطالب مطلوب'}), 400

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM students WHERE student_code = %s", (data['student_code'],))
        student = cursor.fetchone()
        
        if not student:
            return jsonify({'error': 'كود الطالب غير صحيح'}), 404
            
        return jsonify({
            'message': 'تم تسجيل الدخول بنجاح',
            'student': student
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()

# ============== تهيئة قاعدة البيانات ==============
# ============== Helper Functions ==============
def _build_cors_preflight_response():
    response = jsonify({'message': 'Preflight Request Accepted'})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

# ============== تهيئة قاعدة البيانات ==============
@app.route('/init_db', methods=['POST', 'OPTIONS'])
def init_db():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # إنشاء جدول الطلاب
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_code VARCHAR(50) NOT NULL UNIQUE,
            full_name VARCHAR(255) NOT NULL,
            stage VARCHAR(50) NOT NULL,
            grade VARCHAR(50) NOT NULL,
            age INT NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(50) NOT NULL,
            guardian_name VARCHAR(255) NOT NULL,
            guardian_phone VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # إنشاء جدول أجزاء الكورس
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_parts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL
        )
        """)
        
        # إدراج أجزاء الكورس الأساسية
        cursor.execute("""
        INSERT IGNORE INTO course_parts (id, name) VALUES 
        (1, 'الشهر الأول'), (2, 'الشهر الثاني'), (3, 'الشهر الثالث')
        """)
        
        # إنشاء جدول الكورسات
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_name VARCHAR(255) NOT NULL,
            youtube_url VARCHAR(255) NOT NULL,
            description TEXT,
            stage VARCHAR(50) NOT NULL,
            grade VARCHAR(50),
            part_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (part_id) REFERENCES course_parts(id)
        )
        """)
        
        # إنشاء جدول الامتحانات
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INT AUTO_INCREMENT PRIMARY KEY,
            exam_name VARCHAR(255) NOT NULL,
            part_id INT NOT NULL,
            stage VARCHAR(50) NOT NULL,
            grade VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (part_id) REFERENCES course_parts(id)
        )
        """)
        
        # إنشاء جدول أسئلة الامتحانات
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            exam_id INT NOT NULL,
            question_text TEXT NOT NULL,
            options JSON NOT NULL,
            correct_answer INT NOT NULL,
            FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
        )
        ALTER TABLE exams ADD COLUMN duration_minutes INT NOT NULL DEFAULT 30;
        """)
        
        db.commit()
        response = jsonify({'message': 'تم تهيئة قاعدة البيانات بنجاح'})
        return _corsify_actual_response(response)
    except Exception as e:
        logger.error(f"خطأ في تهيئة قاعدة البيانات: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

# ============== طلاب ==============
@app.route('/students', methods=['GET'])
def get_students():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
        return jsonify(students)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/add_student', methods=['POST'])
def add_student():
    try:
        data = request.json
        required_fields = ['student_code', 'full_name', 'stage', 'grade', 'age', 
                         'email', 'phone', 'guardian_name', 'guardian_phone']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'حقل {field} مطلوب'}), 400

        db = get_db_connection()
        cursor = db.cursor()
        
        query = """
        INSERT INTO students 
        (student_code, full_name, stage, grade, age, email, phone, guardian_name, guardian_phone)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data['student_code'],
            data['full_name'],
            data['stage'],
            data['grade'],
            data['age'],
            data['email'],
            data['phone'],
            data['guardian_name'],
            data['guardian_phone']
        )
        
        cursor.execute(query, values)
        db.commit()
        return jsonify({'message': 'تمت إضافة الطالب بنجاح'}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': f'خطأ في قاعدة البيانات: {err}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/edit_student/<int:student_id>', methods=['PUT'])
def edit_student(student_id):
    try:
        data = request.json
        required_fields = ['full_name', 'stage', 'grade', 'age', 'email', 
                         'phone', 'guardian_name', 'guardian_phone']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'حقل {field} مطلوب'}), 400

        db = get_db_connection()
        cursor = db.cursor()
        
        query = """
        UPDATE students
        SET full_name = %s,
            stage = %s,
            grade = %s,
            age = %s,
            email = %s,
            phone = %s,
            guardian_name = %s,
            guardian_phone = %s
        WHERE id = %s
        """
        values = (
            data['full_name'],
            data['stage'],
            data['grade'],
            data['age'],
            data['email'],
            data['phone'],
            data['guardian_name'],
            data['guardian_phone'],
            student_id
        )
        
        cursor.execute(query, values)
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'لا يوجد طالب بهذا الرقم'}), 404
            
        return jsonify({'message': 'تم تعديل بيانات الطالب بنجاح'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/delete_student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'لا يوجد طالب بهذا الرقم'}), 404
            
        return jsonify({'message': 'تم حذف الطالب بنجاح'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()

# ============== كورسات ==============
@app.route('/course_parts', methods=['GET'])
def get_course_parts():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM course_parts")
        parts = cursor.fetchall()
        return jsonify(parts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/student_courses/<student_code>', methods=['GET'])
def get_student_courses(student_code):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # جلب بيانات الطالب
        cursor.execute(
            "SELECT * FROM students WHERE student_code = %s",
            (student_code,)
        )
        student = cursor.fetchone()

        if not student:
            return jsonify({
                'success': False,
                'error': 'كود الطالب غير صحيح'
            }), 404

        # جلب الكورسات المناسبة للطالب
        query = """
        SELECT c.*, p.name as part_name 
        FROM courses c
        JOIN course_parts p ON c.part_id = p.id
        WHERE (c.stage = %s OR c.stage = 'عام')
        AND (c.grade IS NULL OR c.grade = %s)
        ORDER BY c.part_id, c.id
        """
        cursor.execute(query, (student['stage'], student['grade']))
        courses = cursor.fetchall()

        # تنظيم الكورسات حسب الأشهر
        organized_courses = {}
        for course in courses:
            part_name = course['part_name']
            if part_name not in organized_courses:
                organized_courses[part_name] = []
            organized_courses[part_name].append(course)

        cursor.close()
        db.close()

        return jsonify({
            'success': True,
            'student': student,
            'courses_by_part': organized_courses
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/courses', methods=['GET'])
def get_courses():
    try:
        stage = request.args.get('stage')
        grade = request.args.get('grade')
        part_id = request.args.get('part_id')
        
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
        SELECT c.*, p.name as part_name 
        FROM courses c
        JOIN course_parts p ON c.part_id = p.id
        WHERE 1=1
        """
        params = []
        
        if stage and stage != 'all':
            query += " AND (c.stage = %s OR c.stage = 'عام')"
            params.append(stage)
            
        if grade and grade != 'all':
            query += " AND (c.grade = %s OR c.grade IS NULL)"
            params.append(grade)
            
        if part_id and part_id != 'all':
            query += " AND c.part_id = %s"
            params.append(part_id)
        
        cursor.execute(query, params)
        courses = cursor.fetchall()
        return jsonify(courses)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/add_course', methods=['POST'])
def add_course():
    try:
        data = request.json
        required_fields = ['course_name', 'youtube_url', 'stage', 'part_id']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'حقل {field} مطلوب'}), 400

        db = get_db_connection()
        cursor = db.cursor()
        
        grades = data.get('grades', [])
        if data['stage'] != 'عام' and not grades:
            return jsonify({'error': 'يجب تحديد صف واحد على الأقل'}), 400
        
        if data['stage'] == 'عام':
            query = """
            INSERT INTO courses 
            (course_name, youtube_url, description, stage, grade, part_id)
            VALUES (%s, %s, %s, %s, NULL, %s)
            """
            values = (
                data['course_name'],
                data['youtube_url'],
                data.get('description', ''),
                data['stage'],
                data['part_id']
            )
            cursor.execute(query, values)
        else:
            for grade in grades:
                query = """
                INSERT INTO courses 
                (course_name, youtube_url, description, stage, grade, part_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                values = (
                    data['course_name'],
                    data['youtube_url'],
                    data.get('description', ''),
                    data['stage'],
                    grade,
                    data['part_id']
                )
                cursor.execute(query, values)
        
        db.commit()
        return jsonify({'message': 'تمت إضافة الكورس بنجاح'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/get_courses_by_student', methods=['POST'])
def get_courses_by_student():
    try:
        data = request.json
        stage = data.get('stage')
        grade = data.get('grade')  # ممكن يبقى None لو المرحلة "عام"

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # الاستعلام حسب المرحلة والصف
        if stage == 'عام':
            query = """
                SELECT * FROM courses
                WHERE stage = %s
            """
            cursor.execute(query, (stage,))
        else:
            query = """
                SELECT * FROM courses
                WHERE stage = %s AND grade = %s
            """
            cursor.execute(query, (stage, grade))

        courses = cursor.fetchall()

        # نجمع الكورسات حسب الشهر
        courses_by_month = {}
        for course in courses:
            if course['release_date']:  # تأكد انه في تاريخ
                month = course['release_date'].strftime('%B')  # اسم الشهر بالإنجليزي
            else:
                month = 'غير معروف'

            if month not in courses_by_month:
                courses_by_month[month] = []

            courses_by_month[month].append({
                'id': course['id'],
                'course_name': course['course_name'],
                'youtube_url': course['youtube_url'],
                'description': course['description'],
                'stage': course['stage'],
                'grade': course['grade'],
                'part_id': course['part_id']
            })

        return jsonify(courses_by_month), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/delete_course/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'لا يوجد كورس بهذا الرقم'}), 404
            
        return jsonify({'message': 'تم حذف الكورس بنجاح'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()

# ============== امتحانات ==============
@app.route('/check_exam_exists', methods=['POST'])
def check_exam_exists():
    try:
        data = request.json
        part_id = data.get('part_id')
        stage = data.get('stage')
        grade = data.get('grade') if data.get('grade') else None

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        query = """
        SELECT id FROM exams 
        WHERE part_id = %s AND stage = %s 
        AND (grade = %s OR (grade IS NULL AND %s IS NULL))
        """
        cursor.execute(query, (part_id, stage, grade, grade))
        
        exam = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'exists': exam is not None,
            'exam_id': exam['id'] if exam else None
        })
        
    except mysql.connector.Error as err:
        return jsonify({
            'success': False,
            'error': f'خطأ في قاعدة البيانات: {err}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        cursor.close()
        db.close()
@app.route('/exams', methods=['GET'])
def get_exams():
    try:
        search = request.args.get('search', '')
        stage = request.args.get('stage', 'all')
        grade = request.args.get('grade', 'all')
        part_id = request.args.get('part_id', 'all')

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # بناء الاستعلام الديناميكي
        query = """
        SELECT e.*, p.name as part_name 
        FROM exams e
        JOIN course_parts p ON e.part_id = p.id
        WHERE 1=1
        """
        params = []

        if search:
            query += " AND e.exam_name LIKE %s"
            params.append(f"%{search}%")
        
        if stage != 'all':
            query += " AND e.stage = %s"
            params.append(stage)
        
        if grade != 'all':
            query += " AND (e.grade = %s OR (e.grade IS NULL AND %s = 'all'))"
            params.append(grade)
            params.append(grade)
        
        if part_id != 'all':
            query += " AND e.part_id = %s"
            params.append(part_id)
        
        query += " ORDER BY e.created_at DESC"
        
        cursor.execute(query, params)
        exams = cursor.fetchall()
        
        # جلب الأسئلة لكل امتحان
        for exam in exams:
            cursor.execute("""
            SELECT id, question_text, options, correct_answer 
            FROM exam_questions 
            WHERE exam_id = %s
            ORDER BY id
            """, (exam['id'],))
            
            questions = cursor.fetchall()
            
            for question in questions:
                try:
                    if isinstance(question['options'], str):
                        question['options'] = json.loads(question['options'])
                    elif isinstance(question['options'], bytes):
                        question['options'] = json.loads(question['options'].decode('utf-8'))
                except (json.JSONDecodeError, AttributeError) as e:
                    question['options'] = ["خطأ في تحميل الخيارات"]
            
            exam['questions'] = questions
        
        return jsonify({
            'success': True,
            'exams': exams
        })
        
    except mysql.connector.Error as err:
        return jsonify({
            'success': False,
            'error': f'خطأ في قاعدة البيانات: {err}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

@app.route('/exam/<int:exam_id>', methods=['GET'])
def get_exam(exam_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # جلب بيانات الامتحان الأساسية
        cursor.execute("""
        SELECT e.*, p.name as part_name 
        FROM exams e
        JOIN course_parts p ON e.part_id = p.id
        WHERE e.id = %s
        """, (exam_id,))
        
        exam = cursor.fetchone()
        
        if not exam:
            return jsonify({
                'success': False,
                'error': 'الامتحان غير موجود'
            }), 404
        
        # جلب أسئلة الامتحان
        cursor.execute("""
        SELECT id, question_text, options, correct_answer 
        FROM exam_questions 
        WHERE exam_id = %s
        ORDER BY id
        """, (exam_id,))
        
        questions = cursor.fetchall()
        
        # تحويل options من JSON string إلى Python list
        for question in questions:
            try:
                if isinstance(question['options'], str):
                    question['options'] = json.loads(question['options'])
                elif isinstance(question['options'], bytes):
                    question['options'] = json.loads(question['options'].decode('utf-8'))
            except (json.JSONDecodeError, AttributeError) as e:
                question['options'] = ["خطأ في تحميل الخيارات"]
                logger.error(f"Error parsing options: {e}")
        
        exam['questions'] = questions
        
        return jsonify({
            'success': True,
            'exam': exam
        })
    except mysql.connector.Error as err:
        return jsonify({
            'success': False,
            'error': f'خطأ في قاعدة البيانات: {err}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/add_exam', methods=['POST', 'OPTIONS'])
def add_exam():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'preflight ok'}), 200
    
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        logger.debug(f"Received exam data: {data}")

        # Validate required fields
        required_fields = ['exam_name', 'part_id', 'stage', 'questions']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Validate questions
        if not isinstance(data['questions'], list) or not data['questions']:
            return jsonify({'error': 'Questions must be a non-empty list'}), 400

        db = None
        cursor = None
        try:
            db = get_db_connection()
            if db is None:
                return jsonify({'error': 'Database connection failed'}), 500
                
            cursor = db.cursor()

            # Insert exam
            add_exam_query = """
            INSERT INTO exams 
            (exam_name, part_id, stage, grade, duration_minutes)
            VALUES (%s, %s, %s, %s, %s)
            """
            exam_values = (
                data['exam_name'],
                data['part_id'],
                data['stage'],
                data.get('grade') if data['stage'] != 'عام' else None,
                data.get('duration_minutes', 60)  # Default 60 minutes
            )
            cursor.execute(add_exam_query, exam_values)
            exam_id = cursor.lastrowid

            # Insert questions
            add_question_query = """
            INSERT INTO exam_questions 
            (exam_id, question_text, options, correct_answer)
            VALUES (%s, %s, %s, %s)
            """
            for question in data['questions']:
                if not all(k in question for k in ['text', 'options', 'correct']):
                    db.rollback()
                    return jsonify({'error': 'Each question must have text, options, and correct answer'}), 400
                
                if question['correct'] < 0 or question['correct'] >= len(question['options']):
                    db.rollback()
                    return jsonify({'error': 'Correct answer index out of range'}), 400
                
                cursor.execute(add_question_query, (
                    exam_id,
                    question['text'],
                    json.dumps(question['options']),
                    question['correct']
                ))

            db.commit()
            return jsonify({
                'success': True,
                'message': 'Exam added successfully',
                'exam_id': exam_id
            }), 201

        except mysql.connector.Error as db_err:
            db.rollback() if db else None
            logger.error(f"Database error: {db_err}")
            return jsonify({'error': f'Database operation failed: {db_err}'}), 500
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
@app.route('/delete_exam/<int:exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # حذف الأسئلة أولاً بسبب constraint foreign key
        cursor.execute("DELETE FROM exam_questions WHERE exam_id = %s", (exam_id,))
        
        # ثم حذف الامتحان
        cursor.execute("DELETE FROM exams WHERE id = %s", (exam_id,))
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({
                'success': False,
                'error': 'لا يوجد امتحان بهذا الرقم'
            }), 404
            
        return jsonify({
            'success': True,
            'message': 'تم حذف الامتحان بنجاح'
        })
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({
            'success': False,
            'error': f'خطأ في قاعدة البيانات: {err}'
        }), 500
    except Exception as e:
        db.rollback() if 'db' in locals() else None
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        cursor.close() if 'cursor' in locals() else None
        db.close() if 'db' in locals() else None


@app.route('/search_exams', methods=['GET'])
def search_exams():
    try:
        search_query = request.args.get('query', '')
        part_id = request.args.get('part_id', '')
        stage = request.args.get('stage', '')
        grade = request.args.get('grade', '')

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # بناء الاستعلام الديناميكي
        query = """
        SELECT e.*, p.name as part_name 
        FROM exams e
        JOIN course_parts p ON e.part_id = p.id
        WHERE 1=1
        """
        params = []

        if search_query:
            query += " AND e.exam_name LIKE %s"
            params.append(f"%{search_query}%")
        
        if part_id and part_id != 'all':
            query += " AND e.part_id = %s"
            params.append(part_id)
        
        if stage and stage != 'all':
            query += " AND e.stage = %s"
            params.append(stage)
        
        if grade and grade != 'all':
            query += " AND (e.grade = %s OR e.grade IS NULL)"
            params.append(grade)

        query += " ORDER BY e.created_at DESC"

        cursor.execute(query, params)
        exams = cursor.fetchall()

        # جلب الأسئلة لكل امتحان
        for exam in exams:
            cursor.execute("""
            SELECT id, question_text 
            FROM exam_questions 
            WHERE exam_id = %s
            """, (exam['id'],))
            exam['questions'] = cursor.fetchall()

        return jsonify({
            'success': True,
            'exams': exams
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        cursor.close()
        db.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)