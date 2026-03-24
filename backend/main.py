import os
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI(title="Offline Conflict Registry API")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'incidents.db'))

@app.get("/api/incidents")
def get_incidents(q: Optional[str] = None, limit: int = 100):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if q:
            search = f"%{q}%"
            cursor.execute('''
                SELECT * FROM incidents 
                WHERE summary LIKE ? OR location LIKE ? OR state LIKE ? OR attack_type LIKE ?
                ORDER BY year DESC, month DESC, date DESC
                LIMIT ?
            ''', (search, search, search, search, limit))
        else:
            cursor.execute('''
                SELECT * FROM incidents 
                ORDER BY year DESC, month DESC, date DESC
                LIMIT ?
            ''', (limit,))
            
        rows = cursor.fetchall()
        conn.close()
        
        return {
            "success": True,
            "data": [dict(row) for row in rows]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/")
def read_root():
    return {"message": "Offline Conflict Registry API is running."}
