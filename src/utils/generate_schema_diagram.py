from sqlalchemy_schemadisplay import create_schema_graph
from src.models import db
import os


def generate_diagram():
    graph = create_schema_graph(
        metadata=db.metadata,
        show_datatypes=True,
        show_indexes=False,
        rankdir="LR",
        concentrate=False,
    )
    base_dir = os.path.dirname(os.path.dirname(__file__))
    output_path = os.path.join(base_dir, "static", "schema_diagram.png")
    graph.write_png(output_path)
    print(f"Diagrama generado en: {output_path}")


if __name__ == "__main__":
    generate_diagram()
