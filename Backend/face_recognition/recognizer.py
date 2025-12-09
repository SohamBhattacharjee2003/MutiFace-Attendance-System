import os
import json
import numpy as np

EMBED_PATH = "embeddings/"
THRESHOLD = 1.05  # tuned for ArcFace

def recognize(embedding):
    best_name = "Unknown"
    best_dist = 999

    for file in os.listdir(EMBED_PATH):
        if not file.endswith(".json"):
            continue

        data = json.load(open(os.path.join(EMBED_PATH, file)))
        name = data["name"]

        for emb in data["embeddings"]:
            ref = np.array(emb)
            dist = np.linalg.norm(embedding - ref)

            if dist < best_dist:
                best_dist = dist
                best_name = name

    if best_dist > THRESHOLD:
        return "Unknown", float(best_dist)

    return best_name, float(best_dist)
