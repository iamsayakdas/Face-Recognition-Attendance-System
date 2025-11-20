import cv2
import face_recognition
from datetime import datetime

from face_utils import load_encodings
import db

def start_attendance_camera():
    try:
        known_encodings, known_labels = load_encodings()
    except FileNotFoundError as e:
        print("[ERROR]", e)
        return

    print(f"[INFO] Loaded {len(known_encodings)} encodings.")
    db.init_db()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    process_every_other = True

    print("[INFO] Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to grab frame")
            break

        # Resize for speed
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = []
        face_labels = []

        if process_every_other:
            face_locations = face_recognition.face_locations(rgb_small)
            face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(
                    known_encodings, face_encoding, tolerance=0.45
                )
                face_distances = face_recognition.face_distance(
                    known_encodings, face_encoding
                )

                if len(face_distances) > 0:
                    best_match_index = face_distances.argmin()
                    label = "Unknown"
                    if matches[best_match_index]:
                        label = known_labels[best_match_index]
                        # mark attendance in DB
                        now = datetime.now()
                        date_str = now.strftime("%Y-%m-%d")
                        time_str = now.strftime("%H:%M:%S")
                        new_mark = db.mark_attendance_by_roll(label, date_str, time_str)
                        if new_mark:
                            print(f"[ATTENDANCE] Marked Present: Roll {label} at {time_str}")
                    else:
                        # Unknown face alert
                        print("[ALERT] Unknown face detected!")
                    face_labels.append(label)
                else:
                    face_labels.append("Unknown")

        process_every_other = not process_every_other

        # Draw rectangles for each detected face (multi-face)
        for (top, right, bottom, left), label in zip(face_locations, face_labels):
            # scale back
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            if label == "Unknown":
                color = (0, 0, 255)  # red box for unknown
                text = "Unknown"
            else:
                color = (0, 255, 0)
                text = f"Roll: {label}"

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, text, (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        cv2.imshow("Face Recognition Attendance", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
