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

    # Add per-person progress info
    image_files = [f for f in os.listdir(person_path) if not f.startswith('.') and f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]
    for img_name in tqdm(image_files, desc=f"Processing {person_folder}", leave=False):
        img_path = os.path.join(person_path, img_name)
        img = cv2.imread(img_path)

        if img is None:
            continue

        # Add minimum image size guard
        # Skip if image is too small (e.g., less than 50x50 pixels)
        if img.shape[0] < 50 or img.shape[1] < 50:
            continue

        # ── MTCNN 1.0.0 + TF2 bug: crashes with ValueError on empty batches ──
        # When PNet/RNet find no candidates, ONet receives shape (0,48,48,3)
        # and Conv2D raises ValueError instead of returning []
        try:
            results = detector.detect_faces(img)
        except (ValueError, Exception):
            continue

        if not results:
            continue

        # Get image dimensions for clipping
        img_h, img_w = img.shape[:2]

        x, y, w, h = results[0]['box']

        # Fix negative bounding box coordinates and clip to image boundaries
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(img_w, x + w)
        y2 = min(img_h, y + h)

        # Ensure valid dimensions after clipping
        if x2 <= x1 or y2 <= y1:
            continue

        face = img[y1:y2, x1:x2]

        try:
            face = cv2.resize(face, (160, 160))
            cv2.imwrite(os.path.join(save_path, img_name), face)
        except Exception as e: # Catch more specific exceptions if needed
            # print(f"Error resizing or writing image {img_name}: {e}")
            continue

for person in tqdm(os.listdir(INPUT_DIR), desc="Overall Progress"):
    # Skip hidden files or non-directory entries in the INPUT_DIR
    if person.startswith('.') or not os.path.isdir(os.path.join(INPUT_DIR, person)):
        continue
    process_person(person)