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
    if not summary:
        return 0

    death_verbs_list = ['killed', 'dead', 'slain', 'neutralized', 'died', 'massacred', 'murdered', 'assassinated', 'killing', 'beheaded', 'executed']
    death_verbs = r'(?:killed|dead|slain|neutralized|died|massacred|murdered|assassinated|killing|beheaded|executed|shot\s+dead)'
    
    word_map = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11,
        'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16,
        'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
        'dozens': 24, 'scores': 40
    }
    word_pattern = '|'.join(sorted(word_map.keys(), key=len, reverse=True))
    
    def word_to_num(w):
        return word_map.get(w.lower(), 0)
    
    def is_year(val):
        return 1900 <= val <= 2100
    
    def to_num(s):
        """Convert a string that is either a digit or a number word to int."""
        s = s.strip().lower()
        if s.isdigit():
            return int(s)
        return word_map.get(s, 0)
    
    # --- Strategy 1: Check for "death toll to/of X" (this is the definitive total) ---
    toll_match = re.search(r'death\s+toll\s+(?:to|of|at|rose\s+to|reached|climbed\s+to|stands\s+at)\s+(\d+)', summary, re.IGNORECASE)
    if toll_match:
        val = int(toll_match.group(1))
        if not is_year(val):
            return val
    
    # --- Strategy 2: Check for "X people/persons, including Y..." with death context ---
    incl_match = re.search(r'(\d+)\s+(?:people|persons|civilians|victims|members),?\s+including', summary, re.IGNORECASE)
    if incl_match:
        val = int(incl_match.group(1))
        if not is_year(val):
            # Check the entire summary for death context (not just nearby)
            if re.search(death_verbs, summary, re.IGNORECASE) or re.search(r'deaths?\s+of', summary, re.IGNORECASE):
                return val
    
    # --- Strategy 3: Split by sentences and sum death counts across sentences ---
    clauses = re.split(r'[.;]', summary)
    
    total_fatalities = 0
    
    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue
        
        # Check if this clause contains death language
        has_death = bool(re.search(death_verbs, clause, re.IGNORECASE))
        has_death_noun = bool(re.search(r'deaths?\s+of', clause, re.IGNORECASE))
        
        if not has_death and not has_death_noun:
            continue
        
        clause_deaths = []
        
        # --- Compound "and" patterns (sum both sides) ---
        # "N word(s) and N word(s) [were] killed/dead/shot dead"
        and_num = re.findall(r'(\d+)\s+[A-Za-z\-]+(?:\s+[A-Za-z\-]+)?\s+and\s+(\d+)\s+[A-Za-z\-]+(?:\s+[A-Za-z\-]+)?\s+(?:were\s+|was\s+)?' + death_verbs, clause, re.IGNORECASE)
        for m in and_num:
            v1, v2 = int(m[0]), int(m[1])
            if not is_year(v1) and not is_year(v2):
                clause_deaths.append(v1 + v2)
        
        # "shot dead N word and N word"
        shot_and = re.findall(r'shot\s+dead\s+(\d+)\s+[A-Za-z\-]+(?:\s+[A-Za-z\-]+)?\s+and\s+(\d+)\s+[A-Za-z\-]+', clause, re.IGNORECASE)
        for m in shot_and:
            v1, v2 = int(m[0]), int(m[1])
            if not is_year(v1) and not is_year(v2):
                clause_deaths.append(v1 + v2)
        
        # "killed/killing N and N"  (without descriptors)
        kill_and = re.findall(death_verbs + r'\s+(\d+)\s+[A-Za-z\-]+(?:\s+[A-Za-z\-]+)?\s+and\s+(\d+)', clause, re.IGNORECASE)
        for m in kill_and:
            v1, v2 = int(m[0]), int(m[1])
            if not is_year(v1) and not is_year(v2):
                clause_deaths.append(v1 + v2)
        
        # "deaths of N word and N word"
        death_and = re.findall(r'deaths?\s+of\s+(\d+)\s+[A-Za-z\-]+(?:\s+[A-Za-z\-]+)?\s+and\s+(\d+)\s+[A-Za-z\-]+', clause, re.IGNORECASE)
        for m in death_and:
            v1, v2 = int(m[0]), int(m[1])
            if not is_year(v1) and not is_year(v2):
                clause_deaths.append(v1 + v2)
        
        # Word-based "and" sums: "one officer and six soldiers were killed"  
        word_and_num = re.search(fr'\b({word_pattern})\b\s+[A-Za-z\-]+(?:\s+[A-Za-z\-]+)?\s+and\s+(?:({word_pattern})|(\d+))\s+[A-Za-z\-]+(?:\s+[A-Za-z\-]+)?\s+(?:were\s+|was\s+)?{death_verbs}', clause, re.IGNORECASE)
        if word_and_num:
            v1 = word_to_num(word_and_num.group(1))
            v2 = word_to_num(word_and_num.group(2)) if word_and_num.group(2) else int(word_and_num.group(3))
            clause_deaths.append(v1 + v2)
        
        # "a/an [noun] and [number/word] [noun] killed" — treat a/an as 1
        article_and = re.search(fr'\b(?:a|an)\s+[A-Za-z\-]+(?:\s+[A-Za-z\-]+)?\s+and\s+(?:({word_pattern})|(\d+))\s+[A-Za-z\-]+(?:\s+[A-Za-z\-]+)?\s+(?:were\s+|was\s+)?{death_verbs}', clause, re.IGNORECASE)
        if article_and:
            v2 = word_to_num(article_and.group(1)) if article_and.group(1) else int(article_and.group(2))
            clause_deaths.append(1 + v2)
        
        # --- Single number patterns ---
        # "N [words] killed/dead/etc"
        for m in re.finditer(r'(\d+)\s+(?:[A-Za-z\-,]+\s+){0,8}(?:were\s+|are\s+|was\s+|is\s+)?' + death_verbs, clause, re.IGNORECASE):
            val = int(m.group(1))
            if not is_year(val):
                clause_deaths.append(val)
        
        # "killed/etc N"  
        for m in re.finditer(death_verbs + r'\s+(?:at\s+least\s+|about\s+|nearly\s+|up\s+to\s+|over\s+|an\s+|a\s+)?(\d+)', clause, re.IGNORECASE):
            val = int(m.group(1))
            if not is_year(val):
                clause_deaths.append(val)
        
        # "death(s) of N"
        for m in re.finditer(r'deaths?\s+of\s+(?:at\s+least\s+|about\s+|nearly\s+|up\s+to\s+|over\s+)?(\d+)', clause, re.IGNORECASE):
            val = int(m.group(1))
            if not is_year(val):
                clause_deaths.append(val)
        
        # Word-based: "three soldiers were killed" / "Four of those kidnapped were later beheaded"
        for m in re.finditer(fr'\b({word_pattern})\b\s+(?:[A-Za-z\-]+\s+){{0,6}}(?:were\s+|was\s+|are\s+|is\s+)?{death_verbs}', clause, re.IGNORECASE):
            clause_deaths.append(word_to_num(m.group(1)))
        
        # Word-based reverse: "killed three", "death of ten", "killing four"
        for m in re.finditer(fr'(?:{death_verbs}|deaths?\s+of)\s+(?:at\s+least\s+|about\s+|nearly\s+|up\s+to\s+|over\s+)?\b({word_pattern})\b', clause, re.IGNORECASE):
            clause_deaths.append(word_to_num(m.group(1)))
        
        # "leaving N dead"
        for m in re.finditer(r'leaving\s+(?:at\s+least\s+|about\s+)?(\d+)\s+(?:[A-Za-z\-]+\s+){0,4}dead', clause, re.IGNORECASE):
            val = int(m.group(1))
            if not is_year(val):
                clause_deaths.append(val)
        
        # "officer and a friend shot dead" (no numbers, implied 2)
        if re.search(r'and\s+(?:a|an)\s+\w+\s+' + death_verbs, clause, re.IGNORECASE) and not clause_deaths:
            clause_deaths.append(2)
        
        # Pick the max for this clause (the "and" sum patterns will naturally be the largest)
        if clause_deaths:
            total_fatalities += max(clause_deaths)
    
    if total_fatalities > 0:
        return total_fatalities
    
    # --- Fallback ---
    max_f = 0
    simple_patterns = [
        r'(\d+)\s+(?:[A-Za-z\-]+\s+){0,6}(?:were\s|are\s|was\s|is\s)?' + death_verbs,
        r'(?:' + death_verbs + r'|deaths?\s+of)\s+(?:at\s+least\s+|about\s+|nearly\s+|up\s+to\s+|over\s+|an\s+|a\s+)?(\d+)'
    ]    
    for p in simple_patterns:
        for m in re.findall(p, summary, re.IGNORECASE):
            val = int(m)
            if not is_year(val) and val > max_f:
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
                        extracted_fatalities = extract_fatalities(summary, 0)
                        fatalities = max(fatalities, extracted_fatalities)
                        
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
