import re
from flask import Flask, render_template
from pymongo import MongoClient
from collections import defaultdict
from datetime import timedelta

app = Flask(__name__)

MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["RunningTracker"]

@app.template_filter('regex_search')
def regex_search(s, pattern):
    return re.search(pattern, s)

def format_seconds(seconds):
    try:
        return str(timedelta(seconds=int(float(seconds))))
    except Exception:
        return seconds

@app.route("/")
def index():
    # Group summary laps by _source_file
    summary_data = list(db["summary"].find({}, {"_id": 0}))
    grouped = defaultdict(list)
    for row in summary_data:
        source = row.get("_source_file", "Unknown")
        # Format LapTotalTime_s as HH:mm:ss
        if "LapTotalTime_s" in row:
            row["LapTotalTime_formatted"] = format_seconds(row["LapTotalTime_s"])
        grouped[source].append(row)

    # In your Flask app
    detailed_data = list(db["detailed"].find({}, {"_id": 0}))
    detailed_grouped = defaultdict(list)
    for row in detailed_data:
        source = row.get("_source_file", "Unknown")
        detailed_grouped[source].append(row)
    return render_template("index.html", grouped=grouped, detailed=detailed_grouped)
    # In your Flask app
    detailed_data = list(db["detailed"].find({}, {"_id": 0}))
    detailed_grouped = defaultdict(list)
    for row in detailed_data:
        source = row.get("_source_file", "Unknown")
        detailed_grouped[source].append(row)

    return render_template("index.html", grouped=grouped, detailed=detailed_grouped)


if __name__ == "__main__":
    app.run(debug=True)