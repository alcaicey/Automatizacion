from flask import Blueprint, jsonify, request, render_template
import subprocess

architecture_bp = Blueprint('architecture', __name__, template_folder='../templates')


@architecture_bp.route('/architecture')
def architecture_page():
    """Render the architecture view."""
    return render_template('architecture.html')


@architecture_bp.route('/api/regenerate-schema-diagram', methods=['POST'])
def regenerate_schema_diagram():
    """Execute script to regenerate the database schema diagram."""
    # Opcional: restringir a IPs locales o verificar autenticación
    # if request.remote_addr != '127.0.0.1':
    #     return jsonify({'success': False, 'error': 'Acceso no autorizado'}), 403
    try:
        result = subprocess.run(
            ['python', 'src/utils/generate_schema_diagram.py'],
            capture_output=True,
            text=True,
            check=True
        )
        return jsonify({'success': True, 'output': result.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({'success': False, 'error': e.stderr}), 500
