from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import DeviceTag, Device, Project

tag_bp = Blueprint('device_tags', __name__)

@tag_bp.route('', methods=['POST'])
def create_tag():
    data = request.get_json()
    device = Device.query.get(data['instance_id'])
    project = Project.query.get(data['project_id'])
    if not device or not project:
        return jsonify({'error': 'Device or Project not found'}), 404
    tag = DeviceTag(
        instance_id=device.instance_id,
        tag_name=data['tag_name'],
        tag_value=data['tag_value'],
        project_id=project.project_id
    )
    db.session.add(tag)
    try:
        db.session.commit()
        return jsonify({'message': 'Tag created'}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Duplicate tag for this device'}), 400

@tag_bp.route('', methods=['GET'])
def get_tags():
    tags = DeviceTag.query.all()
    return jsonify([{
        'instance_id': t.instance_id,
        'tag_name': t.tag_name,
        'tag_value': t.tag_value,
        'project_id': t.project_id
    } for t in tags])

@tag_bp.route('/<int:instance_id>/<tag_name>', methods=['PUT'])
def update_tag(instance_id, tag_name):
    tag = DeviceTag.query.filter_by(instance_id=instance_id, tag_name=tag_name).first_or_404()
    data = request.get_json()
    tag.tag_value = data.get('tag_value', tag.tag_value)
    db.session.commit()
    return jsonify({'message': 'Tag updated'})

@tag_bp.route('/<int:instance_id>/<tag_name>', methods=['DELETE'])
def delete_tag(instance_id, tag_name):
    tag = DeviceTag.query.filter_by(instance_id=instance_id, tag_name=tag_name).first_or
