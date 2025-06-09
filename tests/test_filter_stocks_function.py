import pytest

from src.scripts import bolsa_service


def test_filter_stocks_with_alternative_keys(monkeypatch):
    data = {
        "data": [
            {"NEMO": "AAA", "price": 1},
            {"symbol": "BBB", "price": 2},
            {"symbol": 123},
            "bad"
        ],
        "timestamp": "01/01/2024 00:00:00",
        "source_file": "dummy.json",
    }

    monkeypatch.setattr(bolsa_service, "get_latest_data", lambda: data)

    result = bolsa_service.filter_stocks(["AAA", "BBB"])

    assert "error" not in result
    assert result["count"] == 2
    symbols = [s.get("NEMO") or s.get("symbol") for s in result["data"]]
    assert symbols == ["AAA", "BBB"]
