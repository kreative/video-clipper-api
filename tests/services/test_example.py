import os
import sys

from src.app import app

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_service_example() -> None:
    with app.app_context():
        pass
