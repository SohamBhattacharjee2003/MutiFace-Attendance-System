import os
import cv2
from mtcnn import MTCNN
from tqdm import tqdm

detector = MTCNN()

INPUT_DIR = "/Users/sohambhattacharjee/.cache/kagglehub/datasets/hearfool/vggface2/versions/1/train"
OUTPUT_DIR = "./processed_dataset"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_person(person_folder):
    person_path = os.path.join(INPUT_DIR, person_folder)
    save_path = os.path.join(OUTPUT_DIR, person_folder)

    os.makedirs(save_path, exist_ok=True)

    for img_name in os.listdir(person_path):
        img_path = os.path.join(person_path, img_name)
        img = cv2.imread(img_path)

        if img is None:
            continue

        results = detector.detect_faces(img)

        if len(results) == 0:
            continue

        x, y, w, h = results[0]['box']
        face = img[y:y+h, x:x+w]

        try:
            face = cv2.resize(face, (160, 160))
            cv2.imwrite(os.path.join(save_path, img_name), face)
        except:
            continue

for person in tqdm(os.listdir(INPUT_DIR)):
    process_person(person)