import argparse
from defusedxml import ElementTree as ET
import pandas as pd
import os
from openpyxl import load_workbook
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


def calc_pace(total_time_s, distance_m):
    if total_time_s and distance_m and distance_m > 0 and total_time_s > 0:
        return (total_time_s / (distance_m / 1000.0)) / 60.0
    return None


def parse_tcx_detailed(tcx_file):
    try:
        ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
        tree = ET.parse(tcx_file)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML file: {e}")

    rows = []
    lap_counter = 0

    for lap in root.findall(".//tcx:Lap", ns):
        lap_counter += 1

        lap_start = lap.attrib.get("StartTime")
        # amazonq-ignore-next-line
        lap_total_time = lap.find("tcx:TotalTimeSeconds", ns)
        # amazonq-ignore-next-line
        lap_distance = lap.find("tcx:DistanceMeters", ns)

        try:
            total_time_s = float(lap_total_time.text) if lap_total_time is not None and lap_total_time.text else None
            distance_m = float(lap_distance.text) if lap_distance is not None and lap_distance.text else None
        except ValueError:
            total_time_s = distance_m = None
        pace = calc_pace(total_time_s, distance_m)

        for tp in lap.findall(".//tcx:Trackpoint", ns):
            row = {
                "LapNumber": lap_counter,
                "LapStartTime": lap_start,
                "LapTotalTime_s": total_time_s,
                "LapDistance_m": distance_m,
                "Pace_min_per_km": pace,
                "Time": None,
                "Latitude": None,
                "Longitude": None,
                "Altitude_m": None,
                "Distance_m": None,
            }

            # amazonq-ignore-next-line
            time_elem = tp.find("tcx:Time", ns)
            if time_elem is not None:
                row["Time"] = time_elem.text

            # amazonq-ignore-next-line
            pos_elem = tp.find("tcx:Position", ns)
            if pos_elem is not None:
                # amazonq-ignore-next-line
                lat_elem = pos_elem.find("tcx:LatitudeDegrees", ns)
                # amazonq-ignore-next-line
                lon_elem = pos_elem.find("tcx:LongitudeDegrees", ns)
                try:
                    row["Latitude"] = float(lat_elem.text) if lat_elem is not None and lat_elem.text else None
                    row["Longitude"] = float(lon_elem.text) if lon_elem is not None and lon_elem.text else None
                except ValueError:
                    row["Latitude"] = row["Longitude"] = None

            # amazonq-ignore-next-line
            alt_elem = tp.find("tcx:AltitudeMeters", ns)
            if alt_elem is not None and alt_elem.text:
                try:
                    row["Altitude_m"] = float(alt_elem.text)
                except ValueError:
                    row["Altitude_m"] = None

            # amazonq-ignore-next-line
            dist_elem = tp.find("tcx:DistanceMeters", ns)
            if dist_elem is not None and dist_elem.text:
                try:
                    row["Distance_m"] = float(dist_elem.text)
                except ValueError:
                    row["Distance_m"] = None

            rows.append(row)

    return pd.DataFrame(rows)


def parse_tcx_summary(tcx_file):
    try:
        ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
        tree = ET.parse(tcx_file)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML file: {e}")

    rows = []
    lap_counter = 0

    for lap in root.findall(".//tcx:Lap", ns):
        lap_counter += 1

        lap_start = lap.attrib.get("StartTime")
        # amazonq-ignore-next-line
        lap_total_time = lap.find("tcx:TotalTimeSeconds", ns)
        # amazonq-ignore-next-line
        lap_distance = lap.find("tcx:DistanceMeters", ns)

        try:
            total_time_s = float(lap_total_time.text) if lap_total_time is not None and lap_total_time.text else None
            distance_m = float(lap_distance.text) if lap_distance is not None and lap_distance.text else None
        except ValueError:
            total_time_s = distance_m = None
        pace = calc_pace(total_time_s, distance_m)

        rows.append({
            "LapNumber": lap_counter,
            "LapStartTime": lap_start,
            "LapTotalTime_s": total_time_s,
            "LapDistance_m": distance_m,
            "Pace_min_per_km": pace,
        })

    return pd.DataFrame(rows)


def get_first_lap_date(tcx_file):
    try:
        ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
        tree = ET.parse(tcx_file)
        root = tree.getroot()
        # amazonq-ignore-next-line
        first_lap = root.find(".//tcx:Lap", ns)
        if first_lap is not None and "StartTime" in first_lap.attrib:
            return first_lap.attrib["StartTime"].split("T")[0]
    except ET.ParseError:
        pass
    return "UnknownDate"


