from flask import Blueprint, request, jsonify, g
from sqlalchemy.exc import IntegrityError

from app import db
from app.middleware.auth import token_required
from app.services.custom_fields_services import save_or_update_custom_fields
from app.models import CustomFieldDefinition,CustomFieldValue

custom_field_bp = Blueprint("custom_fields", __name__)


@custom_field_bp.route('', methods=["POST"])
@token_required
def set_custom_field():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    required_fields = ["instance_id", "name", "value", "field_type"]
    missing = [field for field in required_fields if field not in data]

    if missing:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing,
        }), 400

    data["project_id"] = g.project_id

    try:
        custom_field_value = save_or_update_custom_fields(data)

        return jsonify({
            "message": "Custom field saved successfully.",
            "field_id": custom_field_value.field_id,
            "instance_id": custom_field_value.instance_id,
            "value": custom_field_value.value,
        }), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Custom field already exists or is invalid."}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save custom field."}), 500
    
    

@custom_field_bp.route('definitions', methods=["GET"])
@token_required
def get_custom_fields():
    fields = CustomFieldDefinition.query.all()
    return jsonify(
        [
            {
                'project_id': f.project_id, 
                'name': f.name, 
                'field_id': f.field_id,
            
            } for f in fields
            
        ]
    )   
    
 
@custom_field_bp.route('values', methods=["GET"])
@token_required
def get_custom_values():
    values = CustomFieldValue.query.all()
    return jsonify(
        [
            {
                'value_id': v.value_id, 
                'field_id': v.field_id, 
                'value': v.value,
            
            } for v in values
            
        ]
    )      