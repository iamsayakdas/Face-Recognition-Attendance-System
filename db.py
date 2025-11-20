import sqlite3
import os

DB_PATH = "attendance.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Create students table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT
        )
    """)

    # Create attendance table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    conn.commit()
    conn.close()

def add_student(roll, name, phone="", email=""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO students (roll, name, phone, email)
        VALUES (?, ?, ?, ?)
    """, (roll, name, phone, email))
    conn.commit()
    conn.close()

def get_student_by_roll(roll):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, roll, name, phone, email FROM students WHERE roll = ?", (roll,))
    row = cur.fetchone()
    conn.close()
    return row

def get_all_students():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, roll, name, phone, email FROM students ORDER BY roll")
    rows = cur.fetchall()
    conn.close()
    return rows

def mark_attendance_by_roll(roll, date_str, time_str, status="Present"):
    student = get_student_by_roll(roll)
    if not student:
        return False  # unknown student

    student_id = student[0]

    conn = get_connection()
    cur = conn.cursor()

    # check duplicate for same date
    cur.execute("""
        SELECT id FROM attendance
        WHERE student_id = ? AND date = ?
    """, (student_id, date_str))
    existing = cur.fetchone()
    if existing:
        conn.close()
        return False

    cur.execute("""
        INSERT INTO attendance (student_id, date, time, status)
        VALUES (?, ?, ?, ?)
    """, (student_id, date_str, time_str, status))

    conn.commit()
    conn.close()
    return True

def get_attendance_joined():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.date, a.time, s.roll, s.name, s.phone, s.email, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC, a.time DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows
