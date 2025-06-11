import json
from pathlib import Path
from src.scripts.har_analyzer import analyze_har_and_extract_data


def test_har_analyzer_extracts_json(tmp_path):
    har = {
        "log": {
            "entries": [
                {
                    "request": {"url": "https://api/data", "method": "GET", "headers": []},
                    "response": {
                        "status": 200,
                        "content": {"mimeType": "application/json", "size": 2, "text": "{\"foo\": \"bar\"}"},
                        "headers": [],
                    },
                }
            ]
        }
    }
    har_path = tmp_path / "capture.har"
    har_path.write_text(json.dumps(har), encoding="utf-8")
    out_data = tmp_path / "data.json"
    out_summary = tmp_path / "summary.json"

    analyze_har_and_extract_data(
        str(har_path),
        ["https://api/data"],
        [],
        str(out_data),
        str(out_summary),
    )

    assert out_data.exists()
    assert out_summary.exists()
    parsed = json.loads(out_data.read_text())
    assert parsed["foo"] == "bar"
