from flask import Blueprint, jsonify, request, abort
from src.extensions import db
from datetime import datetime

crud_bp = Blueprint('crud_api', __name__)


def get_model_map():
    """Return mapping of table names to model classes."""
    model_map = {}
    for cls in db.Model._decl_class_registry.values():
        if isinstance(cls, type) and hasattr(cls, '__tablename__'):
            model_map[cls.__tablename__] = cls
    return model_map


def model_to_dict(obj):
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def cast_value(value: str, pytype):
    try:
        if pytype is bool:
            return value.lower() in ('1', 'true', 't', 'yes', 'on')
        if pytype.__name__ == 'datetime':
            return datetime.fromisoformat(value)
        return pytype(value)
    except Exception:
        return value


def parse_pk(model, record_id):
    pk_cols = list(model.__table__.primary_key.columns)
    if len(pk_cols) == 1:
        col = pk_cols[0]
        return cast_value(record_id, col.type.python_type)
    parts = record_id.split(',')
    if len(parts) != len(pk_cols):
        abort(400, description='Clave primaria inválida')
    values = [cast_value(p, c.type.python_type) for p, c in zip(parts, pk_cols)]
    return tuple(values)


@crud_bp.route('/mantenedores/models', methods=['GET'])
def list_models():
    return jsonify(sorted(db.metadata.tables.keys()))


@crud_bp.route('/mantenedores/<table_name>', methods=['GET'])
def list_records(table_name):
    model = get_model_map().get(table_name)
    if not model:
        abort(404)
    records = model.query.all()
    return jsonify([model_to_dict(r) for r in records])


@crud_bp.route('/mantenedores/<table_name>', methods=['POST'])
def create_record(table_name):
    model = get_model_map().get(table_name)
    if not model:
        abort(404)
    data = request.get_json() or {}
    obj = model()
    for column in model.__table__.columns:
        name = column.name
        if name in data:
            setattr(obj, name, data[name])
    db.session.add(obj)
    db.session.commit()
    return jsonify(model_to_dict(obj)), 201


@crud_bp.route('/mantenedores/<table_name>/<record_id>', methods=['PUT'])
def update_record(table_name, record_id):
    model = get_model_map().get(table_name)
    if not model:
        abort(404)
    key = parse_pk(model, record_id)
    obj = db.session.get(model, key)
    if not obj:
        abort(404)
    data = request.get_json() or {}
    for column in model.__table__.columns:
        name = column.name
        if name in data and not column.primary_key:
            setattr(obj, name, data[name])
    db.session.commit()
    return jsonify(model_to_dict(obj))


@crud_bp.route('/mantenedores/<table_name>/<record_id>', methods=['DELETE'])
def delete_record(table_name, record_id):
    model = get_model_map().get(table_name)
    if not model:
        abort(404)
    key = parse_pk(model, record_id)
    obj = db.session.get(model, key)
    if not obj:
        abort(404)
    db.session.delete(obj)
    db.session.commit()
    return '', 204
