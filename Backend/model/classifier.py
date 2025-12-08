import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
import os


class FaceClassifier:
    def __init__(self, path="./models"):
        os.makedirs(path, exist_ok=True)
        self.model_path = os.path.join(path, 'svm_classifier.joblib')
        self.le_path = os.path.join(path, 'label_encoder.joblib')

    def train(self, embeddings, labels):
        le = LabelEncoder()
        y = le.fit_transform(labels)
        clf = SVC(kernel='linear', probability=True)
        clf.fit(embeddings, y)
        joblib.dump(clf, self.model_path)
        joblib.dump(le, self.le_path)
        return clf, le

    def load(self):
        clf = joblib.load(self.model_path)
        le = joblib.load(self.le_path)
        return clf, le