import argparse
import json
from typing import Any

from src import history_view


def main() -> None:
    parser = argparse.ArgumentParser(description="Comparar últimos archivos de precios")
    parser.add_argument("--dir", dest="directory", default=None, help="Directorio con archivos JSON")
    parser.add_argument("--output", dest="output", default="diferencias.json", help="Archivo de salida")
    args = parser.parse_args()

    cmp = history_view.compare_latest(args.directory)
    if not cmp:
        print("No se encontraron suficientes archivos para comparar")
        return

    added = [i["symbol"] for i in cmp["new"]]
    removed = [i["symbol"] for i in cmp["removed"]]
    changed = [c["symbol"] for c in cmp["changes"]]

    print("Agregados:", ", ".join(added) if added else "Ninguno")
    print("Eliminados:", ", ".join(removed) if removed else "Ninguno")
    print("Modificados:", ", ".join(changed) if changed else "Ninguno")

    diffs: list[dict[str, Any]] = []
    for c in cmp["changes"]:
        diffs.append({
            "symbol": c["symbol"],
            "precio_anterior": c["old"]["price"],
            "precio_nuevo": c["new"]["price"],
            "diferencia": c["abs_diff"],
            "porcentaje": c["pct_diff"],
        })

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(diffs, f, indent=2, ensure_ascii=False)

    print(f"Total de acciones comparadas: {cmp['total_compared']}")
    print(f"Cambios detectados: {cmp['change_count']}")
    print(f"Errores de datos inválidos: {len(cmp['errors'])}")


if __name__ == "__main__":
    main()