def write_to_excel(df, output_file, sheet_name):
    if not os.path.exists(output_file):
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        book = load_workbook(output_file)
        existing_sheets = book.sheetnames

        # Remove the sheet if it exists (case-insensitive)
        match_sheet = None
        for s in existing_sheets:
            if s.lower() == sheet_name.lower():
                match_sheet = s
                break

        if match_sheet:
            del book[match_sheet]
            book.save(output_file)  # Save immediately after deletion!

        with pd.ExcelWriter(output_file, mode="a", engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def push_to_mongo(df, collection, unique_keys):
    """
    Upsert each row in df to the mongo collection.
    unique_keys: list of column names for the unique query filter.
    """
    records = df.to_dict(orient="records")
    for rec in records:
        query = {k: rec.get(k) for k in unique_keys}
        # amazonq-ignore-next-line
        collection.replace_one(query, rec, upsert=True)


def process_file(tcx_file, args, mongo_client=None):
    print(f"Processing {tcx_file}")

    date_str = get_first_lap_date(tcx_file)

    dfs_to_write = []
    dfs_to_mongo = []

    if args.mode in ("summary", "both"):
        df_summary = parse_tcx_summary(tcx_file)
        sheet_summary = f"{date_str}_summary"
        dfs_to_write.append((df_summary, sheet_summary))
        if mongo_client:
            dfs_to_mongo.append(("summary", df_summary))

    if args.mode in ("detailed", "both"):
        df_detail = parse_tcx_detailed(tcx_file)
        sheet_detail = f"{date_str}_detail"
        dfs_to_write.append((df_detail, sheet_detail))
        if mongo_client:
            dfs_to_mongo.append(("detailed", df_detail))

    # Write Excel sheets
    for df, sheet_name in dfs_to_write:
        write_to_excel(df, args.output, sheet_name)

    print(f"✅ Data written to Excel file '{args.output}'")

    # Push to MongoDB
    if mongo_client:
        db = mongo_client["RunningTracker"]
        for mode_name, df in dfs_to_mongo:
            collection = db[mode_name]

            # Determine unique keys for upsert based on mode
            if mode_name == "summary":
                unique_keys = ["LapStartTime", "LapNumber", "LapTotalTime_s", "LapDistance_m", "Pace_min_per_km"]
            else:  # detailed
                unique_keys = ["LapStartTime", "LapNumber", "Time"]

            # Add filename to each record for uniqueness and traceability
            filename = os.path.basename(tcx_file)
            if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
                filename = 'sanitized_file.tcx'
            df["_source_file"] = filename

            # Convert DataFrame to dicts with updated keys
            records = df.to_dict(orient="records")

            for rec in records:
                # Compose the filter query only with keys present in rec
                query = {k: rec.get(k) for k in unique_keys if rec.get(k) is not None}
                # Include source file in query to avoid conflicts across files
                query["_source_file"] = rec["_source_file"]
                # amazonq-ignore-next-line
                collection.replace_one(query, rec, upsert=True)

        print("✅ Data pushed to MongoDB")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Parse TCX file(s) (Garmin Training Center XML) into an Excel table and optionally MongoDB.\n"
            "Default export mode is 'both' unless --mode is specified."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("input_path", help="Path to TCX file or folder containing TCX files.")
    parser.add_argument("--output", help="Path to Excel file. Default: tcx_data.xlsx", default="tcx_data.xlsx")
    parser.add_argument(
        "--mode",
        choices=["detailed", "summary", "both"],
        default="both",
        help="Export mode: summary, detailed, or both (default).",
    )
    parser.add_argument(
        "--mongo",
        action="store_true",
        help="Push the parsed data to MongoDB (requires 'pymongo'). MongoDB must be reachable at default localhost:27017.",
    )
    parser.add_argument(
        "--mongo-uri",
        default="mongodb://localhost:27017",
        help="MongoDB connection URI (default: mongodb://localhost:27017).",
    )

    args = parser.parse_args()

    # Validate input path
    if not os.path.exists(args.input_path):
        print(f"Input path '{args.input_path}' does not exist.")
        return

    # Setup MongoDB client if requested
    mongo_client = None
    if args.mongo:
        try:
            # amazonq-ignore-next-line
            mongo_client = MongoClient(args.mongo_uri, serverSelectionTimeoutMS=5000)
            # Trigger a server selection to verify connection
            mongo_client.server_info()
            print("Connected to MongoDB")
        except ServerSelectionTimeoutError:
            print("ERROR: Could not connect to MongoDB. Please check your connection.")
            return

    try:
        # Determine if input is file or folder
        if os.path.isfile(args.input_path):
            files = [args.input_path]
        else:
            # Folder - get all .tcx files
            try:
                files = [
                    os.path.join(args.input_path, f)
                    for f in os.listdir(args.input_path)
                    if f.lower().endswith(".tcx") and os.path.isfile(os.path.join(args.input_path, f))
                ]
                if not files:
                    print(f"No .tcx files found in folder '{args.input_path}'.")
                    return
            except (PermissionError, OSError) as e:
                print(f"ERROR: Cannot access directory '{args.input_path}': {e}")
                return

        for f in files:
            process_file(f, args, mongo_client)
    finally:
        if mongo_client:
            mongo_client.close()


if __name__ == "__main__":
    main()
