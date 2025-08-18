import unittest
from unittest.mock import patch, MagicMock, call
from src import trainparser

class DummyArgs:
    def __init__(self, mode, output):
        self.mode = mode
        self.output = output

class TestProcessFile(unittest.TestCase):
    @patch("src.trainparser.get_first_lap_date", return_value="2024-01-01")
    @patch("src.trainparser.write_to_excel")
    @patch("src.trainparser.parse_tcx_summary")
    @patch("src.trainparser.parse_tcx_detailed")
    @patch("src.trainparser.os.path.basename", return_value="file.tcx")
    def test_process_file_summary_no_mongo(
        self, mock_basename, mock_parse_detailed, mock_parse_summary, mock_write, mock_get_date
    ):
        args = DummyArgs(mode="summary", output="out.xlsx")
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
    def test_process_file_detailed_no_mongo(
        self, mock_basename, mock_parse_detailed, mock_parse_summary, mock_write, mock_get_date
    ):
        args = DummyArgs(mode="detailed", output="out.xlsx")
        df_detail = MagicMock()
        mock_parse_detailed.return_value = df_detail

        trainparser.process_file("file.tcx", args, mongo_client=None)

        mock_parse_detailed.assert_called_once_with("file.tcx")
        mock_write.assert_called_once_with(df_detail, "out.xlsx", "2024-01-01_detail")
        mock_parse_summary.assert_not_called()

    @patch("src.trainparser.get_first_lap_date", return_value="2024-01-01")
    @patch("src.trainparser.write_to_excel")
    @patch("src.trainparser.parse_tcx_summary")
    @patch("src.trainparser.parse_tcx_detailed")
    @patch("src.trainparser.os.path.basename", return_value="file.tcx")
    def test_process_file_both_no_mongo(
        self, mock_basename, mock_parse_detailed, mock_parse_summary, mock_write, mock_get_date
    ):
        args = DummyArgs(mode="both", output="out.xlsx")
        df_summary = MagicMock()
        df_detail = MagicMock()
        mock_parse_summary.return_value = df_summary
        mock_parse_detailed.return_value = df_detail

        trainparser.process_file("file.tcx", args, mongo_client=None)

        mock_parse_summary.assert_called_once_with("file.tcx")
        mock_parse_detailed.assert_called_once_with("file.tcx")
        self.assertEqual(mock_write.call_count, 2)
        mock_write.assert_has_calls([
            call(df_summary, "out.xlsx", "2024-01-01_summary"),
            call(df_detail, "out.xlsx", "2024-01-01_detail"),
        ], any_order=True)

    @patch("src.trainparser.get_first_lap_date", return_value="2024-01-01")
    @patch("src.trainparser.write_to_excel")
    @patch("src.trainparser.parse_tcx_summary")
    @patch("src.trainparser.parse_tcx_detailed")
    @patch("src.trainparser.os.path.basename", return_value="file.tcx")
    def test_process_file_summary_with_mongo(
        self, mock_basename, mock_parse_detailed, mock_parse_summary, mock_write, mock_get_date
    ):
        args = DummyArgs(mode="summary", output="out.xlsx")
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
        # Check that _source_file is set
        self.assertEqual(df_summary.__setitem__.call_args[0][0], "_source_file")

    @patch("src.trainparser.get_first_lap_date", return_value="2024-01-01")
    @patch("src.trainparser.write_to_excel")
    @patch("src.trainparser.parse_tcx_summary")
    @patch("src.trainparser.parse_tcx_detailed")
    @patch("src.trainparser.os.path.basename", return_value="file.tcx")
    def test_process_file_detailed_with_mongo(
        self, mock_basename, mock_parse_detailed, mock_parse_summary, mock_write, mock_get_date
    ):
        args = DummyArgs(mode="detailed", output="out.xlsx")
        df_detail = MagicMock()
        df_detail.to_dict.return_value = [{"LapStartTime": "2024-01-01T10:00:00Z", "LapNumber": 1, "Time": "2024-01-01T10:00:01Z", "_source_file": "file.tcx"}]
        mock_parse_detailed.return_value = df_detail

        mock_collection = MagicMock()
        mock_db = {"detailed": mock_collection}
        mock_mongo_client = MagicMock()
        mock_mongo_client.__getitem__.return_value = mock_db

        trainparser.process_file("file.tcx", args, mongo_client=mock_mongo_client)

        mock_parse_detailed.assert_called_once_with("file.tcx")
        mock_write.assert_called_once_with(df_detail, "out.xlsx", "2024-01-01_detail")
        mock_collection.replace_one.assert_called()
        self.assertEqual(df_detail.__setitem__.call_args[0][0], "_source_file")

if __name__ == "__main__":
    unittest.main()