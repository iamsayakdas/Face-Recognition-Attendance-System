import cv2
import face_recognition
from datetime import datetime
import db
from face_utils import load_encodings

def start_attendance_camera():
    try:
        encodings, labels = load_encodings()
    except:
        print("Model not trained!")
        return

    cam = cv2.VideoCapture(0)

    while True:
        ret, frame = cam.read()
        small = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        boxes = face_recognition.face_locations(rgb)
        encs = face_recognition.face_encodings(rgb, boxes)

        for (top,right,bottom,left), face_enc in zip(boxes, encs):
            matches = face_recognition.compare_faces(encodings, face_enc, tolerance=0.45)
            dist = face_recognition.face_distance(encodings, face_enc)

            label = "Unknown"
            if len(dist) > 0:
                i = dist.argmin()
                if matches[i]:
                    label = labels[i]

                    now = datetime.now()
                    db.mark_attendance_by_roll(
                        roll=label,
                        date=now.strftime("%Y-%m-%d"),
                        time=now.strftime("%H:%M:%S")
                    )

            top, right, bottom, left = top*4, right*4, bottom*4, left*4
            color = (0,255,0) if label!="Unknown" else (0,0,255)

            cv2.rectangle(frame,(left,top),(right,bottom),color,2)
            cv2.putText(frame,label,(left,top-10),cv2.FONT_HERSHEY_SIMPLEX,0.7,color,2)

        cv2.imshow("Attendance Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
    cv2.destroyAllWindows()
