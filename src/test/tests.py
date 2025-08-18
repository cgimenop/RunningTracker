import unittest
from unittest.mock import patch, MagicMock, call
from src import trainparser

class TestArgs:
    def __init__(self, mode="both", output="test.xlsx", mongo=False, mongo_uri="mongodb://localhost:27017"):
        self.mode = mode
        self.output = output
        self.mongo = mongo
        self.mongo_uri = mongo_uri
        self.input_path = "test.tcx"

class TestCalcPace(unittest.TestCase):
    def test_calc_pace_valid_inputs(self):
        result = trainparser.calc_pace(600, 1000)  # 10 minutes for 1km
        self.assertEqual(result, 10.0)
    
    def test_calc_pace_zero_distance(self):
        result = trainparser.calc_pace(600, 0)
        self.assertIsNone(result)
    
    def test_calc_pace_none_inputs(self):
        result = trainparser.calc_pace(None, 1000)
        self.assertIsNone(result)

class TestGetFirstLapDate(unittest.TestCase):
    @patch('src.trainparser.ET.parse')
    def test_get_first_lap_date_valid_xml(self, mock_parse):
        mock_tree = MagicMock()
        mock_root = MagicMock()
        mock_lap = MagicMock()
        mock_lap.attrib = {"StartTime": "2024-01-01T10:00:00Z"}
        
        mock_parse.return_value = mock_tree
        mock_tree.getroot.return_value = mock_root
        mock_root.find.return_value = mock_lap
        
        result = trainparser.get_first_lap_date("test.tcx")
        self.assertEqual(result, "2024-01-01")
    
    @patch('src.trainparser.ET.parse')
    def test_get_first_lap_date_parse_error(self, mock_parse):
        mock_parse.side_effect = trainparser.ET.ParseError("Invalid XML")
        result = trainparser.get_first_lap_date("invalid.tcx")
        self.assertEqual(result, "UnknownDate")

class TestWriteToExcel(unittest.TestCase):
    @patch('src.trainparser.os.path.exists')
    @patch('src.trainparser.pd.ExcelWriter')
    def test_write_to_excel_new_file(self, mock_writer, mock_exists):
        mock_exists.return_value = False
        mock_df = MagicMock()
        
        trainparser.write_to_excel(mock_df, "test.xlsx", "sheet1")
        
        mock_writer.assert_called_once_with("test.xlsx", engine="openpyxl")

class TestPushToMongo(unittest.TestCase):
    def test_push_to_mongo(self):
        mock_df = MagicMock()
        mock_df.to_dict.return_value = [
            {"key1": "value1", "key2": "value2"},
            {"key1": "value3", "key2": "value4"}
        ]
        mock_collection = MagicMock()
        unique_keys = ["key1"]
        
        trainparser.push_to_mongo(mock_df, mock_collection, unique_keys)
        
        self.assertEqual(mock_collection.replace_one.call_count, 2)

class TestProcessFile(unittest.TestCase):
    @patch("src.trainparser.get_first_lap_date", return_value="2024-01-01")
    @patch("src.trainparser.write_to_excel")
    @patch("src.trainparser.parse_tcx_summary")
    @patch("src.trainparser.parse_tcx_detailed")
    @patch("src.trainparser.os.path.basename", return_value="file.tcx")
    def test_process_file_summary_no_mongo(
        self, mock_basename, mock_parse_detailed, mock_parse_summary, mock_write, mock_get_date
    ):
        args = TestArgs(mode="summary", output="out.xlsx")
        df_summary = MagicMock()
        mock_parse_summary.return_value = df_summary

        trainparser.process_file("file.tcx", args, mongo_client=None)

        mock_parse_summary.assert_called_once_with("file.tcx")
        mock_write.assert_called_once_with(df_summary, "out.xlsx", "2024-01-01_summary")
        mock_parse_detailed.assert_not_called()

    @patch("src.trainparser.get_first_lap_date", return_value="2024-01-01")
    @patch("src.trainparser.write_to_excel")
    @patch("src.trainparser.parse_tcx_summary")
    @patch("src.trainparser.parse_tcx_detailed")
    @patch("src.trainparser.os.path.basename", return_value="file.tcx")
    def test_process_file_both_no_mongo(
        self, mock_basename, mock_parse_detailed, mock_parse_summary, mock_write, mock_get_date
    ):
        args = TestArgs(mode="both", output="out.xlsx")
        df_summary = MagicMock()
        df_detail = MagicMock()
        mock_parse_summary.return_value = df_summary
        mock_parse_detailed.return_value = df_detail

        trainparser.process_file("file.tcx", args, mongo_client=None)

        mock_parse_summary.assert_called_once_with("file.tcx")
        mock_parse_detailed.assert_called_once_with("file.tcx")
        self.assertEqual(mock_write.call_count, 2)

    @patch("src.trainparser.get_first_lap_date", return_value="2024-01-01")
    @patch("src.trainparser.write_to_excel")
    @patch("src.trainparser.parse_tcx_summary")
    @patch("src.trainparser.parse_tcx_detailed")
    @patch("src.trainparser.os.path.basename", return_value="file.tcx")
    def test_process_file_with_mongo(
        self, mock_basename, mock_parse_detailed, mock_parse_summary, mock_write, mock_get_date
    ):
        args = TestArgs(mode="summary", output="out.xlsx")
        df_summary = MagicMock()
        df_summary.to_dict.return_value = [{"LapStartTime": "2024-01-01T10:00:00Z", "LapNumber": 1, "LapTotalTime_s": 100, "LapDistance_m": 1000, "Pace_min_per_km": 6.0, "_source_file": "file.tcx"}]
        mock_parse_summary.return_value = df_summary

        mock_collection = MagicMock()
        mock_db = {"summary": mock_collection}
        mock_mongo_client = MagicMock()
        mock_mongo_client.__getitem__.return_value = mock_db

        trainparser.process_file("file.tcx", args, mongo_client=mock_mongo_client)

        mock_parse_summary.assert_called_once_with("file.tcx")
        mock_write.assert_called_once_with(df_summary, "out.xlsx", "2024-01-01_summary")
        mock_collection.replace_one.assert_called()

class TestMain(unittest.TestCase):
    @patch('src.trainparser.argparse.ArgumentParser')
    @patch('src.trainparser.os.path.exists')
    @patch('src.trainparser.os.path.isfile')
    @patch('src.trainparser.process_file')
    def test_main_single_file(self, mock_process, mock_isfile, mock_exists, mock_parser):
        mock_args = TestArgs(mode="both", output="test.xlsx")
        mock_parser_instance = MagicMock()
        mock_parser_instance.parse_args.return_value = mock_args
        mock_parser.return_value = mock_parser_instance
        
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        trainparser.main()
        
        mock_process.assert_called_once_with("test.tcx", mock_args, None)

if __name__ == "__main__":
    unittest.main()