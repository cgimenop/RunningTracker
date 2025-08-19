import re
import os
from flask import Flask, render_template
from pymongo import MongoClient
from collections import defaultdict
from datetime import timedelta
from const import MERGE_COLUMNS, FRIENDLY_COLUMN_NAMES, DETAILED_DATA_SAMPLE_INTERVAL, MIN_VALID_LAP_DISTANCE

app = Flask(__name__)

# Load configuration based on environment
env = os.getenv('FLASK_ENV', 'production')
if env == 'development':
    from config.development import DEBUG, MONGO_URI, DATABASE_NAME
else:
    from config.production import DEBUG, MONGO_URI, DATABASE_NAME

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

@app.template_filter('regex_search')
def regex_search(s, pattern):
    return re.search(pattern, s)

@app.template_filter('format_distance')
def format_distance_filter(distance_m):
    return format_distance(distance_m)

@app.template_filter('format_altitude')
def format_altitude_filter(altitude_m):
    return format_altitude(altitude_m)

@app.template_filter('friendly_name')
def friendly_name_filter(column_name):
    return get_friendly_column_name(column_name)

def format_seconds(seconds):
    try:
        return str(timedelta(seconds=int(float(seconds))))
    except (ValueError, TypeError):
        return "00:00:00"

def format_distance(distance_m):
    try:
        distance = float(distance_m)
        if distance >= 1000:
            return f"{distance / 1000:.2f} km"
        else:
            return f"{distance:.2f} m"
    except (ValueError, TypeError):
        return "0.00 m"

def format_altitude(altitude_m):
    try:
        return f"{float(altitude_m):.2f} m"
    except (ValueError, TypeError):
        return "0.00 m"

def get_friendly_column_name(column_name):
    """Convert technical column names to human-friendly names"""
    return FRIENDLY_COLUMN_NAMES.get(column_name, column_name)

def extract_date_from_filename(filename):
    match = re.search(r'([0-9]{4}-[0-9]{2}-[0-9]{2})', filename)
    return match.group(1) if match else filename

def load_summary_data():
    summary_data = list(db["summary"].find({}, {"_id": 0}))
    grouped = defaultdict(list)
    all_laps = []
    for row in summary_data:
        source = row.get("_source_file", "Unknown")
        if "LapTotalTime_s" in row:
            row["LapTotalTime_formatted"] = format_seconds(row["LapTotalTime_s"])
        if "LapDistance_m" in row:
            row["LapDistance_formatted"] = format_distance(row["LapDistance_m"])
        grouped[source].append(row)
    
    # Calculate altitude deltas for each file (need detailed data for max/min calculation)
    for source, laps in grouped.items():
        # Get detailed data for this source to calculate lap altitude deltas
        source_detailed = list(db["detailed"].find({"_source_file": source}, {"_id": 0}).sort("Time", 1))
        
        for lap in laps:
            lap_num = lap.get("LapNumber")
            if lap_num is not None:
                # Find all detailed points for this lap
                lap_points = [p for p in source_detailed if p.get("LapNumber") == lap_num and p.get("Altitude_m") is not None]
                
                if lap_points:
                    try:
                        altitudes = [float(p["Altitude_m"]) for p in lap_points]
                        
                        # Accumulate all elevation changes between consecutive checkpoints
                        total_elevation_change = 0
                        for i in range(1, len(altitudes)):
                            change = altitudes[i] - altitudes[i-1]
                            total_elevation_change += change  # Accumulate signed changes
                            
                        lap["AltitudeDelta_m"] = total_elevation_change
                    except (ValueError, TypeError):
                        lap["AltitudeDelta_m"] = 0
                else:
                    lap["AltitudeDelta_m"] = 0
            else:
                lap["AltitudeDelta_m"] = 0
            
            lap["AltitudeDelta_formatted"] = format_altitude(lap["AltitudeDelta_m"])
    
    # Build all_laps after altitude delta calculation
    for source, laps in grouped.items():
        for lap in laps:
            row_copy = lap.copy()
            row_copy["_source_file"] = source
            all_laps.append(row_copy)
    return grouped, all_laps

def calculate_file_summaries(grouped):
    file_summaries = []
    file_all_laps = {}
    file_valid_laps = {}
    for source, laps in grouped.items():
        try:
            valid = [l for l in laps if l.get("LapDistance_m") is not None and float(l["LapDistance_m"]) >= MIN_VALID_LAP_DISTANCE]
        except (ValueError, TypeError):
            valid = []
        file_all_laps[source] = laps
        file_valid_laps[source] = valid
        try:
            total_distance = sum(float(l.get("LapDistance_m", 0)) for l in laps)
            total_time = sum(float(l.get("LapTotalTime_s", 0)) for l in laps)
        except (ValueError, TypeError):
            total_distance = total_time = 0
        total_time_formatted = format_seconds(total_time)
        file_summaries.append({
            "source": source,
            "date": extract_date_from_filename(source),
            "total_distance": total_distance,
            "total_distance_formatted": format_distance(total_distance),
            "total_time": total_time,
            "total_time_formatted": total_time_formatted
        })
    return file_summaries, file_all_laps, file_valid_laps

