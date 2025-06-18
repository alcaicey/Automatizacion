import json
from src.utils import history_view


def test_load_and_compare(tmp_path, monkeypatch):
    logs_dir = tmp_path
    # file1
    f1 = logs_dir / 'acciones-precios-plus_20240101_120000.json'
    f1.write_text(json.dumps([
        {"symbol": "AAA", "price": 1, "variation": 0.0, "timestamp": "2024-01-01T12:00:00"},
        {"symbol": "BBB", "price": 2, "variation": 0.1, "timestamp": "2024-01-01T12:00:00"}
    ]), encoding='utf-8')
    # file2
    f2 = logs_dir / 'acciones-precios-plus_20240102_120000.json'
    f2.write_text(json.dumps([
        {"symbol": "AAA", "price": 1.5, "variation": 0.2, "timestamp": "2024-01-02T12:00:00"},
        {"symbol": "CCC", "price": 3, "variation": 0.0, "timestamp": "2024-01-02T12:00:00"}
    ]), encoding='utf-8')

    history = history_view.load_history(str(logs_dir))
    assert len(history) == 2
    assert history[0]['total'] == 2

    cmp = history_view.compare_latest(str(logs_dir))
    assert len(cmp['new']) == 1
    assert cmp['new'][0]['symbol'] == 'CCC'
    assert len(cmp['removed']) == 1
    assert cmp['removed'][0]['symbol'] == 'BBB'
    assert len(cmp['changes']) == 1
    assert cmp['changes'][0]['symbol'] == 'AAA'

