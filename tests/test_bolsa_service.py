import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.scripts import bolsa_service


def test_filter_stocks(monkeypatch):
    sample = {
        "data": [
            {"NEMO": "AAA", "VALUE": 1},
            {"NEMO": "BBB", "VALUE": 2},
        ],
        "timestamp": "now",
        "source_file": "test.json",
    }
    monkeypatch.setattr(bolsa_service, "get_latest_data", lambda: sample)
    result = bolsa_service.filter_stocks(["BBB"])
    assert result["count"] == 1
    assert result["data"][0]["NEMO"] == "BBB"


def test_filter_stocks_all(monkeypatch):
    sample = {
        "data": [
            {"NEMO": "AAA"},
            {"NEMO": "BBB"},
        ],
        "timestamp": "now",
        "source_file": "test.json",
    }
    monkeypatch.setattr(bolsa_service, "get_latest_data", lambda: sample)
    result = bolsa_service.filter_stocks([])
    assert result["count"] == len(sample["data"])

