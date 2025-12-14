# Face Attendance System - Backend

A Flask-based REST API for face recognition and attendance tracking using deep learning.

## Features

- 👤 Student registration with face embeddings
- 🎯 Real-time face detection and recognition
- 📊 Attendance tracking with MongoDB
- 🔄 Update student profiles with additional images
- 📅 Date-based attendance queries
- 🗑️ Student and attendance management

## Tech Stack

- **Flask**: Web framework
- **InsightFace**: Face recognition (ArcFace model)
- **MTCNN**: Face detection
- **MongoDB**: Database
- **PyTorch**: Deep learning framework

## Prerequisites

- Python 3.8 or higher
- MongoDB (local or Atlas)
- 4GB+ RAM (for face recognition models)

## Installation

### 1. Clone the repository

```bash
cd Backend
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the Backend directory:

```env
MONGO_URI=mongodb://127.0.0.1:27017
# Or for MongoDB Atlas:
# MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority

FLASK_SECRET_KEY=your-secret-key-here
```

### 5. Verify setup

Run the setup check script:

```bash
python check_setup.py
```

## Running the Application

### Development Mode

```bash
python app.py
```

The server will start on `http://localhost:5000`

### Production Mode

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app
```

## API Endpoints

### Health Check

```http
GET /health
```

Returns server status.

### Register Student

```http
POST /register
Content-Type: application/json

{
  "name": "John Doe",
  "images": ["data:image/jpeg;base64,...", ...]
}
```

Registers a new student with at least 5 face images.

### Predict/Recognize Faces

```http
POST /predict
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,..."
}
```

Detects and recognizes faces in the image. Automatically marks attendance for known faces.

### Get Attendance Records

```http
GET /attendance
```

Returns all attendance records.

### Get Attendance by Date

```http
GET /attendance/date/2024-12-14
```

Returns attendance records for a specific date (YYYY-MM-DD format).

### Clear Attendance

```http
DELETE /attendance/clear
```

Clears all attendance records.

### Get Students List

```http
GET /students
```

Returns list of registered students with their sample counts.

### Update Student

```http
POST /update-student
Content-Type: application/json

{
  "name": "John Doe",
  "images": ["data:image/jpeg;base64,...", ...]
}
```

Adds more images to an existing student's profile.

### Delete Student

```http
DELETE /students/<name>
```

Deletes a student and their attendance records.

### Get Valid Student Names

```http
GET /students/valid-names
```

Returns names of students who have embedding files.

### Delete Students Missing Embeddings

```http
POST /students/delete-missing
```

Removes students from database if their embedding files are missing.

## Project Structure

```
Backend/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── check_setup.py             # Setup verification script
├── .env                       # Environment variables
├── embeddings/                # Student face embeddings (JSON files)
├── face_recognition/          # Face recognition modules
│   ├── detector.py           # Face detection (MTCNN)
│   ├── embedder.py           # Face embedding (InsightFace)
│   ├── recognizer.py         # Face recognition logic
│   └── tracker.py            # Face tracking
└── routes/
    ├── register.py           # Registration endpoints
    └── attendance.py         # Attendance endpoints
```

## Face Recognition Pipeline

1. **Detection**: MTCNN detects faces in images
2. **Embedding**: InsightFace (ArcFace) generates 512-dimensional embeddings
3. **Recognition**: Compares embeddings using L2 distance
4. **Threshold**: Distance < 1.05 for positive match

## Troubleshooting

### Import Errors

```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### MongoDB Connection Issues

- Check if MongoDB is running: `mongod --version`
- Verify MONGO_URI in `.env`
- For Atlas: Check IP whitelist and credentials

### Face Detection Issues

- Ensure good lighting in images
- Face should be clearly visible
- Minimum 5 images required for registration
- Images should be front-facing

### Model Loading Errors

- First run downloads InsightFace models (~100MB)
- Check internet connection
- Models are cached in `~/.insightface/`

### Memory Issues

- Reduce image size before sending
- Use CPU execution provider (default)
- Close other applications

## Performance Tips

1. **Image Size**: Resize images to 640x480 before processing
2. **Batch Processing**: Process multiple images in parallel
3. **Model Caching**: Models are loaded once at startup
4. **Database Indexing**: Create indexes on frequently queried fields

## Security Notes

- Keep `.env` file secure and never commit it
- Use strong FLASK_SECRET_KEY
- Enable HTTPS in production
- Validate and sanitize all inputs
- Rate limit API endpoints

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.
