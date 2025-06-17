from flask import Blueprint, jsonify, render_template
import subprocess
import logging

logger = logging.getLogger(__name__)
architecture_bp = Blueprint("architecture", __name__, template_folder="../templates")

@architecture_bp.route("/architecture")
def architecture_page():
    return render_template("architecture.html")

@architecture_bp.route("/api/regenerate-schema-diagram", methods=["POST"])
def regenerate_schema_diagram():
    try:
        result = subprocess.run(
            ['python', 'src/utils/generate_schema_diagram.py'],
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        logger.info(f"Diagrama de esquema regenerado: {result.stdout}")
        return jsonify({'success': True, 'output': result.stdout})
    except subprocess.CalledProcessError as e:
        error_message = f"Error al ejecutar el script: {e.stderr}"
        logger.error(error_message)
        return jsonify({'success': False, 'error': error_message}), 500
    except FileNotFoundError:
        error_message = "No se encontró el script 'generate_schema_diagram.py'."
        logger.error(error_message)
        return jsonify({'success': False, 'error': error_message}), 500