from flask import Blueprint, request, jsonify,g
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import DeviceLog, Device, Project, LogLevel
from datetime import datetime,timezone
from app.middleware.auth import token_required

log_bp = Blueprint('device_logs', __name__)

@log_bp.route('', methods=['POST'])
@token_required
def create_log():
    data = request.get_json()
    device = Device.query.get(data['instance_id'])
    project = Project.query.get(g.project_id)
    if not device or not project:
        return jsonify({'error': 'Device or Project not found'}), 404
    log = DeviceLog(
        instance_id=device.instance_id,
        project_id=g.project_id,
        message=data['message'],
        level=LogLevel[data['level']],
        tag=data.get('tag'),
        actual_log_time=datetime.strptime(data['actual_log_time'], '%Y-%m-%d %H:%M:%S'),
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'Log created', 'log_id': log.log_id}), 201

@log_bp.route('', methods=['GET'])
def get_logs():
    logs = DeviceLog.query.all()
    return jsonify([{
        'log_id': l.log_id,
        'project_id': l.project_id,
        'instance_id': l.instance_id,
        'message': l.message,
        'level': l.level.name,
        'tag': l.tag,
        'actual_log_time': l.actual_log_time,
        'created_at': l.created_at
    } for l in logs])

@log_bp.route('/<int:log_id>', methods=['PUT'])
def update_log(log_id):
    log = DeviceLog.query.get_or_404(log_id)
    data = request.get_json()
    log.message = data.get('message', log.message)
    if 'level' in data:
        log.level = LogLevel[data['level']]
    db.session.commit()
    return jsonify({'message': 'Log updated'})

@log_bp.route('/<int:log_id>', methods=['DELETE'])
def delete_log(log_id):
    log = DeviceLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    return jsonify({'message': 'Log deleted'})
