import sqlite3

DB = "attendance.db"

def connect():
    return sqlite3.connect(DB)

def init_db():
    con = connect()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll TEXT UNIQUE,
            name TEXT,
            phone TEXT,
            email TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            time TEXT,
            status TEXT
        )
    """)

    con.commit()
    con.close()

def add_student(roll, name, phone, email):
    con = connect()
    con.execute("INSERT OR IGNORE INTO students(roll,name,phone,email) VALUES(?,?,?,?)",
                (roll, name, phone, email))
    con.commit()
    con.close()

def get_student_by_roll(roll):
    con = connect()
    res = con.execute("SELECT * FROM students WHERE roll=?", (roll,)).fetchone()
    con.close()
    return res

def get_all_students():
    con = connect()
    res = con.execute("SELECT * FROM students").fetchall()
    con.close()
    return res

def mark_attendance_by_roll(roll, date, time, status="Present"):
    stu = get_student_by_roll(roll)
    if not stu:
        return False

    student_id = stu[0]

    con = connect()
    con.execute("INSERT INTO attendance(student_id,date,time,status) VALUES(?,?,?,?)",
                (student_id, date, time, status))
    con.commit()
    con.close()
    return True

def get_attendance_joined():
    con = connect()
    rows = con.execute("""
        SELECT a.date,a.time,s.roll,s.name,s.phone,s.email,a.status
        FROM attendance a
        JOIN students s ON a.student_id=s.id
        ORDER BY a.id DESC
    """).fetchall()
    con.close()
    return rows
