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
    'LapTotalTime_s': 'Lap Time',
    'Pace_min_per_km': 'Pace',
    'Latitude_deg': 'Latitude',
    'Longitude_deg': 'Longitude',
    'HeartRate_bpm': 'Heart Rate',
    'Speed_ms': 'Speed',
    'Cadence_rpm': 'Cadence'
}

# Data sampling interval (every Nth row for detailed data)
DETAILED_DATA_SAMPLE_INTERVAL = 10

# Minimum distance for valid laps (in meters)
MIN_VALID_LAP_DISTANCE = 990