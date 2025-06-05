import pytest
import requests
import time
from unittest.mock import patch

@pytest.mark.integration
class TestIntegration:
    """Integration tests that require external services"""
    
    @pytest.mark.integration
    def test_remediator_service_connection(self):
        """Test connection to C# remediator service"""
        try:
            response = requests.get("http://localhost:5001/health", timeout=5)
            assert response.status_code in [200, 404]  # 404 is OK if health endpoint doesn't exist
        except requests.exceptions.ConnectionError:
            pytest.skip("C# remediator service not running")
    
    @pytest.mark.integration
    @patch('monitor.send_slack_message')
    def test_end_to_end_monitoring(self, mock_slack):
        """Test complete monitoring flow"""
        from monitor import check_system
        
        # Run system check
        result = check_system()
        
        # First verify we got a tuple or list
        assert isinstance(result, (tuple, list))
        
        # Check if we get 2 or 3 values
        if len(result) == 2:
            cpu, memory = result
            assert isinstance(cpu, float)
            assert isinstance(memory, float)
            assert 0 <= cpu <= 100
            assert 0 <= memory <= 100
        else:
            cpu, disk, memory = result
            assert isinstance(cpu, float)
            assert isinstance(disk, float)
            assert isinstance(memory, float)
            assert 0 <= cpu <= 100
            assert 0 <= disk <= 100
            assert 0 <= memory <= 100
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_monitoring_loop(self):
        """Test monitoring loop for a short duration"""
        from monitor import check_system

        # Run monitoring for 3 iterations
        results = []
        for _ in range(3):
            result = check_system()
            results.append(result)
            time.sleep(1)

        # Verify we got 3 results
        assert len(results) == 3

        # Verify all results are valid
        for result in results:
            if len(result) == 2:
                cpu, memory = result
                assert 0 <= cpu <= 100
                assert 0 <= memory <= 100
            else:
                cpu, disk, memory = result
                assert 0 <= cpu <= 100
                assert 0 <= disk <= 100
                assert 0 <= memory <= 100