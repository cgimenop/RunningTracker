import argparse
import xml.etree.ElementTree as ET
import pandas as pd
import os


def calc_pace(total_time_s, distance_m):
    if total_time_s and distance_m and distance_m > 0:
        return (total_time_s / (distance_m / 1000.0)) / 60.0
    return None


def parse_tcx_detailed(tcx_file):
    ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
    tree = ET.parse(tcx_file)
    root = tree.getroot()

    rows = []
    lap_counter = 0

    for lap in root.findall(".//tcx:Lap", ns):
        lap_counter += 1

        lap_start = lap.attrib.get("StartTime")
        lap_total_time = lap.find("tcx:TotalTimeSeconds", ns)
        lap_distance = lap.find("tcx:DistanceMeters", ns)

        total_time_s = float(lap_total_time.text) if lap_total_time is not None else None
        distance_m = float(lap_distance.text) if lap_distance is not None else None
        pace = calc_pace(total_time_s, distance_m)

        for tp in lap.findall(".//tcx:Trackpoint", ns):
            row = {
                "LapNumber": lap_counter,
                "LapStartTime": lap_start,
                "LapTotalTime (s)": total_time_s,
                "LapDistance (m)": distance_m,
                "Pace (min/km)": pace,
            }

            time_elem = tp.find("tcx:Time", ns)
            row["Time"] = time_elem.text if time_elem is not None else None

            pos_elem = tp.find("tcx:Position", ns)
            if pos_elem is not None:
                lat_elem = pos_elem.find("tcx:LatitudeDegrees", ns)
                lon_elem = pos_elem.find("tcx:LongitudeDegrees", ns)
                row["Latitude"] = float(lat_elem.text) if lat_elem is not None else None
                row["Longitude"] = float(lon_elem.text) if lon_elem is not None else None
            else:
                row["Latitude"] = None
                row["Longitude"] = None

            alt_elem = tp.find("tcx:AltitudeMeters", ns)
            row["Altitude (m)"] = float(alt_elem.text) if alt_elem is not None else None

            dist_elem = tp.find("tcx:DistanceMeters", ns)
            row["Distance (m)"] = float(dist_elem.text) if dist_elem is not None else None

            rows.append(row)

    return pd.DataFrame(rows)


def parse_tcx_summary(tcx_file):
    ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
    tree = ET.parse(tcx_file)
    root = tree.getroot()

    rows = []
    lap_counter = 0

    for lap in root.findall(".//tcx:Lap", ns):
        lap_counter += 1

        lap_start = lap.attrib.get("StartTime")
        lap_total_time = lap.find("tcx:TotalTimeSeconds", ns)
        lap_distance = lap.find("tcx:DistanceMeters", ns)

        total_time_s = float(lap_total_time.text) if lap_total_time is not None else None
        distance_m = float(lap_distance.text) if lap_distance is not None else None
        pace = calc_pace(total_time_s, distance_m)

        rows.append({
            "LapNumber": lap_counter,
            "LapStartTime": lap_start,
            "LapTotalTime (s)": total_time_s,
            "LapDistance (m)": distance_m,
            "Pace (min/km)": pace,
        })

    return pd.DataFrame(rows)


def get_first_lap_date(tcx_file):
    ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
    tree = ET.parse(tcx_file)
    root = tree.getroot()
    first_lap = root.find(".//tcx:Lap", ns)
    if first_lap is not None and "StartTime" in first_lap.attrib:
        return first_lap.attrib["StartTime"].split("T")[0]
    return "UnknownDate"

def write_to_excel(df, output_file, sheet_name):
    from openpyxl import load_workbook

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

        # Now open ExcelWriter in append mode (the clean workbook)
        with pd.ExcelWriter(output_file, mode="a", engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def write_to_excel_old(df, output_file, sheet_name):
    from openpyxl import load_workbook

    if not os.path.exists(output_file):
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        book = load_workbook(output_file)
        existing_sheets = book.sheetnames

        match_sheet = None
        for s in existing_sheets:
            if s.lower() == sheet_name.lower():
                match_sheet = s
                break

        if match_sheet:
            del book[match_sheet]
            with pd.ExcelWriter(output_file, mode="a", engine="openpyxl") as writer:
                writer.book = book
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            with pd.ExcelWriter(output_file, mode="a", engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Parse a TCX file (Garmin Training Center XML) into an Excel table.\n"
            "Default export mode is 'both' unless --mode is specified."
        ),
        epilog=(
            "Examples:\n"
            "  Default (both summary & detailed):\n"
            "    python tcx_parser.py workout.tcx\n\n"
            "  Summary only:\n"
            "    python tcx_parser.py workout.tcx --mode summary\n\n"
            "  Detailed only:\n"
            "    python tcx_parser.py workout.tcx --mode detailed\n\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("tcx_file", help="Path to the TCX file to parse.")
    parser.add_argument("--output", help="Path to Excel file. Default: tcx_data.xlsx", default="tcx_data.xlsx")
    parser.add_argument(
        "--mode",
        choices=["detailed", "summary", "both"],
        default="both",  # Default changed here
        help="Export mode: summary, detailed, or both (default)."
    )

    args = parser.parse_args()

    date_str = get_first_lap_date(args.tcx_file)

    if args.mode == "summary":
        df = parse_tcx_summary(args.tcx_file)
        write_to_excel(df, args.output, f"{date_str}_summary")
        print(f"✅ Summary written to sheet '{date_str}_summary' in {args.output}")

    elif args.mode == "detailed":
        df = parse_tcx_detailed(args.tcx_file)
        write_to_excel(df, args.output, f"{date_str}_detail")
        print(f"✅ Detailed written to sheet '{date_str}_detail' in {args.output}")

    else:  # both
        df_summary = parse_tcx_summary(args.tcx_file)
        df_detail = parse_tcx_detailed(args.tcx_file)
        write_to_excel(df_summary, args.output, f"{date_str}_summary")
        write_to_excel(df_detail, args.output, f"{date_str}_detail")
        print(f"✅ Summary & Detailed written to '{args.output}' as '{date_str}_summary' and '{date_str}_detail'")


if __name__ == "__main__":
    main()
