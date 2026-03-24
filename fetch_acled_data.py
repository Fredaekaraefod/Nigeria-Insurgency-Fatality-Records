import os
import requests
import datetime
import math

# --- ACLED API CONFIGURATION ---
# Please replace with your registered ACLED email and access key.
# Register for free at: https://developer.acleddata.com/
EMAIL = "fredaefod@gmail.com"
ACCESS_KEY = "YOUR_ACCESS_KEY_HERE"

def fetch_acled_data(start_year=2016, end_year=2025):
    print("Fetching ACLED data for Nigeria...")
    url = "https://api.acleddata.com/acled/read/"
    
    # Query for Nigeria between the dates and limit results to ensure we don't cap early 
    params = {
        "key": ACCESS_KEY,
        "email": EMAIL,
        "country": "Nigeria",
        "event_date": f"{start_year}-01-01|{end_year}-12-31",
        "event_date_where": "BETWEEN",
        "limit": 10000 
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Failed to fetch data: {response.status_code}")
        print(response.text)
        return []
        
    data = response.json()
    if not data.get("success"):
        print("API returned an error:")
        print(data)
        if "Please provide valid credentials" in str(data):
            print("\n*** MAKE SURE you have replaced EMAIL and ACCESS_KEY at the top of this script! ***\n")
        return []
        
    events = data.get("data", [])
    
    # Filter for Boko Haram / ISWAP
    filtered_events = []
    target_actors = ["Boko Haram", "Islamic State (West Africa)"]
    for event in events:
        actor1 = event.get("actor1", "")
        actor2 = event.get("actor2", "")
        assoc1 = event.get("assoc_actor_1", "")
        assoc2 = event.get("assoc_actor_2", "")
        
        relevant = False
        for tgt in target_actors:
            if tgt in actor1 or tgt in actor2 or tgt in assoc1 or tgt in assoc2:
                relevant = True
                break
                
        if relevant:
            filtered_events.append(event)
            
    # Sort by date
    filtered_events.sort(key=lambda x: x.get("event_date", ""))
    return filtered_events

def chunk_events_by_quarter(events):
    # Groups events into batches of 3 months (Quarters)
    batches = {}
    for event in events:
        date_str = event.get("event_date", "")
        if not date_str:
            continue
            
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            year = dt.year
            quarter = math.ceil(dt.month / 3)
            key = (year, quarter)
            if key not in batches:
                batches[key] = []
            batches[key].append(event)
        except ValueError:
            continue
            
    return batches

def main():
    if EMAIL == "YOUR_EMAIL_HERE" or ACCESS_KEY == "YOUR_ACCESS_KEY_HERE":
        print("ERROR: Please update EMAIL and ACCESS_KEY in the script with your ACLED developer credentials.")
        return

    events = fetch_acled_data()
    if not events:
        print("No events fetched or there was an error. Exiting.")
        return

    print(f"Found {len(events)} relevant incidents.")
    
    batches = chunk_events_by_quarter(events)
    sorted_quarters = sorted(batches.keys())
    
    batch_num = 15
    current_id = 281
    output_dir = r"c:\Users\User\Documents\Boko haram research"
    
    for (year, quarter) in sorted_quarters:
        quarter_events = batches[(year, quarter)]
        filename = os.path.join(output_dir, f"incidents_batch_{batch_num}.md")
        
        # Quarter mapping
        q_start_month = (quarter - 1) * 3 + 1
        q_end_month = quarter * 3
        start_month_name = datetime.date(year, q_start_month, 1).strftime('%B')
        end_month_name = datetime.date(year, q_end_month, 1).strftime('%B')
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Boko Haram Incidents: Batch {batch_num} ({start_month_name} {year} – {end_month_name} {year})\n\n")
            f.write("| Incident_ID | Date | State | City/Town/Village | Type of Attack | Estimated Fatalities | Primary Source | Secondary Source(s) | Summary | Verification Status |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
            
            for event in quarter_events:
                date = event.get("event_date", "")
                state = event.get("admin1", "Unknown")
                location = event.get("location", "Unknown")
                attack_type = event.get("event_type", "") + " / " + event.get("sub_event_type", "")
                fatalities = event.get("fatalities", "0")
                source = event.get("source", "Unknown")
                # Clean up newlines for the markdown table
                summary = event.get("notes", "No summary").replace('\n', ' ').replace('\r', '').replace('|', '/')
                
                status = "Confirmed"
                
                f.write(f"| BH-{current_id} | {date} | {state} | {location} | {attack_type} | {fatalities} | {source} | ACLED API | {summary} | {status} |\n")
                current_id += 1
                
        print(f"Generated {filename} with {len(quarter_events)} incidents.")
        batch_num += 1

    print("\nAll batches generated successfully! You can now commit these to your repository.")

if __name__ == "__main__":
    main()
