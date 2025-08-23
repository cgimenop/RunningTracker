"""
Tests for const.py module
"""
import pytest


class TestConstants:
    """Test constants module"""
    
    def test_merge_columns_exists(self):
        """Test MERGE_COLUMNS constant exists and is list"""
        from webapp.const import MERGE_COLUMNS
        assert isinstance(MERGE_COLUMNS, list)
        assert len(MERGE_COLUMNS) > 0
        assert 'LapNumber' in MERGE_COLUMNS
    
    def test_friendly_column_names_exists(self):
        """Test FRIENDLY_COLUMN_NAMES constant exists and is dict"""
        from webapp.const import FRIENDLY_COLUMN_NAMES
        assert isinstance(FRIENDLY_COLUMN_NAMES, dict)
        assert len(FRIENDLY_COLUMN_NAMES) > 0
        assert 'LapNumber' in FRIENDLY_COLUMN_NAMES
        assert FRIENDLY_COLUMN_NAMES['LapNumber'] == 'Lap'
    
    def test_detailed_data_sample_interval(self):
        """Test DETAILED_DATA_SAMPLE_INTERVAL constant"""
        from webapp.const import DETAILED_DATA_SAMPLE_INTERVAL
        assert isinstance(DETAILED_DATA_SAMPLE_INTERVAL, int)
        assert DETAILED_DATA_SAMPLE_INTERVAL > 0
    
    def test_min_valid_lap_distance(self):
        """Test MIN_VALID_LAP_DISTANCE constant"""
        from webapp.const import MIN_VALID_LAP_DISTANCE
        assert isinstance(MIN_VALID_LAP_DISTANCE, int)
        assert MIN_VALID_LAP_DISTANCE > 0
    
    def test_collection_names(self):
        """Test database collection name constants"""
        from webapp.const import COLLECTION_SUMMARY, COLLECTION_DETAILED
        assert isinstance(COLLECTION_SUMMARY, str)
        assert isinstance(COLLECTION_DETAILED, str)
        assert COLLECTION_SUMMARY == "summary"
        assert COLLECTION_DETAILED == "detailed"
    
    def test_column_names(self):
        """Test column name constants"""
        from webapp.const import (COL_ID, COL_SOURCE_FILE, COL_LAP_TOTAL_TIME_S, 
                                 COL_LAP_DISTANCE_M, COL_LAP_NUMBER)
        assert isinstance(COL_ID, str)
        assert isinstance(COL_SOURCE_FILE, str)
        assert isinstance(COL_LAP_TOTAL_TIME_S, str)
        assert isinstance(COL_LAP_DISTANCE_M, str)
        assert isinstance(COL_LAP_NUMBER, str)
    
    def test_formatted_column_names(self):
        """Test formatted column name constants"""
        from webapp.const import (COL_LAP_TOTAL_TIME_FORMATTED, COL_LAP_DISTANCE_FORMATTED,
                                 COL_ALTITUDE_FORMATTED)
        assert isinstance(COL_LAP_TOTAL_TIME_FORMATTED, str)
        assert isinstance(COL_LAP_DISTANCE_FORMATTED, str)
        assert isinstance(COL_ALTITUDE_FORMATTED, str)
    
    def test_field_names(self):
        """Test field name constants"""
        from webapp.const import (FIELD_SOURCE, FIELD_DATE, FIELD_TOTAL_DISTANCE,
                                 FIELD_TOTAL_TIME, FIELD_MERGE_INFO)
        assert isinstance(FIELD_SOURCE, str)
        assert isinstance(FIELD_DATE, str)
        assert isinstance(FIELD_TOTAL_DISTANCE, str)
        assert isinstance(FIELD_TOTAL_TIME, str)
        assert isinstance(FIELD_MERGE_INFO, str)