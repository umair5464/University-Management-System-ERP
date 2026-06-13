from flask import Flask, request, jsonify
from flask_cors import CORS
from db_config import get_db_connection

app = Flask(__name__)
# Upgraded CORS to ensure it accepts traffic from both 127.0.0.1 and localhost seamlessly
CORS(app, resources={r"/*": {"origins": "*"}})

# ---------------------------------------------------------
# ROUTE 1: Fetch Programs
# ---------------------------------------------------------
@app.route('/get_programs', methods=['GET'])
def get_programs():
    conn = get_db_connection()
    if not conn: 
        return jsonify([]), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT Program_ID, Program_Name FROM programs")
        programs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(programs), 200
    except Exception as e:
        return jsonify([]), 500

# ---------------------------------------------------------
# ROUTE 2: Submit Application
# ---------------------------------------------------------
@app.route('/submit_application', methods=['POST'])
def submit_application():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO applicants 
            (First_Name, Last_Name, Email, Phone_no, Address, City, District, 
             Board_Name, Matric_Obtained, Matric_Total, Inter_Obtained, Inter_Total, 
             Applied_Program_ID, Merit_Score, Status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending')
        """
        values = (data.get('firstName'), data.get('lastName'), data.get('email'), data.get('phone'), 
                  data.get('address'), data.get('city'), data.get('district'), data.get('board'), 
                  data.get('matricObt'), data.get('matricTot'), data.get('interObt'), data.get('interTot'), 
                  data.get('programId'), data.get('meritScore'))
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ---------------------------------------------------------
# ROUTE 3: System Login (Your Bulletproof Version)
# ---------------------------------------------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM system_users WHERE Username = %s AND Password_Hash = %s", (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return jsonify({
            "status": "success",
            "role": user['Role'],
            "userId": user['Reference_ID'],
            "user_id": user['Reference_ID'],
            "Reference_ID": user['Reference_ID'],
            "id": user['Reference_ID']
        })
    else:
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401

# ---------------------------------------------------------
# ROUTE 4: Faculty Profile
# ---------------------------------------------------------
@app.route('/get_faculty_profile', methods=['POST'])
def get_faculty_profile():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT f.First_Name, f.Last_Name, f.Email, f.Phone_no, f.Role, d.Department_Name
        FROM faculty f
        INNER JOIN departments d ON f.Department_ID = d.Department_ID
        WHERE f.Faculty_ID = %s
    """
    cursor.execute(sql, (data.get('facultyId'),))
    profile = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "profile": profile})

# ---------------------------------------------------------
# ROUTE 5: Faculty Assigned Courses
# ---------------------------------------------------------
@app.route('/get_faculty_courses', methods=['POST'])
def get_faculty_courses():
    faculty_id = request.json.get('facultyId')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT DISTINCT c.Course_ID, c.Course_Name, c.Course_Code, t.Section_ID
        FROM timetable_slots t
        INNER JOIN courses c ON t.Course_ID = c.Course_ID
        WHERE t.Faculty_ID = %s
    """
    cursor.execute(sql, (faculty_id,))
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "courses": courses})

# ---------------------------------------------------------
# ROUTE 6: Faculty Grading Roster
# ---------------------------------------------------------
@app.route('/get_my_students', methods=['POST'])
def get_my_students():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT e.Roll_no, a.First_Name, a.Last_Name, e.Student_ID,
               sg.Sessional_Marks, sg.Mid_Marks, sg.Final_Marks, sg.Practical_Marks, 
               sg.Total_Obtained, sg.GPA_Points, sg.Grade_Letter
        FROM enrolled_students e
        INNER JOIN applicants a ON e.Applicant_ID = a.Applicant_ID
        LEFT JOIN student_grades sg ON e.Student_ID = sg.Student_ID AND sg.Course_ID = %s
        WHERE e.Program_ID = (SELECT Program_ID FROM courses WHERE Course_ID = %s)
        AND e.Current_Semester = (SELECT Semester_Number FROM courses WHERE Course_ID = %s)
    """
    cursor.execute(sql, (data.get('courseId'), data.get('courseId'), data.get('courseId')))
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"status": "success", "students": students})

