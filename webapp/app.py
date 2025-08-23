import re
import os
import logging
from flask import Flask, render_template
from pymongo import MongoClient
from collections import defaultdict
from datetime import timedelta
from logging_config import setup_webapp_logging
from const import (MERGE_COLUMNS, FRIENDLY_COLUMN_NAMES, DETAILED_DATA_SAMPLE_INTERVAL, MIN_VALID_LAP_DISTANCE,
                   COLLECTION_SUMMARY, COLLECTION_DETAILED, COL_ID, COL_SOURCE_FILE, COL_LAP_TOTAL_TIME_S,
                   COL_LAP_DISTANCE_M, COL_LAP_NUMBER, COL_ALTITUDE_M, COL_ALTITUDE_DELTA_M, COL_DISTANCE_M,
                   COL_TIME, COL_LAP_TOTAL_TIME_FORMATTED, COL_LAP_DISTANCE_FORMATTED, COL_ALTITUDE_FORMATTED,
                   COL_ALTITUDE_DELTA_FORMATTED, COL_DISTANCE_FORMATTED, FIELD_SOURCE, FIELD_DATE,
                   FIELD_TOTAL_DISTANCE, FIELD_TOTAL_DISTANCE_FORMATTED, FIELD_TOTAL_TIME,
                   FIELD_TOTAL_TIME_FORMATTED, FIELD_MERGE_INFO)

# Setup logging
logger = setup_webapp_logging()

app = Flask(__name__)

# Load configuration based on environment - use server-side config only
# Fixed: Use hardcoded server-side configuration instead of client-controlled env
DEBUG = False  # Always False in production
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'RunningTracker')

# Only enable debug mode if explicitly set by server admin
if os.getenv('FLASK_DEBUG') == 'true':
    DEBUG = True

# Global client variable for proper resource management
client = None
db = None

