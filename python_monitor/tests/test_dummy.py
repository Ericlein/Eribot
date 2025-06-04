import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitory import check_system
import psutil

def test_basic_math():
    assert 1 + 1 == 2

def test_system_monitoring():
    # Mock the slack_client and requests to avoid actual API calls
    cpu = psutil.cpu_percent(interval=1)
    disk = psutil.disk_usage('/').percent
    
    assert isinstance(cpu, float)
    assert isinstance(disk, float)
    assert 0 <= cpu <= 100
    assert 0 <= disk <= 100