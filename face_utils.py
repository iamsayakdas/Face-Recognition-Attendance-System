import os
import cv2
import face_recognition
import pickle

DATASET_DIR = "dataset"
ENCODINGS_PATH = "encodings.pickle"

def ensure_dataset_dir():
    os.makedirs(DATASET_DIR, exist_ok=True)

def capture_faces_for_roll(roll, num_images=30):
    ensure_dataset_dir()
    save_dir = os.path.join(DATASET_DIR, roll)
    os.makedirs(save_dir, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam")
        return

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    count = 0
    print("[INFO] Press 'q' to stop capture early.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read frame")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(100, 100)
        )

        # multi-face detection: it will capture for every detected face
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            face_img = frame[y:y+h, x:x+w]
            img_path = os.path.join(save_dir, f"{roll}_{count}.jpg")
            cv2.imwrite(img_path, face_img)
            count += 1
            print(f"[INFO] Saved image {count}/{num_images}")
            if count >= num_images:
                break

        cv2.putText(frame, f"Roll: {roll} | Images: {count}/{num_images}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (255, 255, 255), 2)

        cv2.imshow("Capture Faces - Press q to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if count >= num_images:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Capture finished for roll:", roll)

def train_encodings():
    ensure_dataset_dir()
    known_encodings = []
    known_labels = []

    # iterate over rolls
    for roll_folder in os.listdir(DATASET_DIR):
        roll_dir = os.path.join(DATASET_DIR, roll_folder)
        if not os.path.isdir(roll_dir):
            continue
        label = roll_folder
        print(f"[INFO] Processing roll {label}")

        for img_name in os.listdir(roll_dir):
            img_path = os.path.join(roll_dir, img_name)
            image = cv2.imread(img_path)
            if image is None:
                print(f"[WARNING] Could not read {img_path}")
                continue

            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            boxes = face_recognition.face_locations(rgb, model="hog")
            if len(boxes) == 0:
                print(f"[WARNING] No face found in {img_path}")
                continue

            encodings = face_recognition.face_encodings(rgb, boxes)
            for encoding in encodings:
                known_encodings.append(encoding)
                known_labels.append(label)

    data = {"encodings": known_encodings, "labels": known_labels}
    with open(ENCODINGS_PATH, "wb") as f:
        pickle.dump(data, f)

    print(f"[INFO] Training complete. Saved {len(known_encodings)} encodings.")

def load_encodings():
    if not os.path.exists(ENCODINGS_PATH):
        raise FileNotFoundError(f"{ENCODINGS_PATH} not found. Train model first.")
    with open(ENCODINGS_PATH, "rb") as f:
        data = pickle.load(f)
    return data["encodings"], data["labels"]
