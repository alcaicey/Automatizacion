"""
Genera un diagrama PNG de la base de datos a partir de los modelos SQLAlchemy.

Usa sqlalchemy_schemadisplay si está disponible; si no, usa PIL como fallback.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)

from src.models import db  # Asegura acceso a los modelos

OUTPUT_PATH = os.path.join(BASE_DIR, "src", "static", "schema_diagram.png")
FALLBACK_FONT_SIZE = 14
FALLBACK_PADDING = 10


def generate_with_sqlalchemy_schemadisplay():
    from sqlalchemy_schemadisplay import create_schema_graph

    graph = create_schema_graph(
        metadata=db.metadata,
        show_datatypes=True,
        show_indexes=False,
        rankdir="LR",
        concentrate=False,
    )
    graph.write_png(OUTPUT_PATH)
    print(f"✅ Diagrama generado con sqlalchemy_schemadisplay en {OUTPUT_PATH}")


def generate_with_pil_fallback():
    from PIL import Image, ImageDraw, ImageFont

    lines = []
    for table in db.metadata.sorted_tables:
        cols = ", ".join(c.name for c in table.columns)
        lines.append(f"{table.name}: {cols}")

    font = ImageFont.load_default()
    width = max(font.getlength(line) for line in lines) + FALLBACK_PADDING * 2
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 4
    height = line_height * len(lines) + FALLBACK_PADDING * 2

    img = Image.new("RGB", (int(width), int(height)), "white")
    draw = ImageDraw.Draw(img)
    y = FALLBACK_PADDING
    for line in lines:
        draw.text((FALLBACK_PADDING, y), line, fill="black", font=font)
        y += line_height

    img.save(OUTPUT_PATH)
    print(f"⚠️ Diagrama generado con fallback PIL en {OUTPUT_PATH}")


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    try:
        generate_with_sqlalchemy_schemadisplay()
    except ImportError:
        print("❌ sqlalchemy_schemadisplay no disponible. Usando fallback...")
        generate_with_pil_fallback()


if __name__ == "__main__":
    main()