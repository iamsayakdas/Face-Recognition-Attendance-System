import os
import cv2
import face_recognition
import pickle

DATASET = "dataset"
ENC = "encodings.pickle"

def ensure_dataset_dir():
    os.makedirs(DATASET, exist_ok=True)

def capture_faces_for_roll(roll, num=30):
    ensure_dataset_dir()
    path = os.path.join(DATASET, roll)
    os.makedirs(path, exist_ok=True)

    cam = cv2.VideoCapture(0)
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    count = 0
    while True:
        ret, frame = cam.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = cascade.detectMultiScale(gray, 1.1, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
            crop = frame[y:y+h, x:x+w]
            cv2.imwrite(f"{path}/{roll}_{count}.jpg", crop)
            count += 1

        cv2.imshow("Capture Faces", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        if count >= num:
            break

    cam.release()
    cv2.destroyAllWindows()

def train_encodings():
    ensure_dataset_dir()
    known_enc = []
    known_labels = []

    for roll in os.listdir(DATASET):
        folder = os.path.join(DATASET, roll)
        if not os.path.isdir(folder):
            continue

        for img in os.listdir(folder):
            img_path = os.path.join(folder, img)
            image = cv2.imread(img_path)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            boxes = face_recognition.face_locations(rgb)
            enc = face_recognition.face_encodings(rgb, boxes)
            for e in enc:
                known_enc.append(e)
                known_labels.append(roll)

    with open(ENC, "wb") as f:
        pickle.dump({"encodings": known_enc, "labels": known_labels}, f)

def load_encodings():
    with open(ENC, "rb") as f:
        data = pickle.load(f)
    return data["encodings"], data["labels"]
