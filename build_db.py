import os
import sqlite3
import re
import calendar

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

def extract_fatalities(summary, current_fatality):
    if current_fatality > 0:
        return current_fatality
        
    patterns = [
        r'(\d+)\s+(?:[A-Za-z\-]+\s+){0,6}(?:were\s|are\s|was\s|is\s)?(?:killed|dead|slain|neutralized|died|massacred|murdered|assassinated|killing|beheaded|executed)',
        r'(?:killed|dead|slain|neutralized|died|massacred|murdered|assassinated|killing|beheaded|executed)\s+(?:at\s+least\s+|about\s+|nearly\s+|up\s+to\s+|over\s+|an\s+|a\s+)?(\d+)'
    ]
    
    max_f = 0
    for p in patterns:
        matches = re.findall(p, summary, re.IGNORECASE)
        for m in matches:
            val = int(m)
            if val < 1900 or val > 2100: # avoid years
                if val > max_f:
                    max_f = val
                    
    word_map = {
        'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 
        'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 
        'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20, 
        'dozens': 24, 'scores': 40
    }
    if max_f == 0:
        for w, val in word_map.items():
            p1 = fr'\b{w}\b\s+(?:[A-Za-z\-]+\s+){{0,6}}(?:were\s+|was\s+|are\s+|is\s+)?(?:killed|dead|slain|neutralized|died|massacred|murdered|assassinated|beheaded|executed)'
            p2 = fr'(?:killed|dead|slain|neutralized|died|massacred|killing|beheaded|executed)\s+(?:at\s+least\s+|about\s+|nearly\s+|up\s+to\s+|over\s+)?\b{w}\b'
            if re.search(p1, summary, re.IGNORECASE) or re.search(p2, summary, re.IGNORECASE):
                if val > max_f:
                    max_f = val

    return max_f

def extract_location(summary, current_location):
    c_loc = current_location.strip()
    if c_loc and c_loc.lower() not in ["unknown", "unspecified", "none", "-"]:
        return c_loc
        
    # Attempt to extract location from summary
    prepositions = r'\b(?:in|at|near|on|along|around|from|outside|towards|into|surrounding)\b'
    modifiers = r'(?:the\s+|a\s+|an\s+|northern\s+|southern\s+|eastern\s+|western\s+|central\s+|rural\s+|local\s+)*'
    place_types = r'(?:village\s+of|villages\s+of|town\s+of|city\s+of|state\s+of|community\s+of|district\s+of|area\s+of|island\s+of|region\s+of|village|villages|town|community|city|state|district|area|region|island|islands|road)?\s*'
    proper_noun = r'([A-Z][a-zA-Z]+(?:-[A-Z][a-zA-Z]+)*(?:\s+[A-Z][a-zA-Z]+(?:-[A-Z][a-zA-Z]+)*)*)'

    pattern = f"{prepositions}\\s+{modifiers}{place_types}(?:of\\s+)?{proper_noun}"
    bad_words = ['the', 'a', 'an', 'nigerian', 'army', 'military', 'troops', 'soldiers', 'boko', 'haram', 'iswap', 'multinational', 'joint', 'task', 'force', 'mnjtf', 'operation', 'suspected', 'armed', 'jihadists', 'police', 'state', 'government']
    
    match = re.search(pattern, summary)
    if match:
        extracted = match.group(1).strip()
        if not any(w in extracted.lower().split() for w in bad_words):
            return extracted
            
    pattern2 = f"\\b(?:village|villages|town|community|city|state|district|area|region|island|road|base|camp)\\s+of\\s+{proper_noun}"
    match2 = re.search(pattern2, summary)
    if match2:
        extracted = match2.group(1).strip()
        if not any(w in extracted.lower().split() for w in bad_words):
            return extracted
    return "Unknown"
    
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
            "Incident id" TEXT PRIMARY KEY,
            "Date" TEXT,
            "Year" INTEGER,
            "Month" INTEGER,
            "Month name" TEXT,
            "State" TEXT,
            "Location" TEXT,
            "Attack type" TEXT,
            "Fatalities" INTEGER,
            "Primary source" TEXT,
            "Secondary source" TEXT,
            "Summary" TEXT,
            "Verification status" TEXT
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
                        cursor.execute('SELECT "Incident id" FROM incidents WHERE "Incident id"=?', (inc_id,))
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
                        
                        # Clean up annoying Wikipedia citation brackets like &#91;715&#93;
                        summary = re.sub(r'&#91;\d+&#93;', '', summary).strip()
                        
                        status = parts[10]
                        
                        location = extract_location(summary, location)
                        fatalities = extract_fatalities(summary, fatalities)
                        
                        year = 0
                        month = 0
                        # Extract parsed Year/Month for super easy query access
                        if "-" in date_str and len(date_str) >= 10:
                            try:
                                year = int(date_str.split('-')[0])
                                month = int(date_str.split('-')[1])
                            except ValueError:
                                pass
                                
                        month_name = calendar.month_name[month] if 1 <= month <= 12 else "Unknown"

                        cursor.execute('''
                            INSERT INTO incidents 
                            ("Incident id", "Date", "Year", "Month", "Month name", "State", "Location", "Attack type", "Fatalities", "Primary source", "Secondary source", "Summary", "Verification status")
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (inc_id, date_str, year, month, month_name, state, location, attack_type, fatalities, primary_source, secondary_source, summary, status))
                        
                        total_inserted += 1
                        
    conn.commit()
    conn.close()
    
    print(f"Database build complete! Successfully inserted {total_inserted} unified conflict events into incidents.db.")

if __name__ == "__main__":
    build_database()
