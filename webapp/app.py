import re
import os
from flask import Flask, render_template
from pymongo import MongoClient
from collections import defaultdict
from datetime import timedelta

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

def format_seconds(seconds):
    try:
        return str(timedelta(seconds=int(float(seconds))))
    except (ValueError, TypeError):
        return "00:00:00"

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
        grouped[source].append(row)
        row_copy = row.copy()
        row_copy["_source_file"] = source
        all_laps.append(row_copy)
    return grouped, all_laps

def calculate_file_summaries(grouped):
    file_summaries = []
    file_all_laps = {}
    file_valid_laps = {}
    for source, laps in grouped.items():
        try:
            valid = [l for l in laps if l.get("LapDistance_m") is not None and float(l["LapDistance_m"]) >= 990]
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
            "total_time": total_time,
            "total_time_formatted": total_time_formatted
        })
    return file_summaries, file_all_laps, file_valid_laps

def load_summary_data():
    summary_data = list(db["summary"].find({}, {"_id": 0}))
    grouped = defaultdict(list)
    all_laps = []
    for row in summary_data:
        source = row.get("_source_file", "Unknown")
        if "LapTotalTime_s" in row:
            row["LapTotalTime_formatted"] = format_seconds(row["LapTotalTime_s"])
        grouped[source].append(row)
        row_copy = row.copy()
        row_copy["_source_file"] = source
        all_laps.append(row_copy)
    return grouped, all_laps

def calculate_file_summaries(grouped):
    file_summaries = []
    file_all_laps = {}
    file_valid_laps = {}
    for source, laps in grouped.items():
        try:
            valid = [l for l in laps if l.get("LapDistance_m") is not None and float(l["LapDistance_m"]) >= 990]
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
            "total_time": total_time,
            "total_time_formatted": total_time_formatted
        })
    return file_summaries, file_all_laps, file_valid_laps

def find_records(all_laps, file_summaries):
    try:
        valid_laps = [lap for lap in all_laps if lap.get("LapDistance_m") is not None and float(lap["LapDistance_m"]) >= 990]
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
    detailed_data = list(db["detailed"].find({}, {"_id": 0}))
    detailed_grouped = defaultdict(list)
    for row in detailed_data:
        source = row.get("_source_file", "Unknown")
        detailed_grouped[source].append(row)
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