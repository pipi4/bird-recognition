import sqlite3
import os
from typing import Optional, List
import numpy as np
import cv2

# Database file path
DB_PATH = "yolo_data_test.db"

def init_db():
    """Initialize the database with required tables."""
    # Remove existing database file if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create images table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_data BLOB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create video_frames table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS video_frames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        frame_data BLOB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

# Initialize the database when the module is imported
init_db() 