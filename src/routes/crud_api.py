from flask import Blueprint, jsonify, request, abort, current_app
from src.extensions import db
from datetime import datetime
import json
from sqlalchemy import or_, String, Text

crud_bp = Blueprint('crud', __name__)

def model_to_dict(obj):
    """
    Convierte un objeto SQLAlchemy en un diccionario serializable,
    iterando directamente sobre las columnas de la tabla para asegurar consistencia.
    """
    d = {}
    for c in obj.__table__.columns:
        val = getattr(obj, c.name)
        # Convertir datetime a formato estándar ISO para compatibilidad
        if isinstance(val, datetime):
            val = val.isoformat()
        d[c.name] = val
    return d

def cast_value(value: str, col_type):
    """Intenta convertir un valor string al tipo de dato de la columna del modelo."""
    try:
        pytype = col_type.python_type
        if value is None: return None
        if pytype is bool:
            return str(value).lower() in ('1', 'true', 't', 'yes', 'on')
        if pytype is datetime:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return pytype(value)
    except (ValueError, TypeError):
        return value

def get_pk_values(model, record_id_str):
    """Parsea un string que representa una clave primaria (simple o compuesta) a sus tipos correctos."""
    pk_cols = list(model.__table__.primary_key.columns)
    
    if len(pk_cols) == 1:
        return cast_value(record_id_str, pk_cols[0].type)
        
    try:
        id_parts = json.loads(record_id_str)
        if len(id_parts) != len(pk_cols):
            abort(400, description="Número incorrecto de valores para la clave primaria compuesta.")
        
        return tuple(cast_value(part, col.type) for part, col in zip(id_parts, pk_cols))
    except (json.JSONDecodeError, TypeError):
        abort(400, description="La clave primaria compuesta debe ser un array JSON (ej: [\"valor1\", \"fecha_iso\"]).")


@crud_bp.route('/mantenedores/models', methods=['GET'])
def list_models():
    """Devuelve una lista de todos los nombres de tablas/modelos disponibles."""
    return jsonify(sorted(current_app.model_map.keys()))


@crud_bp.route('/mantenedores/<table_name>', methods=['GET'])
def list_records(table_name):
    """Devuelve una lista paginada de registros para una tabla específica, con opción de búsqueda."""
    model = current_app.model_map.get(table_name)
    if not model: abort(404, description=f"Tabla '{table_name}' no encontrada.")
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search_term = request.args.get('q', None, type=str)

    pk_column_names = [c.name for c in model.__table__.primary_key.columns]
    
    query = model.query

    if search_term:
        search_filters = []
        for column in model.__table__.columns:
            if isinstance(column.type, (String, Text)):
                search_filters.append(column.ilike(f"%{search_term}%"))
        
        if search_filters:
            query = query.filter(or_(*search_filters))

    # --- INICIO DE LA CORRECCIÓN: Usar siempre el model_to_dict genérico ---
    # La paginación se mantiene igual, pero ahora la conversión de datos será consistente.
    pagination = query.order_by(*pk_column_names).paginate(page=page, per_page=per_page, error_out=False)
    records = pagination.items
    
    return jsonify({
        "pk_columns": pk_column_names,
        "records": [model_to_dict(r) for r in records],
        "pagination": {
            "total_records": pagination.total,
            "total_pages": pagination.pages,
            "current_page": pagination.page,
            "per_page": pagination.per_page,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
    })
    # --- FIN DE LA CORRECCIÓN ---

@crud_bp.route('/mantenedores/<table_name>', methods=['POST'])
def create_record(table_name):
    """Crea un nuevo registro en una tabla."""
    model = current_app.model_map.get(table_name)
    if not model: abort(404)
    
    data = request.get_json()
    if not data: abort(400, "No se recibieron datos.")

    valid_data = {k: v for k, v in data.items() if hasattr(model, k)}
    new_record = model(**valid_data)
    
    db.session.add(new_record)
    db.session.commit()
    return jsonify(model_to_dict(new_record)), 201


@crud_bp.route('/mantenedores/<table_name>/<path:record_id>', methods=['PUT'])
def update_record(table_name, record_id):
    """Actualiza un registro existente."""
    model = current_app.model_map.get(table_name)
    if not model: abort(404)
    
    key_values = get_pk_values(model, record_id)
    record = db.session.get(model, key_values)
    if not record: abort(404, f"Registro con ID '{record_id}' no encontrado.")
    
    data = request.get_json()
    if not data: abort(400)

    for key, value in data.items():
        if key not in record.__table__.primary_key.columns.keys() and hasattr(record, key):
            setattr(record, key, value)
            
    db.session.commit()
    return jsonify(model_to_dict(record))


@crud_bp.route('/mantenedores/<table_name>/<path:record_id>', methods=['DELETE'])
def delete_record(table_name, record_id):
    """Elimina un registro existente."""
    model = current_app.model_map.get(table_name)
    if not model: abort(404)

    key_values = get_pk_values(model, record_id)
    record = db.session.get(model, key_values)
    if not record: abort(404)
    
    db.session.delete(record)
    db.session.commit()
    return '', 204

@crud_bp.route('/mantenedores/<table_name>/all', methods=['DELETE'])
def delete_all_records(table_name):
    """Borra todos los registros de una tabla específica y permitida."""
    
    allowed_tables_for_deletion = ['log_entries', 'stock_prices']
    
    if table_name not in allowed_tables_for_deletion:
        abort(403, description=f"El borrado masivo no está permitido para la tabla '{table_name}'.")

    model = current_app.model_map.get(table_name)
    if not model:
        abort(404, description=f"Tabla '{table_name}' no encontrada.")

    try:
        rows_deleted = db.session.query(model).delete()
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Se eliminaron {rows_deleted} registros de la tabla '{table_name}'."
        })
    except Exception as e:
        db.session.rollback()
        abort(500, description=f"Error al borrar los registros: {e}")