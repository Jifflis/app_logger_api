from flask import Blueprint, request, jsonify
from app import db
from app.models import Device, Project, DeviceLog, Platform
from datetime import datetime,timezone,timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, and_
from app.middleware.auth import token_required
from flask import g
from app.services.devices_services import save_or_update_device
from app.services.device_sessions_services import save_session

device_bp = Blueprint('devices', __name__)


@device_bp.route('/init',methods =['POST'])
@token_required
def initialize_device():
    #instance_id
    #project_id
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
    """
    Fetch devices for a given project.
    Optional filters:
      - date (YYYY-MM-DD): filter by last_updated and logs on that date
      - platform: filter by platform
      - page, per_page: pagination
    Example:
      GET /devices?project_id=1&date=2025-11-10&platform=ios&page=1&per_page=20
    """
    # --- 1️⃣ Parse query params ---
    project_id = g.project_id
    date_str = request.args.get("date")
    platform_str = request.args.get("platform")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    if not project_id:
        return jsonify({"error": "Missing required parameter: project_id"}), 400

    # --- 2️⃣ Date handling ---
    start_dt, end_dt = None, None
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            start_dt = date_obj
            end_dt = date_obj + timedelta(days=1)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # --- 3️⃣ Base query ---
    query = (
        db.session.query(
            Device.instance_id,
            Device.device_id,
            Device.project_id,
            Device.name,
            Device.model,
            Device.platform,
            Device.created_at,
            Device.last_updated,
            func.count(DeviceLog.log_id).label("total_logs"),
        )
        .outerjoin(
            DeviceLog,
            and_(
                DeviceLog.instance_id == Device.instance_id,
                True if not start_dt else and_(
                    DeviceLog.actual_log_time >= start_dt,
                    DeviceLog.actual_log_time < end_dt,
                )
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
        .order_by(Device.last_updated.desc())
    )

    # --- 4️⃣ Optional date filter on device.last_updated ---
    if start_dt:
        query = query.filter(Device.last_updated >= start_dt, Device.last_updated < end_dt)

    # --- 5️⃣ Optional platform filter ---
    if platform_str:
        try:
            platform_enum = Platform(platform_str.lower())
            query = query.filter(Device.platform == platform_enum)
        except ValueError:
            return jsonify({"error": f"Invalid platform: {platform_str}"}), 400

    # --- 6️⃣ Pagination ---
    total_items = query.count()
    devices = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total_items + per_page - 1) // per_page

    # --- 7️⃣ Response ---
    devices_data = [
        {
            "instance_id": d.instance_id,
            "device_id": d.device_id,
            "project_id": d.project_id,
            "name": d.name,
            "model": d.model,
            "platform": d.platform.value if d.platform else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "last_updated": d.last_updated.isoformat() if d.last_updated else None,
            "total_logs": int(d.total_logs or 0),
        }
        for d in devices
    ]

    return jsonify({
        "devices": devices_data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_items": total_items,
        },
        "filters": {
            "project_id": project_id,
            "date": date_str,
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

    
