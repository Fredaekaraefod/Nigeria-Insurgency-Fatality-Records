import os
import sqlite3
import csv
import io
from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
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
                WHERE "Summary" LIKE ? OR "Location" LIKE ? OR "State" LIKE ? OR "Attack type" LIKE ?
                ORDER BY "Year" DESC, "Month" DESC, "Date" DESC
                LIMIT ?
            ''', (search, search, search, search, limit))
        else:
            cursor.execute('''
                SELECT * FROM incidents 
                ORDER BY "Year" DESC, "Month" DESC, "Date" DESC
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

@app.get("/api/download-db")
def download_db():
    if os.path.exists(DB_PATH):
        return FileResponse(path=DB_PATH, filename="incidents.db", media_type="application/octet-stream")
    return {"error": "Database file not found."}

@app.get("/api/download-csv")
def download_csv():
    try:
        if not os.path.exists(DB_PATH):
            return {"error": "Database file not found."}
            
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM incidents ORDER BY "Year" DESC, "Month" DESC, "Date" DESC')
        rows = cursor.fetchall()
        conn.close()

        output = io.StringIO()
        if not rows:
            return {"error": "No data available."}
            
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
            
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]), 
            media_type="text/csv", 
            headers={"Content-Disposition": "attachment; filename=incidents.csv"}
        )
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def read_root():
    return {"message": "Offline Conflict Registry API is running."}
