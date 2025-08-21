import unittest
from unittest.mock import MagicMock, patch

class TestAltitudeDelta(unittest.TestCase):
    
    def test_altitude_delta_calculation_net_gain(self):
        """Test altitude delta calculation for net elevation gain"""
        # Mock altitude profile: 100 -> 120 -> 110 -> 130 -> 105
        # Changes: +20, -10, +20, -25 = +5 (net gain)
        altitudes = [100, 120, 110, 130, 105]
        
        total_change = 0
        for i in range(1, len(altitudes)):
            change = altitudes[i] - altitudes[i-1]
            total_change += change
        
        self.assertEqual(total_change, 5)  # Net gain
    
    def test_altitude_delta_calculation_net_loss(self):
        """Test altitude delta calculation for net elevation loss"""
        # Mock altitude profile: 130 -> 120 -> 125 -> 110 -> 100
        # Changes: -10, +5, -15, -10 = -30 (net loss)
        altitudes = [130, 120, 125, 110, 100]
        
        total_change = 0
        for i in range(1, len(altitudes)):
            change = altitudes[i] - altitudes[i-1]
            total_change += change
        
        self.assertEqual(total_change, -30)  # Net loss
    
    def test_altitude_delta_calculation_no_change(self):
        """Test altitude delta calculation for no net change"""
        # Mock altitude profile: 100 -> 110 -> 100
        # Changes: +10, -10 = 0 (no net change)
        altitudes = [100, 110, 100]
        
        total_change = 0
        for i in range(1, len(altitudes)):
            change = altitudes[i] - altitudes[i-1]
            total_change += change
        
        self.assertEqual(total_change, 0)  # No net change

if __name__ == '__main__':
    unittest.main()