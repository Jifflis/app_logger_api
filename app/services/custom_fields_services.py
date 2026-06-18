from app import db
from app.models import CustomFieldDefinition, CustomFieldValue, FieldType


def save_or_update_custom_fields(data):
    try:
        field_type = FieldType(data["field_type"])
    except ValueError:
        raise ValueError("Invalid field_type.")

    custom_field = CustomFieldDefinition.query.filter_by(
        project_id=data["project_id"],
        name=data["name"],
    ).first()

    if not custom_field:
        custom_field = CustomFieldDefinition(
            project_id=data["project_id"],
            name=data["name"],
            field_type=field_type,
        )
        db.session.add(custom_field)
        db.session.flush()

    custom_field_value = CustomFieldValue.query.filter_by(
        field_id=custom_field.field_id,
        instance_id=data["instance_id"],
    ).first()

    if not custom_field_value:
        custom_field_value = CustomFieldValue(
            field_id=custom_field.field_id,
            instance_id=data["instance_id"],
            value=data["value"],
        )
        db.session.add(custom_field_value)
    else:
        custom_field_value.value = data["value"]

    db.session.commit()

    return custom_field_value


