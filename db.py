import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB = "attendance.db"


def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row  # allows name-based access
    return conn


def init_db():
    con = connect()
    cur = con.cursor()

    # Students table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll TEXT UNIQUE,
            name TEXT,
            phone TEXT,
            email TEXT
        )
    """)

    # Attendance table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            time TEXT,
            status TEXT
        )
    """)

    # Admins table (for login)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            reset_token TEXT,
            reset_token_expires_at TEXT
        )
    """)

    con.commit()

    # Ensure at least one default admin exists
    if count_admins(con) == 0:
        create_admin("admin", "admin@example.com", "admin123", con)

    con.close()


# ========== Student functions ==========

def add_student(roll, name, phone, email):
    con = connect()
    con.execute(
        "INSERT OR IGNORE INTO students(roll, name, phone, email) VALUES (?, ?, ?, ?)",
        (roll, name, phone, email),
    )
    con.commit()
    con.close()


def get_student_by_roll(roll):
    con = connect()
    row = con.execute("SELECT * FROM students WHERE roll = ?", (roll,)).fetchone()
    con.close()
    return row


def get_all_students():
    con = connect()
    rows = con.execute("SELECT * FROM students ORDER BY roll").fetchall()
    con.close()
    return rows


def mark_attendance_by_roll(roll, date, time, status="Present"):
    stu = get_student_by_roll(roll)
    if not stu:
        return False

    student_id = stu["id"]

    con = connect()
    con.execute(
        "INSERT INTO attendance(student_id, date, time, status) VALUES (?, ?, ?, ?)",
        (student_id, date, time, status),
    )
    con.commit()
    con.close()
    return True


def get_attendance_joined():
    con = connect()
    rows = con.execute("""
        SELECT a.date, a.time, s.roll, s.name, s.phone, s.email, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.id DESC
    """).fetchall()
    con.close()
    return rows


# ========== Admin functions ==========

def count_admins(con=None):
    own = False
    if con is None:
        con = connect()
        own = True
    cur = con.execute("SELECT COUNT(*) AS cnt FROM admins")
    cnt = cur.fetchone()["cnt"]
    if own:
        con.close()
    return cnt


def create_admin(username, email, password, con=None):
    own = False
    if con is None:
        con = connect()
        own = True

    pwd_hash = generate_password_hash(password)
    con.execute(
        "INSERT OR IGNORE INTO admins(username, email, password_hash) VALUES (?, ?, ?)",
        (username, email, pwd_hash),
    )
    con.commit()
    if own:
        con.close()


def get_admin_by_username(username):
    con = connect()
    row = con.execute(
        "SELECT * FROM admins WHERE username = ?", (username,)
    ).fetchone()
    con.close()
    return row


def get_admin_by_id(admin_id):
    con = connect()
    row = con.execute(
        "SELECT * FROM admins WHERE id = ?", (admin_id,)
    ).fetchone()
    con.close()
    return row


def verify_admin_password(admin_row, password):
    if admin_row is None:
        return False
    return check_password_hash(admin_row["password_hash"], password)


def list_admins():
    con = connect()
    rows = con.execute(
        "SELECT id, username, email FROM admins ORDER BY username"
    ).fetchall()
    con.close()
    return rows


def set_admin_password(admin_id, new_password):
    con = connect()
    pwd_hash = generate_password_hash(new_password)
    con.execute(
        "UPDATE admins SET password_hash = ?, reset_token = NULL, reset_token_expires_at = NULL WHERE id = ?",
        (pwd_hash, admin_id),
    )
    con.commit()
    con.close()


def set_admin_reset_token(admin_id, token, expires_at):
    con = connect()
    con.execute(
        "UPDATE admins SET reset_token = ?, reset_token_expires_at = ? WHERE id = ?",
        (token, expires_at, admin_id),
    )
    con.commit()
    con.close()


def get_admin_by_reset_token(token):
    con = connect()
    row = con.execute(
        "SELECT * FROM admins WHERE reset_token = ?", (token,)
    ).fetchone()
    con.close()
    return row
