import os
import sqlite3
import re

DATA_DIR = r"c:\Users\User\Documents\Boko haram research"
DB_FILE = os.path.join(DATA_DIR, "incidents.db")

def clean_fatality(f_str):
    # Extracts the numeric value for fatalities to enable accurate SQL (> <) querying
    f_str = str(f_str).strip()
    if not f_str or f_str.lower() in ["unknown", "unspecified", "none"]:
        return 0
    # Find the very first sequence of digits (if things like "14–42" exist, takes the upper bound safely, or lower bound)
    nums = re.findall(r'\d+', f_str)
    if nums:
        # if a range like 14-42 is provided, taking max is common for conflict data worst-case
        return max([int(n) for n in nums])
    return 0
    
def build_database():
    print(f"Initializing {DB_FILE}...")
    
    # Remove old db if exists
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create the incidents table optimized for SQL querying
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            incident_id TEXT PRIMARY KEY,
            date TEXT,
            year INTEGER,
            month INTEGER,
            state TEXT,
            location TEXT,
            attack_type TEXT,
            fatalities INTEGER,
            primary_source TEXT,
            secondary_source TEXT,
            summary TEXT,
            verification_status TEXT
        )
    ''')
    
    total_inserted = 0
    
    for filename in os.listdir(DATA_DIR):
        if filename.startswith("incidents_batch_") and filename.endswith(".md"):
            filepath = os.path.join(DATA_DIR, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                if line.startswith("|") and not line.startswith("| Incident_ID") and not line.startswith("| :---"):
                    parts = [p.strip() for p in line.split('|')]
                    
                    if len(parts) >= 11:
                        inc_id = parts[1]
                        
                        # Only insert actual records (BH-XXX)
                        if not inc_id.startswith("BH-"):
                            continue
                            
                        # If incident already in db, skip entirely to prevent primary key issues when batches overlap
                        cursor.execute("SELECT incident_id FROM incidents WHERE incident_id=?", (inc_id,))
                        if cursor.fetchone():
                            continue
                            
                        date_str = parts[2]
                        state = parts[3]
                        location = parts[4]
                        attack_type = parts[5]
                        fatalities_raw = parts[6]
                        fatalities = clean_fatality(fatalities_raw)
                        primary_source = parts[7]
                        secondary_source = parts[8]
                        summary = parts[9]
                        status = parts[10]
                        
                        year = 0
                        month = 0
                        # Extract parsed Year/Month for super easy query access
                        if "-" in date_str and len(date_str) >= 10:
                            try:
                                year = int(date_str.split('-')[0])
                                month = int(date_str.split('-')[1])
                            except ValueError:
                                pass
                                
                        cursor.execute('''
                            INSERT INTO incidents 
                            (incident_id, date, year, month, state, location, attack_type, fatalities, primary_source, secondary_source, summary, verification_status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (inc_id, date_str, year, month, state, location, attack_type, fatalities, primary_source, secondary_source, summary, status))
                        
                        total_inserted += 1
                        
    conn.commit()
    conn.close()
    
    print(f"Database build complete! Successfully inserted {total_inserted} unified conflict events into incidents.db.")

if __name__ == "__main__":
    build_database()
