import sqlite3
import os
from typing import Optional, List
import numpy as np
import cv2
import json
from datetime import datetime

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
    
    # Create qa_interactions table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS qa_interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create species_alerts table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS species_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        species TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def save_qa_interaction(question: str, answer: str = None) -> int:
    """Save a QA interaction to the database and return its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO qa_interactions 
        (question, answer)
        VALUES (?, ?)
    """, (question, answer))
    
    qa_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return qa_id

def get_qa_interactions(limit: int = 50) -> List[dict]:
    """Retrieve QA interaction records."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, question, answer, created_at
        FROM qa_interactions
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row[0],
            'question': row[1],
            'answer': row[2],
            'created_at': row[3]
        })
    
    conn.close()
    return results

def get_qa_count(date: str = None) -> int:
    """Get the count of QA interactions, optionally filtered by date."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if date:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM qa_interactions
            WHERE date(created_at) = ?
        """, (date,))
    else:
        cursor.execute("SELECT COUNT(*) FROM qa_interactions")
    
    count = cursor.fetchone()[0]
    conn.close()
    return count

def save_alert(message: str, species: str) -> int:
    """Save a species alert to the database and return its ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO species_alerts 
        (message, species)
        VALUES (?, ?)
    """, (message, species))
    
    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return alert_id

def get_alerts(limit: int = 50) -> List[dict]:
    """Retrieve species alert records."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, message, species, timestamp
        FROM species_alerts
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row[0],
            'message': row[1],
            'species': row[2],
            'timestamp': row[3]
        })
    
    conn.close()
    return results

def get_alert_counts() -> dict:
    """Get total and today's alert counts."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get total alerts count
    cursor.execute("SELECT COUNT(*) FROM species_alerts")
    total_count = cursor.fetchone()[0]
    
    # Get today's alerts count
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        "SELECT COUNT(*) FROM species_alerts WHERE date(timestamp) = ?", 
        (today,)
    )
    today_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total": total_count,
        "today": today_count
    }

def get_species_alert_stats() -> List[dict]:
    """Get statistics on species that triggered alerts."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT species, COUNT(*) as count
        FROM species_alerts
        GROUP BY species
        ORDER BY count DESC
    """)
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'species': row[0],
            'count': row[1]
        })
    
    conn.close()
    return results

# Initialize the database when the module is imported
init_db() 