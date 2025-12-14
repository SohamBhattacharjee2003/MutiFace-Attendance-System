import os
import json
import numpy as np

EMBED_PATH = "embeddings/"
THRESHOLD = 1.05  # tuned for ArcFace

def recognize(embedding):
    best_name = "Unknown"
    best_dist = 999

    if not os.path.exists(EMBED_PATH):
        return "Unknown", float(best_dist)

    for file in os.listdir(EMBED_PATH):
        if not file.endswith(".json"):
            continue

        try:
            file_path = os.path.join(EMBED_PATH, file)
            with open(file_path, "r") as f:
                data = json.load(f)
            
            name = data.get("name", "Unknown")
            embeddings = data.get("embeddings", [])

            for emb in embeddings:
                ref = np.array(emb)
                dist = np.linalg.norm(embedding - ref)

                if dist < best_dist:
                    best_dist = dist
                    best_name = name
        except Exception as e:
            print(f"⚠️ Error loading {file}: {e}")
            continue

    if best_dist > THRESHOLD:
        return "Unknown", float(best_dist)

    return best_name, float(best_dist)
