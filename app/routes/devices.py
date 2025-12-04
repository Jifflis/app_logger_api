from flask import Blueprint, request, jsonify
from app import db
from app.models import Device, Project, DeviceLog, Platform, DeviceSession
from datetime import datetime,timezone,timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, and_
from app.middleware.auth import token_required
from flask import g
from app.services.devices_services import save_or_update_device
from app.services.device_sessions_services import save_session
from app.utils.date_util import to_iso_utc

device_bp = Blueprint('devices', __name__)


@device_bp.route('/init',methods =['POST'])
@token_required
def initialize_device():
    #instance_id
    #actual_log_time
    #model
    #device_id
    #name
    #platform = web,ios,android,macos,windows
    
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
@token_required
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
        platform=data['platform'].upper() ,
        model=data.get('model'),
        created_at=datetime.now(timezone.utc) 
    )
    db.session.add(device)
    db.session.commit()
    return jsonify({'message': 'Device created', 'instance_id': device.instance_id}), 201

@device_bp.route('', methods=['GET'])
@token_required
def get_devices():
    project_id = g.project_id
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    platform_str = request.args.get("platform")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    order = request.args.get("order", "most_recent")

    if not project_id:
        return jsonify({"error": "Missing required parameter: project_id"}), 400

    # Parse date range
    try:
        if start_str and end_str:
            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        else:
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            start_dt = today
            end_dt = today + timedelta(days=1)
            start_str = start_dt.isoformat().replace("+00:00", "Z")
            end_str = end_dt.isoformat().replace("+00:00", "Z")
    except ValueError:
        return jsonify({"error": "Invalid datetime format"}), 400

    # Aggregates
    total_logs = func.count(func.distinct(DeviceLog.log_id)).label("total_logs")
    total_sessions = func.count(func.distinct(DeviceSession.id)).label("total_sessions")
    total_actions = (
        db.session.query(func.count(DeviceLog.log_tag_id))
        .filter(
            DeviceLog.instance_id == Device.instance_id,
            DeviceLog.actual_log_time >= start_dt,
            DeviceLog.actual_log_time <= end_dt,
            DeviceLog.log_tag_id.isnot(None)
        )
        .correlate(Device)
        .as_scalar()
        .label("total_actions")
    )

    # --- MAIN QUERY WITHOUT PAGINATION ---
    base_query = (
        db.session.query(
            Device.instance_id,
            Device.device_id,
            Device.project_id,
            Device.name,
            Device.model,
            Device.platform,
            Device.created_at,
            Device.last_updated,
            total_logs,
            total_sessions,
            total_actions,
        )
        .outerjoin(
            DeviceLog,
            and_(
                DeviceLog.instance_id == Device.instance_id,
                DeviceLog.actual_log_time >= start_dt,
                DeviceLog.actual_log_time <= end_dt,
            )
        )
        .outerjoin(
            DeviceSession,
            and_(
                DeviceSession.instance_id == Device.instance_id,
                DeviceSession.actual_log_time >= start_dt,
                DeviceSession.actual_log_time <= end_dt,
            )
        )
        .filter(Device.project_id == project_id)
        .group_by(
            Device.instance_id,
            Device.device_id,
            Device.project_id,
            Device.name,
            Device.model,
            Device.platform,
            Device.created_at,
            Device.last_updated,
        )
        .having(total_sessions > 0)
    )

    # Filters
    if platform_str:
        try:
            platform_enum = Platform(platform_str.lower())
            base_query = base_query.filter(Device.platform == platform_enum)
        except ValueError:
            return jsonify({"error": f"Invalid platform: {platform_str}"}), 400

    # Ordering
    ordering_map = {
        "most_recent": Device.last_updated.desc(),
        "total_logs_desc": total_logs.desc(),
        "total_logs_asc": total_logs.asc(),
        "total_sessions_desc": total_sessions.desc(),
        "total_sessions_asc": total_sessions.asc(),
    }
    base_query = base_query.order_by(ordering_map.get(order, Device.last_updated.desc()))

    # --- FIX PAGINATION USING SUBQUERY ---
    subq = base_query.subquery()

    total_items = db.session.query(func.count()).select_from(subq).scalar()

    results = (
        db.session.query(subq)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Build response
    devices_data = []
    for row in results:
        devices_data.append({
            "instance_id": row.instance_id,
            "device_id": row.device_id,
            "project_id": row.project_id,
            "name": row.name,
            "model": row.model,
            "platform": row.platform.value if row.platform else None,
            "created_at": to_iso_utc(row.created_at),
            "last_updated": to_iso_utc(row.last_updated),
            "total_logs": int(row.total_logs or 0),
            "total_sessions": int(row.total_sessions or 0),
            "total_actions": int(row.total_actions or 0),
        })

    return jsonify({
        "devices": devices_data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": (total_items + per_page - 1) // per_page,
        },
        "filters": {
            "project_id": project_id,
            "start": start_str,
            "end": end_str,
            "platform": platform_str,
        },
    })




@device_bp.route('/<int:instance_id>', methods=['GET'])
@token_required
def get_device(instance_id):
    device = Device.query.get_or_404(instance_id)
    return jsonify({
        'instance_id': device.instance_id,
        'device_id': device.device_id,
        'project_id': device.project_id,
        'name': device.name,
        'platform':device.platform.value,
        'model': device.model
    })

@device_bp.route('/<int:instance_id>', methods=['PUT'])
@token_required
def update_device(instance_id):
    device = Device.query.get_or_404(instance_id)
    data = request.get_json()
    device.device_id = data.get('device_id', device.device_id)
    device.name = data.get('name', device.name)
    device.model = data.get('model', device.model)
    device.platform = data.get('platform',device.platform)
    db.session.commit()
    return jsonify({'message': 'Device updated'})

@device_bp.route('/<int:instance_id>', methods=['DELETE'])
@token_required
def delete_device(instance_id):
    device = Device.query.get_or_404(instance_id)
    db.session.delete(device)
    db.session.commit()
    return jsonify({'message': 'Device deleted'})

    
