# Column names that should be merged in detailed tables
MERGE_COLUMNS = ['LapNumber', 'LapStartTime', 'LapTotalTime_s', 'LapDistance_m', 'Pace_min_per_km', '_source_file']

# Human-friendly column name mappings
FRIENDLY_COLUMN_NAMES = {
    'LapNumber': 'Lap',
    'Time': 'Time',
    'LapStartTime': 'Lap Start',
    'LapDistance_m': 'Lap Distance',
    'Distance_m': 'Distance',
    'Altitude_m': 'Altitude',
    'AltitudeDelta_m': 'Altitude Δ',
    'LapTotalTime_s': 'Lap Time',
    'Pace_min_per_km': 'Pace',
    'Latitude_deg': 'Latitude',
    'Longitude_deg': 'Longitude',
    'HeartRate_bpm': 'Heart Rate',
    'Speed_ms': 'Speed',
    'Cadence_rpm': 'Cadence'
}

# Data sampling interval (every Nth row for detailed data)
DETAILED_DATA_SAMPLE_INTERVAL = 60

# Minimum distance for valid laps (in meters)
MIN_VALID_LAP_DISTANCE = 990

# Database collection names
COLLECTION_SUMMARY = "summary"
COLLECTION_DETAILED = "detailed"

# Column names used in database queries and processing
COL_ID = "_id"
COL_SOURCE_FILE = "_source_file"
COL_LAP_TOTAL_TIME_S = "LapTotalTime_s"
COL_LAP_DISTANCE_M = "LapDistance_m"
COL_LAP_NUMBER = "LapNumber"
COL_ALTITUDE_M = "Altitude_m"
COL_ALTITUDE_DELTA_M = "AltitudeDelta_m"
COL_DISTANCE_M = "Distance_m"
COL_TIME = "Time"

# Formatted column names (suffixed versions)
COL_LAP_TOTAL_TIME_FORMATTED = "LapTotalTime_formatted"
COL_LAP_DISTANCE_FORMATTED = "LapDistance_formatted"
COL_ALTITUDE_FORMATTED = "Altitude_formatted"
COL_ALTITUDE_DELTA_FORMATTED = "AltitudeDelta_formatted"
COL_DISTANCE_FORMATTED = "Distance_formatted"

# Summary fields
FIELD_SOURCE = "source"
FIELD_DATE = "date"
FIELD_TOTAL_DISTANCE = "total_distance"
FIELD_TOTAL_DISTANCE_FORMATTED = "total_distance_formatted"
FIELD_TOTAL_TIME = "total_time"
FIELD_TOTAL_TIME_FORMATTED = "total_time_formatted"

# Merge info field
FIELD_MERGE_INFO = "_merge_info"