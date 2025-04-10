import sqlite3
import os
from typing import Optional, List
import numpy as np
import cv2
import json

# Database file path
DB_PATH = "yolo_data.db"

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create images table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_data BLOB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create video_frames table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS video_frames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        frame_data BLOB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create detection_history table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS detection_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_id INTEGER,
        frame_id INTEGER,
        detected_objects TEXT NOT NULL,
        confidence FLOAT,
        has_warning BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (image_id) REFERENCES images(id),
        FOREIGN KEY (frame_id) REFERENCES video_frames(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def save_image(image_data: np.ndarray) -> int:
    """Save an image to the database and return its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Convert numpy array to bytes
    success, encoded_image = cv2.imencode(".png", image_data)
    if not success:
        raise ValueError("Failed to encode image")
    
    cursor.execute("INSERT INTO images (image_data) VALUES (?)", 
                  (encoded_image.tobytes(),))
    image_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return image_id

def get_image(image_id: int) -> Optional[np.ndarray]:
    """Retrieve an image from the database by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT image_data FROM images WHERE id = ?", (image_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result is None:
        return None
    
    # Convert bytes back to numpy array
    nparr = np.frombuffer(result[0], np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

def save_video_frame(frame_data: np.ndarray) -> int:
    """Save a video frame to the database and return its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Convert numpy array to bytes
    success, encoded_frame = cv2.imencode(".png", frame_data)
    if not success:
        raise ValueError("Failed to encode frame")
    
    cursor.execute("INSERT INTO video_frames (frame_data) VALUES (?)", 
                  (encoded_frame.tobytes(),))
    frame_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return frame_id

def get_video_frame(frame_id: int) -> Optional[np.ndarray]:
    """Retrieve a video frame from the database by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT frame_data FROM video_frames WHERE id = ?", (frame_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result is None:
        return None
    
    # Convert bytes back to numpy array
    nparr = np.frombuffer(result[0], np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

def save_detection_history(image_id: Optional[int] = None, frame_id: Optional[int] = None, 
                         detected_objects: List[str] = None, confidence: float = None,
                         has_warning: bool = False) -> int:
    """Save a detection record to history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO detection_history 
        (image_id, frame_id, detected_objects, confidence, has_warning)
        VALUES (?, ?, ?, ?, ?)
    """, (image_id, frame_id, json.dumps(detected_objects), confidence, has_warning))
    
    history_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return history_id

def get_detection_history(limit: int = 50) -> List[dict]:
    """Retrieve detection history records."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, image_id, frame_id, detected_objects, confidence, has_warning, created_at
        FROM detection_history
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row[0],
            'image_id': row[1],
            'frame_id': row[2],
            'detected_objects': json.loads(row[3]),
            'confidence': row[4],
            'has_warning': bool(row[5]),
            'created_at': row[6]
        })
    
    conn.close()
    return results

# Initialize the database when the module is imported
init_db() 