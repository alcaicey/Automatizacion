"""Generate a simple PNG diagram from SQLAlchemy models."""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)
from src.models import db  # type: ignore  # ensure models are imported

OUTPUT = os.path.join(BASE_DIR, "src", "static", "schema_diagram.png")
FONT_SIZE = 14
PADDING = 10


def collect_schema() -> list[str]:
    lines = []
    metadata = db.metadata
    for table in metadata.sorted_tables:
        cols = ", ".join(c.name for c in table.columns)
        lines.append(f"{table.name}: {cols}")
    return lines


def render_image(lines: list[str], path: str) -> None:
    font = ImageFont.load_default()
    width = max(font.getlength(line) for line in lines) + PADDING * 2
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 4
    height = line_height * len(lines) + PADDING * 2
    img = Image.new("RGB", (int(width), int(height)), "white")
    draw = ImageDraw.Draw(img)
    y = PADDING
    for line in lines:
        draw.text((PADDING, y), line, fill="black", font=font)
        y += line_height
    img.save(path)


def main() -> None:
    lines = collect_schema()
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    render_image(lines, OUTPUT)
    print(f"Diagrama generado en {OUTPUT}")


if __name__ == "__main__":
    main()
