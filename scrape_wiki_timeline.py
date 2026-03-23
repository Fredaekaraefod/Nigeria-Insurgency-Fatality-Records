import urllib.request
import re
import datetime
import os

OUTPUT_DIR = r"c:\Users\User\Documents\Boko haram research"

def parse_wikipedia_timeline():
    # Wikipedia has a robust unified timeline page where all years are listed
    url = "https://en.wikipedia.org/wiki/Timeline_of_the_Boko_Haram_insurgency"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
    except Exception as e:
        print("Failed to fetch timeline:", e)
        return []

    # Linear scan to maintain `current_year`
    events = []
    current_year = 2009 
    
    # We find all h* tags and li tags sequentially
    tokens = re.finditer(r'<h[234][^>]*>.*?</h[234]>|<li[^>]*>(.*?)</li>', html, re.IGNORECASE | re.DOTALL)
    
    date_pattern = re.compile(r'^\s*([0-9]{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+[0-9]{1,2})', re.IGNORECASE)
    
    for match in tokens:
        full_match = match.group(0)
        
        # If it's a heading, update the year
        if full_match.lower().startswith('<h'):
            year_match = re.search(r'\b(20[12][0-9])\b', full_match)
            if year_match:
                current_year = int(year_match.group(1))
            continue
            
        # If it's a list item
        if full_match.lower().startswith('<li'):
            # Only care about 2016-2026
            if current_year < 2016 or current_year > 2026:
                continue
                
            item = match.group(1)
            text = re.sub(r'<[^>]+>', '', item).strip()
            text = text.replace('&#160;', ' ').replace('&nbsp;', ' ').replace('&amp;', '&')
            
            d_match = date_pattern.search(text)
            if not d_match:
                continue
                
            date_str = d_match.group(1).strip()
            
            desc = text.split('–', 1)[-1].strip() if '–' in text else text.split('-', 1)[-1].strip()
            if desc == text:
                desc = text[len(date_str):].strip(' -:')
                
            if len(desc) < 15 or "References" in desc or "Navigation" in desc or "^" in desc:
                continue

            fatalities = "Unknown"
            fat_match = re.search(r'([0-9]+)\s+(?:people\s+)?(?:were\s+)?killed', desc, re.IGNORECASE)
            if fat_match: fatalities = fat_match.group(1)
            else:
                fat_match = re.search(r'killed(?:\s+at\s+least)?\s+([0-9]+)', desc, re.IGNORECASE)
                if fat_match: fatalities = fat_match.group(1)
                    
            location = "Unknown"
            loc_match = re.search(r'(?:in|at)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)', desc)
            if loc_match: location = loc_match.group(1)
                
            state = "Unknown"
            if "Borno" in text: state = "Borno"
            elif "Yobe" in text: state = "Yobe"
            elif "Adamawa" in text: state = "Adamawa"
            elif "Kano" in text: state = "Kano"
            
            attack_type = "Armed Attack"
            if "suicide" in text.lower(): attack_type = "Suicide Bombing"
            elif "ambush" in text.lower(): attack_type = "Ambush"
            elif "kidnap" in text.lower() or "abduct" in text.lower(): attack_type = "Kidnapping / Raid"
            elif "raid" in text.lower(): attack_type = "Raid"
            
            try:
                parsed_date = datetime.datetime.strptime(f"{date_str} {current_year}", "%B %d %Y")
            except ValueError:
                try:
                    parsed_date = datetime.datetime.strptime(f"{date_str} {current_year}", "%d %B %Y")
                except ValueError:
                    parsed_date = None
                    
            if parsed_date:
                final_date = parsed_date.strftime("%Y-%m-%d")
                quarter = (parsed_date.month - 1) // 3 + 1
            else:
                continue 
                
            desc = desc.replace('\n', ' ').replace('\r', '').replace('|', '/')
            
            events.append({
                "date": final_date,
                "year": current_year,
                "quarter": quarter,
                "state": state,
                "location": location,
                "type": attack_type,
                "fatalities": fatalities,
                "source": "[Wikipedia Timeline](https://en.wikipedia.org/wiki/Timeline_of_the_Boko_Haram_insurgency)",
                "summary": desc[:250] + "..." if len(desc) > 250 else desc,
                "status": "Publicly Documented"
            })
            
    return events


def main():
    events = parse_wikipedia_timeline()
    
    unique_events = []
    seen = set()
    for e in events:
        identifier = f"{e['date']}_{e['summary'][:20]}"
        if identifier not in seen:
            seen.add(identifier)
            unique_events.append(e)
            
    print(f"\nSuccessfully scraped {len(unique_events)} unique events from Wikipedia from 2016-2025.")
    
    if not unique_events:
        print("No events found. Check internet connection or Wikipedia page formats.")
        return

    all_events = {}
    for e in unique_events:
        key = (e['year'], e['quarter'])
        if key not in all_events:
            all_events[key] = []
        all_events[key].append(e)

    batch_num = 15
    current_id = 281
    
    sorted_keys = sorted(all_events.keys())
    for (year, quarter) in sorted_keys:
        quarter_events = sorted(all_events[(year, quarter)], key=lambda x: x['date'])
        
        filename = os.path.join(OUTPUT_DIR, f"incidents_batch_{batch_num}.md")
        
        q_start_month = (quarter - 1) * 3 + 1
        q_end_month = quarter * 3
        start_month_name = datetime.date(year, q_start_month, 1).strftime('%B')
        end_month_name = datetime.date(year, q_end_month, 1).strftime('%B')
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Boko Haram Incidents: Batch {batch_num} ({start_month_name} {year} – {end_month_name} {year})\n\n")
            f.write("| Incident_ID | Date | State | City/Town/Village | Type of Attack | Estimated Fatalities | Primary Source | Secondary Source(s) | Summary | Verification Status |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
            
            for event in quarter_events:
                f.write(f"| BH-{current_id} | {event['date']} | {event['state']} | {event['location']} | {event['type']} | {event['fatalities']} | {event['source']} | Open Source Extracts | {event['summary']} | {event['status']} |\n")
                current_id += 1
                
        print(f"Generated {filename} with {len(quarter_events)} events.")
        batch_num += 1

if __name__ == "__main__":
    main()