# ---------------------------------------------------------
# ROUTE 7: Faculty Batch Grade Submit
# ---------------------------------------------------------
@app.route('/submit_batch_grades', methods=['POST'])
def submit_batch_grades():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    for s in data.get('grades'):
        cursor.execute("SELECT Student_ID FROM enrolled_students WHERE Roll_no = %s", (s['rollNo'],))
        result = cursor.fetchone()
        if result:
            student_id = result[0]
            cursor.execute("""
                INSERT IGNORE INTO student_grades 
                (Student_ID, Course_ID, Sessional_Marks, Mid_Marks, Final_Marks, Practical_Marks, Total_Obtained, Total_Max, GPA_Points, Grade_Letter) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (student_id, s['courseId'], s['sessional'], s['mid'], s['final'], s['practical'], s['totalObtained'], s['totalMax'], s['gpaPoints'], s['gradeLetter']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success"})

# ---------------------------------------------------------
# ROUTE 8: Student Profile (RESTORED WITH FEE_STATUS)
# ---------------------------------------------------------
@app.route('/get_student_profile', methods=['POST'])
def get_student_profile():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT a.First_Name, a.Last_Name, a.Email, a.Phone_no, 
               e.Roll_no, e.Current_Semester, p.Program_Name, e.Fee_Status
        FROM enrolled_students e
        INNER JOIN applicants a ON e.Applicant_ID = a.Applicant_ID
        INNER JOIN programs p ON e.Program_ID = p.Program_ID
        WHERE e.Student_ID = %s
    """
    cursor.execute(sql, (data.get('studentId'),))
    profile = cursor.fetchone()
    cursor.close()
    conn.close()
    if profile:
        return jsonify({"status": "success", "profile": profile})
    return jsonify({"status": "error", "message": "Student profile not found."}), 404

# ---------------------------------------------------------
# ROUTE 9: Student Transcript
# ---------------------------------------------------------
@app.route('/get_student_transcript', methods=['POST'])
def get_student_transcript():
    student_id = request.json.get('studentId')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT c.Course_Name, sg.Grade_Letter, sg.GPA_Points, 
               COALESCE(CONCAT(f.First_Name, ' ', f.Last_Name), 'Pending Assignment') as Professor
        FROM student_grades sg
        INNER JOIN courses c ON sg.Course_ID = c.Course_ID
        LEFT JOIN enrolled_students e ON sg.Student_ID = e.Student_ID
        LEFT JOIN timetable_slots t ON t.Course_ID = c.Course_ID AND t.Section_ID = e.Section_ID
        LEFT JOIN faculty f ON t.Faculty_ID = f.Faculty_ID
        WHERE sg.Student_ID = %s
    """
    cursor.execute(sql, (student_id,))
    grades = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"grades": grades})

# ---------------------------------------------------------
# ROUTE 10: Student Timetable
# ---------------------------------------------------------
@app.route('/get_student_timetable', methods=['POST'])
def get_student_timetable():
    student_id = request.json.get('studentId')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql = """
        SELECT c.Course_Name, f.First_Name as Prof_First, f.Last_Name as Prof_Last, 
               t.Day_Of_Week, 
               TIME_FORMAT(t.Start_Time, '%h:%i %p') as Start_Time, 
               TIME_FORMAT(t.End_Time, '%h:%i %p') as End_Time, 
               t.Room_ID,
               s.Section_Name  -- Added this column
        FROM enrolled_students e
        INNER JOIN timetable_slots t ON e.Section_ID = t.Section_ID
        INNER JOIN sections s ON t.Section_ID = s.Section_ID -- Added JOIN to sections table
        INNER JOIN courses c ON t.Course_ID = c.Course_ID
        INNER JOIN faculty f ON t.Faculty_ID = f.Faculty_ID
        WHERE e.Student_ID = %s
    """
    cursor.execute(sql, (student_id,))
    timetable = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"timetable": timetable})
# ---------------------------------------------------------
# ROUTE 11: Faculty Timetable

@app.route('/get_faculty_timetable', methods=['POST'])
def get_faculty_timetable():
    faculty_id = request.json.get('facultyId')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    sql = """
        SELECT c.Course_Name, c.Course_Code, s.Section_Name, t.Day_Of_Week, 
               TIME_FORMAT(t.Start_Time, '%h:%i %p') as Start_Time, 
               TIME_FORMAT(t.End_Time, '%h:%i %p') as End_Time, 
               t.Room_ID
        FROM timetable_slots t
        INNER JOIN courses c ON t.Course_ID = c.Course_ID
        INNER JOIN sections s ON t.Section_ID = s.Section_ID -- Added JOIN to sections table
        WHERE t.Faculty_ID = %s
        ORDER BY FIELD(t.Day_Of_Week, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'), t.Start_Time
    """
    cursor.execute(sql, (faculty_id,))
    timetable = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({"timetable": timetable})
# ---------------------------------------------------------
# ROUTE 12: Generate Printable Fee Challan
# ---------------------------------------------------------
@app.route('/download_challan/<roll_no>', methods=['GET'])
def download_challan(roll_no):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT a.First_Name, a.Last_Name, e.Roll_no, p.Program_Name, e.Fee_Status
        FROM enrolled_students e
        INNER JOIN applicants a ON e.Applicant_ID = a.Applicant_ID
        INNER JOIN programs p ON e.Program_ID = p.Program_ID
        WHERE e.Roll_no = %s
    """
    cursor.execute(sql, (roll_no,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not student:
        return "Student not found.", 404

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fee Challan - {student['Roll_no']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .challan-container {{ display: flex; justify-content: space-between; gap: 20px; }}
            .slip {{ border: 2px dashed #ccc; padding: 20px; width: 30%; }}
            .header {{ text-align: center; border-bottom: 2px solid black; padding-bottom: 10px; margin-bottom: 15px; }}
            h2, h3 {{ margin: 0; }}
            .details {{ margin-bottom: 20px; line-height: 1.8; font-size: 14px; }}
            .amount {{ text-align: center; font-size: 24px; font-weight: bold; padding: 10px; border: 1px solid black; background: #f9f9f9; }}
            .watermark {{ color: {'red' if student['Fee_Status'] == 'Unpaid' else 'green'}; font-size: 30px; text-align: center; font-weight: bold; text-transform: uppercase; margin-top: 20px; border: 3px solid; padding: 10px; opacity: 0.8; transform: rotate(-15deg);}}
        </style>
    </head>
    <body onload="window.print()"> <div class="challan-container">
            {''.join([f'''
            <div class="slip">
                <div class="header">
                    <h2>MNS-UAM</h2>
                    <h3>{copy_name} Copy</h3>
                    <p style="margin:5px 0 0 0; font-size:12px;">UBL A/C: 1234-567890-1</p>
                </div>
                <div class="details">
                    <strong>Date:</strong> 10-May-2026<br>
                    <strong>Roll No:</strong> {student['Roll_no']}<br>
                    <strong>Name:</strong> {student['First_Name']} {student['Last_Name']}<br>
                    <strong>Program:</strong> {student['Program_Name']}<br>
                    <strong>Semester:</strong> 1st
                </div>
                <div class="amount">Total: Rs. 45,000/-</div>
                <div class="watermark">{student['Fee_Status']}</div>
                <p style="margin-top: 50px; text-align: center; border-top: 1px solid black; padding-top: 5px;">Cashier Signature</p>
            </div>
            ''' for copy_name in ['Bank', 'University', 'Student']])}
        </div>
    </body>
    </html>
    """
    return html_content

if __name__ == '__main__':
    print("🚀 API Server is running on http://localhost:5000")
    # Using 0.0.0.0 forces Flask to listen to all network interfaces, completely bypassing the "localhost" vs "127.0.0.1" disconnect bug!
    app.run(host='0.0.0.0', debug=True, port=5000)