def get_db_connection():
    """Get database connection with proper error handling"""
    global client, db
    if client is None:
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            db = client[DATABASE_NAME]
            # Test connection
            client.server_info()
            logger.info(f"Successfully connected to MongoDB: {DATABASE_NAME}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    return db

def close_db_connection():
    """Close database connection properly"""
    global client, db
    if client:
        client.close()
        client = None
        db = None

@app.template_filter('regex_search')
def regex_search(s, pattern):
    # Only allow safe, predefined patterns to prevent ReDoS attacks
    safe_patterns = {
        'date': r'([0-9]{4}-[0-9]{2}-[0-9]{2})',
        'time': r'([0-9]{2}:[0-9]{2}:[0-9]{2})',
        'number': r'([0-9]+\.?[0-9]*)',
    }
    
    # Validate input string
    if not isinstance(s, str):
        return None
        
    if pattern in safe_patterns:
        return re.search(safe_patterns[pattern], s)
    else:
        # Return None for unsafe patterns
        return None

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
    match = regex_search(filename, 'date')
    return match.group(1) if match else filename

def _is_valid_lap(lap):
    """Check if a lap has valid distance data"""
    distance = lap.get(COL_LAP_DISTANCE_M)
    if distance is None:
        return False
    try:
        return float(distance) >= MIN_VALID_LAP_DISTANCE
    except (ValueError, TypeError):
        return False

def _calculate_lap_altitude_delta(lap, source_detailed):
    """Calculate altitude delta for a single lap"""
    lap_num = lap.get(COL_LAP_NUMBER)
    if lap_num is None:
        return 0
        
    lap_points = [p for p in source_detailed 
                  if p.get(COL_LAP_NUMBER) == lap_num and p.get(COL_ALTITUDE_M) is not None]
    
    if not lap_points:
        return 0
        
    try:
        altitudes = [float(p[COL_ALTITUDE_M]) for p in lap_points]
        return sum(altitudes[i] - altitudes[i-1] for i in range(1, len(altitudes)))
    except (ValueError, TypeError):
        return 0

def _calculate_altitude_deltas(grouped, db):
    """Calculate altitude deltas for all laps in grouped data"""
    # Optimize: Load all detailed data once instead of per source (N+1 fix)
    # Use safe query with no user input
    query = {}
    projection = {COL_ID: 0}
    all_detailed = list(db[COLLECTION_DETAILED].find(query, projection).sort(COL_TIME, 1))
    detailed_by_source = defaultdict(list)
    
    # Group detailed data by source
    for row in all_detailed:
        source = row.get(COL_SOURCE_FILE, "Unknown")
        detailed_by_source[source].append(row)
    
    for source, laps in grouped.items():
        source_detailed = detailed_by_source.get(source, [])
        
        for lap in laps:
            lap[COL_ALTITUDE_DELTA_M] = _calculate_lap_altitude_delta(lap, source_detailed)
            lap[COL_ALTITUDE_DELTA_FORMATTED] = format_altitude(lap[COL_ALTITUDE_DELTA_M])

def _format_summary_data(summary_data):
    """Format summary data and group by source"""
    grouped = defaultdict(list)
    for row in summary_data:
        source = row.get(COL_SOURCE_FILE, "Unknown")
        if COL_LAP_TOTAL_TIME_S in row:
            row[COL_LAP_TOTAL_TIME_FORMATTED] = format_seconds(row[COL_LAP_TOTAL_TIME_S])
        if COL_LAP_DISTANCE_M in row:
            row[COL_LAP_DISTANCE_FORMATTED] = format_distance(row[COL_LAP_DISTANCE_M])
        grouped[source].append(row)
    return grouped

def _build_all_laps(grouped):
    """Build all_laps list from grouped data"""
    all_laps = []
    for source, laps in grouped.items():
        for lap in laps:
            row_copy = lap.copy()
            row_copy[COL_SOURCE_FILE] = source
            all_laps.append(row_copy)
    return all_laps

def load_summary_data():
    db = get_db_connection()
    # Use safe query with no user input
    query = {}
    projection = {COL_ID: 0}
    summary_data = list(db[COLLECTION_SUMMARY].find(query, projection))
    grouped = _format_summary_data(summary_data)
    _calculate_altitude_deltas(grouped, db)
    all_laps = _build_all_laps(grouped)
    return grouped, all_laps

def calculate_file_summaries(grouped):
    file_summaries = []
    file_all_laps = {}
    file_valid_laps = {}
    for source, laps in grouped.items():
        valid = [l for l in laps if _is_valid_lap(l)]
        file_all_laps[source] = laps
        file_valid_laps[source] = valid
        try:
            total_distance = sum(float(l.get(COL_LAP_DISTANCE_M, 0)) for l in laps)
            total_time = sum(float(l.get(COL_LAP_TOTAL_TIME_S, 0)) for l in laps)
        except (ValueError, TypeError):
            total_distance = total_time = 0
        total_time_formatted = format_seconds(total_time)
        file_summaries.append({
            FIELD_SOURCE: source,
            FIELD_DATE: extract_date_from_filename(source),
            FIELD_TOTAL_DISTANCE: total_distance,
            FIELD_TOTAL_DISTANCE_FORMATTED: format_distance(total_distance),
            FIELD_TOTAL_TIME: total_time,
            FIELD_TOTAL_TIME_FORMATTED: total_time_formatted
        })
    return file_summaries, file_all_laps, file_valid_laps

def find_records(all_laps, file_summaries):
    valid_laps = [lap for lap in all_laps if _is_valid_lap(lap)]
    
    try:
        fastest_lap = min((lap for lap in valid_laps if lap.get(COL_LAP_TOTAL_TIME_S) is not None), key=lambda x: float(x[COL_LAP_TOTAL_TIME_S]), default=None)
        slowest_lap = max((lap for lap in valid_laps if lap.get(COL_LAP_TOTAL_TIME_S) is not None), key=lambda x: float(x[COL_LAP_TOTAL_TIME_S]), default=None)
    except (ValueError, TypeError):
        fastest_lap = slowest_lap = None
    try:
        longest_distance_file = max(file_summaries, key=lambda x: x[FIELD_TOTAL_DISTANCE], default=None)
        longest_time_file = max(file_summaries, key=lambda x: x[FIELD_TOTAL_TIME], default=None)
    except (ValueError, TypeError):
        longest_distance_file = longest_time_file = None
    
    return fastest_lap, slowest_lap, longest_distance_file, longest_time_file

def _calculate_merge_info(filtered_data, i):
    """Calculate merge info for table cell merging"""
    merge_info = {}
    for col in MERGE_COLUMNS:
        if col in filtered_data[i]:
            # Check if this is the first occurrence of this value
            is_first = i == 0 or (i > 0 and filtered_data[i-1].get(col) != filtered_data[i][col])
            
            if is_first:
                # Count consecutive rows with same value
                rowspan = 1
                for j in range(i + 1, len(filtered_data)):
                    if filtered_data[j].get(col) == filtered_data[i][col]:
                        rowspan += 1
                    else:
                        break
                merge_info[col] = {"show": True, "rowspan": rowspan}
            else:
                merge_info[col] = {"show": False, "rowspan": 1}
    return merge_info

def _filter_data_by_interval(source_data):
    """Filter data to show every N seconds"""
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
    
    return filtered_data

def load_detailed_data():
    db = get_db_connection()
    # Use safe query with no user input
    query = {}
    projection = {COL_ID: 0}
    detailed_data = list(db[COLLECTION_DETAILED].find(query, projection).sort(COL_TIME, 1))
    detailed_grouped = defaultdict(list)
    
    # Optimize: Group data by source more efficiently
    data_by_source = defaultdict(list)
    for row in detailed_data:
        source = row.get(COL_SOURCE_FILE, "Unknown")
        data_by_source[source].append(row)
    
    for source, source_data in data_by_source.items():
        
        filtered_data = _filter_data_by_interval(source_data)
        
        # Format fields and add cell merging info
        
        for i, row in enumerate(filtered_data):
            # Format fields
            if COL_LAP_DISTANCE_M in row and row[COL_LAP_DISTANCE_M] is not None:
                row[COL_LAP_DISTANCE_FORMATTED] = format_distance(row[COL_LAP_DISTANCE_M])
            if COL_DISTANCE_M in row and row[COL_DISTANCE_M] is not None:
                row[COL_DISTANCE_FORMATTED] = format_distance(row[COL_DISTANCE_M])
            if COL_ALTITUDE_M in row and row[COL_ALTITUDE_M] is not None:
                row[COL_ALTITUDE_FORMATTED] = format_altitude(row[COL_ALTITUDE_M])
            if COL_LAP_TOTAL_TIME_S in row and row[COL_LAP_TOTAL_TIME_S] is not None:
                row[COL_LAP_TOTAL_TIME_FORMATTED] = format_seconds(row[COL_LAP_TOTAL_TIME_S])
            
            # Calculate altitude delta from previous sample
            if i == 0:
                row[COL_ALTITUDE_DELTA_M] = 0  # First sample has no delta
            else:
                try:
                    prev_alt = float(filtered_data[i-1].get(COL_ALTITUDE_M, 0))
                    curr_alt = float(row.get(COL_ALTITUDE_M, 0))
                    row[COL_ALTITUDE_DELTA_M] = curr_alt - prev_alt
                except (ValueError, TypeError):
                    row[COL_ALTITUDE_DELTA_M] = 0
            row[COL_ALTITUDE_DELTA_FORMATTED] = format_altitude(row[COL_ALTITUDE_DELTA_M])
            
            row[FIELD_MERGE_INFO] = _calculate_merge_info(filtered_data, i)
        
        detailed_grouped[source] = filtered_data
    
    return detailed_grouped

@app.route("/")
def index():
    try:
        logger.info("Processing index page request")
        grouped, all_laps = load_summary_data()
        file_summaries, file_all_laps, file_valid_laps = calculate_file_summaries(grouped)
        fastest_lap, slowest_lap, longest_distance_file, longest_time_file = find_records(all_laps, file_summaries)
        detailed_grouped = load_detailed_data()
        logger.info(f"Successfully processed data for {len(file_summaries)} files")
    except Exception as e:
        logger.error(f"Error processing index page: {e}")
        # Return empty data on error
        grouped, all_laps = defaultdict(list), []
        file_summaries, file_all_laps, file_valid_laps = [], {}, {}
        fastest_lap = slowest_lap = longest_distance_file = longest_time_file = None
        detailed_grouped = defaultdict(list)
    
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

@app.teardown_appcontext
def close_db(error):
    """Close database connection on app context teardown"""
    if error:
        # Sanitize error before logging
        error_msg = str(error)[:200]  # Limit length
        error_msg = error_msg.replace('\n', '\\n').replace('\r', '\\r')
        logger.error(f"App context error: {error_msg}")
    # Connection cleanup handled in finally block of main

if __name__ == "__main__":
    try:
        app.run(debug=DEBUG)
    finally:
        # Ensure database connection is closed on shutdown
        close_db_connection()