def find_records(all_laps, file_summaries):
    try:
        valid_laps = [lap for lap in all_laps if lap.get("LapDistance_m") is not None and float(lap["LapDistance_m"]) >= MIN_VALID_LAP_DISTANCE]
    except (ValueError, TypeError):
        valid_laps = []
    
    try:
        fastest_lap = min((lap for lap in valid_laps if lap.get("LapTotalTime_s") is not None), key=lambda x: float(x["LapTotalTime_s"]), default=None)
        slowest_lap = max((lap for lap in valid_laps if lap.get("LapTotalTime_s") is not None), key=lambda x: float(x["LapTotalTime_s"]), default=None)
    except (ValueError, TypeError):
        fastest_lap = slowest_lap = None
    try:
        longest_distance_file = max(file_summaries, key=lambda x: x["total_distance"], default=None)
        longest_time_file = max(file_summaries, key=lambda x: x["total_time"], default=None)
    except (ValueError, TypeError):
        longest_distance_file = longest_time_file = None
    
    return fastest_lap, slowest_lap, longest_distance_file, longest_time_file

def load_detailed_data():
    detailed_data = list(db["detailed"].find({}, {"_id": 0}).sort("Time", 1))
    detailed_grouped = defaultdict(list)
    
    for source in set(row.get("_source_file", "Unknown") for row in detailed_data):
        source_data = [row for row in detailed_data if row.get("_source_file") == source]
        
        # Filter to show every N seconds
        filtered_data = []
        last_time = None
        
        for i, row in enumerate(source_data):
            # Always include first row
            if i == 0:
                filtered_data.append(row)
                last_time = i
            # Include every Nth row (approximately N seconds)
            elif i - last_time >= DETAILED_DATA_SAMPLE_INTERVAL:
                filtered_data.append(row)
                last_time = i
        
        # Format fields and add cell merging info
        
        for i, row in enumerate(filtered_data):
            # Format fields
            if "LapDistance_m" in row and row["LapDistance_m"] is not None:
                row["LapDistance_formatted"] = format_distance(row["LapDistance_m"])
            if "Distance_m" in row and row["Distance_m"] is not None:
                row["Distance_formatted"] = format_distance(row["Distance_m"])
            if "Altitude_m" in row and row["Altitude_m"] is not None:
                row["Altitude_formatted"] = format_altitude(row["Altitude_m"])
            if "LapTotalTime_s" in row and row["LapTotalTime_s"] is not None:
                row["LapTotalTime_formatted"] = format_seconds(row["LapTotalTime_s"])
            
            # Calculate altitude delta from previous sample
            if i == 0:
                row["AltitudeDelta_m"] = 0  # First sample has no delta
            else:
                try:
                    prev_alt = float(filtered_data[i-1].get("Altitude_m", 0))
                    curr_alt = float(row.get("Altitude_m", 0))
                    row["AltitudeDelta_m"] = curr_alt - prev_alt
                except (ValueError, TypeError):
                    row["AltitudeDelta_m"] = 0
            row["AltitudeDelta_formatted"] = format_altitude(row["AltitudeDelta_m"])
            
            # Add merging info for each column
            row["_merge_info"] = {}
            for col in MERGE_COLUMNS:
                if col in row:
                    # Check if this is the first occurrence of this value
                    is_first = i == 0 or (i > 0 and filtered_data[i-1].get(col) != row[col])
                    
                    if is_first:
                        # Count consecutive rows with same value
                        rowspan = 1
                        for j in range(i + 1, len(filtered_data)):
                            if filtered_data[j].get(col) == row[col]:
                                rowspan += 1
                            else:
                                break
                        row["_merge_info"][col] = {"show": True, "rowspan": rowspan}
                    else:
                        row["_merge_info"][col] = {"show": False, "rowspan": 1}
        
        detailed_grouped[source] = filtered_data
    
    return detailed_grouped

@app.route("/")
def index():
    grouped, all_laps = load_summary_data()
    file_summaries, file_all_laps, file_valid_laps = calculate_file_summaries(grouped)
    fastest_lap, slowest_lap, longest_distance_file, longest_time_file = find_records(all_laps, file_summaries)
    detailed_grouped = load_detailed_data()
    
    return render_template(
        "index.html",
        grouped=grouped,
        file_summaries=file_summaries,
        file_all_laps=file_all_laps,
        file_valid_laps=file_valid_laps,
        fastest_lap=fastest_lap,
        slowest_lap=slowest_lap,
        longest_distance_file=longest_distance_file,
        longest_time_file=longest_time_file,
        detailed=detailed_grouped
    )

if __name__ == "__main__":
    app.run(debug=DEBUG)