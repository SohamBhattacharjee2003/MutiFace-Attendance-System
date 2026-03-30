# Automatic Attendance System using Face Recognition

This project is a multi-camera face recognition attendance system built entirely in Python using standard libraries (no custom C++ compilation needed beyond standard `dlib` installation).

## Approach & Architecture

The system uses a classic computer vision pipeline combined with machine learning classification:

1.  **Face Detection:** 
    *   **MTCNN (Multi-task Cascaded Convolutional Networks)** is used for preprocessing the large VGGFace2 dataset. It is highly accurate at finding faces in varying poses.
    *   **Haar Cascades** are used for live webcam ingestion (`collect_student.py`) because they are extremely fast and lightweight for real-time capture.
2.  **Feature Extraction (Embeddings):** 
    *   The `face_recognition` library (which wraps `dlib`'s state-of-the-art ResNet deep learning model) is used to map each cropped face into a **128-dimensional embedding vector**. This vector uniquely represents the facial features.
3.  **Classification:** 
    *   A **Support Vector Machine (SVM)** with an RBF kernel from `scikit-learn` is trained on these embeddings. SVMs are highly effective for high-dimensional spaces like our 128-d vectors.
4.  **Live Multithreading (macOS optimized):** 
    *   The real-time attendance script (`attendance.py`) uses **multithreading**. Background threads handle camera capture, face extraction, and SVM prediction. 
    *   The Main Thread handles the `cv2.imshow` UI, which is a strict requirement for macOS GUI applications.

## Directory Structure

```text
Server/
├── dataset/                   ← Raw images (downloaded via dataset.py)
├── processed_dataset/         ← Cropped 160x160 faces (from preprocess.py & collect_student.py)
├── encodings/                 ← Stores encodings.pkl (128-d vectors)
├── models/                    ← Stores the trained SVM classifier and label encoder
├── logs/                      ← Daily attendance CSV records
├── scripts/
│   ├── dataset.py             ← Step 1: Downloads VGGFace2 dataset via Kagglehub.
│   ├── preprocess.py          ← Step 2: Crops faces from the dataset using MTCNN.
│   ├── collect_student.py     ← Step 2.5: Live webcam tool to add your own face to the dataset.
│   ├── generate_encodings.py  ← Step 3: Converts cropped faces into 128-d encodings.
│   ├── train_classifier.py    ← Step 4: Trains the SVM model on the encodings.
│   └── attendance.py          ← Step 5: Live multi-camera attendance logging.
├── venv/                      ← Python virtual environment
└── requirements.txt           ← Dependencies
```

## How to setup and run your own face

Because the model was initially tested on the VGGFace2 dataset (which contains celebrities), pointing the camera at yourself resulted in low accuracy or wrong guesses. The model had never seen your face!

To fix this and use the system properly, follow these steps to add yourself:

### 1. Collect your face data
Run the collection script. Press `A` to start auto-capturing or `SPACE` to capture manually. Move your head around slightly to get different angles.
```bash
python scripts/collect_student.py --name "Soham" --count 80
```
*(This saves 80 images of your face directly into `processed_dataset/Soham`)*

### 2. Generate Encodings
Now that your face is in the dataset, recreate the embeddings so the system learns your features.
```bash
python scripts/generate_encodings.py
```

### 3. Train the Classifier
Train the SVM model on the newly generated encodings.
```bash
python scripts/train_classifier.py --classifier svm
```

### 4. Run Live Attendance
Start the live attendance tracker. It should now recognize you and log your attendance.
```bash
python scripts/attendance.py --cameras 0
```
