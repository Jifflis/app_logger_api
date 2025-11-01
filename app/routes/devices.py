from flask import Blueprint, request, jsonify
from app import db
from app.models import Device, Project
from datetime import datetime,timezone
from sqlalchemy.exc import IntegrityError
from app.middleware.auth import token_required
from flask import g
from app.services.devices_services import save_or_update_device
from app.services.device_sessions_services import save_session

device_bp = Blueprint('devices', __name__)


@device_bp.route('/init',methods =['POST'])
@token_required
def initialize_device():
    data = request.get_json();
    
    if not data:
        return {"error": "Invalid JSON"}, 400

    data['project_id'] = g.project_id
    
    try:
        save_or_update_device(data)
        save_session(data)
        return jsonify({'message': 'Device initiated successfully!',}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Invalid'}), 400


@device_bp.route('', methods=['POST'])
def create_device():
    data = request.get_json()
    project = Project.query.get(data['project_id'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    device = Device(
        instance_id=data['instance_id'],
        device_id=data.get('device_id'),
        project_id=project.project_id,
        name=data['name'],
        model=data.get('model'),
        created_at=datetime.now(timezone.utc) 
    )
    db.session.add(device)
    db.session.commit()
    return jsonify({'message': 'Device created', 'instance_id': device.instance_id}), 201

@device_bp.route('', methods=['GET'])
@token_required
def get_devices():
    
    print('user id',g.user_id);
    print('project id',g.project_id);
    
    devices = Device.query.all()
    return jsonify([{
        'instance_id': d.instance_id,
        'device_id': d.device_id,
        'project_id': d.project_id,
        'name': d.name,
        'model': d.model,
        'last_updated':d.last_updated
    } for d in devices])

@device_bp.route('/<int:instance_id>', methods=['GET'])
def get_device(instance_id):
    device = Device.query.get_or_404(instance_id)
    return jsonify({
        'instance_id': device.instance_id,
        'device_id': device.device_id,
        'project_id': device.project_id,
        'name': device.name,
        'model': device.model
    })

@device_bp.route('/<int:instance_id>', methods=['PUT'])
def update_device(instance_id):
    device = Device.query.get_or_404(instance_id)
    data = request.get_json()
    device.device_id = data.get('device_id', device.device_id)
    device.name = data.get('name', device.name)
    device.model = data.get('model', device.model)
    db.session.commit()
    return jsonify({'message': 'Device updated'})

@device_bp.route('/<int:instance_id>', methods=['DELETE'])
def delete_device(instance_id):
    device = Device.query.get_or_404(instance_id)
    db.session.delete(device)
    db.session.commit()
    return jsonify({'message': 'Device deleted'})

    
