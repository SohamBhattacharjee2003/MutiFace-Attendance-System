import time
import uuid

class FaceTracker:
    def __init__(self):
        self.active_ids = {}  # face_id → last_seen_time

    def get_face_id(self, name):
        """
        Maintain a temporary ID for each recognized person.
        Prevents multiple attendance entries within a short time.
        """
        now = time.time()

        # Cleanup old entries (> 10 seconds)
        self.active_ids = {
            k: v for k, v in self.active_ids.items()
            if now - v < 10
        }

        if name in self.active_ids:
            self.active_ids[name] = now
            return name  # same student

        # New face detected
        self.active_ids[name] = now
        return name
