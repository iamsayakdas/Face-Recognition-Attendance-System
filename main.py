import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

import db
from face_utils import capture_faces_for_roll, train_encodings, ensure_dataset_dir
from attendance_cam import start_attendance_camera

root = None

def add_student_window(parent):
    win = tk.Toplevel(parent)
    win.title("Add Student")
    win.geometry("350x260")

    tk.Label(win, text="Roll:").pack(pady=5)
    entry_roll = tk.Entry(win)
    entry_roll.pack(pady=5)

    tk.Label(win, text="Name:").pack(pady=5)
    entry_name = tk.Entry(win)
    entry_name.pack(pady=5)

    tk.Label(win, text="Phone:").pack(pady=5)
    entry_phone = tk.Entry(win)
    entry_phone.pack(pady=5)

    tk.Label(win, text="Email:").pack(pady=5)
    entry_email = tk.Entry(win)
    entry_email.pack(pady=5)

    def save_student():
        roll = entry_roll.get().strip()
        name = entry_name.get().strip()
        phone = entry_phone.get().strip()
        email = entry_email.get().strip()

        if not roll or not name:
            messagebox.showerror("Error", "Roll and Name are required")
            return

        db.add_student(roll, name, phone, email)
        ensure_dataset_dir()
        os.makedirs(os.path.join("dataset", roll), exist_ok=True)
        messagebox.showinfo("Success", f"Student {name} added with roll {roll}")
        win.destroy()

    tk.Button(win, text="Save", command=save_student).pack(pady=15)

def capture_faces_ui():
    def start_capture():
        roll = entry_roll.get().strip()

        if not roll:
            messagebox.showerror("Error", "Enter roll number")
            return

        student = db.get_student_by_roll(roll)
        if not student:
            messagebox.showerror("Error", "No such student. Add student first.")
            return

        win.destroy()
        capture_faces_for_roll(roll)

    win = tk.Toplevel(root)
    win.title("Capture Faces")
    win.geometry("300x150")

    tk.Label(win, text="Enter Roll to capture faces:").pack(pady=10)
    entry_roll = tk.Entry(win)
    entry_roll.pack(pady=5)

    tk.Button(win, text="Start Capture", command=start_capture).pack(pady=15)

def train_model():
    try:
        train_encodings()
        messagebox.showinfo("Success", "Training complete.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def start_attendance():
    start_attendance_camera()

def export_to_excel():
    rows = db.get_attendance_joined()

    if not rows:
        messagebox.showinfo("Info", "No attendance data to export.")
        return

    df = pd.DataFrame(rows, columns=[
        "Date", "Time", "Roll", "Name", "Phone", "Email", "Status"
    ])

    df.to_excel("attendance_export.xlsx", index=False)
    messagebox.showinfo("Exported", "Exported to attendance_export.xlsx")

def show_students():
    rows = db.get_all_students()
    win = tk.Toplevel(root)
    win.title("Students")
    win.geometry("600x320")

    cols = ("ID", "Roll", "Name", "Phone", "Email")
    tree = ttk.Treeview(win, columns=cols, show="headings")

    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=110)

    for r in rows:
        tree.insert("", tk.END, values=r)

    tree.pack(fill=tk.BOTH, expand=True)

def main_ui():
    global root
    db.init_db()
    ensure_dataset_dir()

    root = tk.Tk()
    root.title("Face Recognition Attendance System")
    root.geometry("650x420")

    tk.Label(root,
             text="Face Recognition Attendance System",
             font=("Helvetica", 16, "bold")).pack(pady=20)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Add Student", width=24,
              command=lambda: add_student_window(root)).grid(row=0, column=0, padx=10, pady=10)

    tk.Button(btn_frame, text="Show Students", width=24,
              command=show_students).grid(row=0, column=1, padx=10, pady=10)

    tk.Button(btn_frame, text="Capture Faces", width=24,
              command=capture_faces_ui).grid(row=1, column=0, padx=10, pady=10)

    tk.Button(btn_frame, text="Train Model", width=24,
              command=train_model).grid(row=1, column=1, padx=10, pady=10)

    tk.Button(btn_frame, text="Start Attendance", width=24,
              command=start_attendance).grid(row=2, column=0, padx=10, pady=10)

    tk.Button(btn_frame, text="Export to Excel", width=24,
              command=export_to_excel).grid(row=2, column=1, padx=10, pady=10)

    tk.Button(root, text="Exit", command=root.destroy).pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main_ui()
