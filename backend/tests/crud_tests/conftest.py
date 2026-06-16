import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest
from tester_db_setup import get_test_session

@pytest.fixture(scope="module")
def session():
    s = get_test_session()
    yield s
    s.close()
