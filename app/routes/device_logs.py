from flask import Blueprint, request, jsonify,g
from sqlalchemy.exc import IntegrityError
from app import db
from sqlalchemy import func, desc, and_
from app.models import DeviceLog, Device, Project, LogLevel,Platform
from datetime import datetime,timezone,timedelta
from app.middleware.auth import token_required

log_bp = Blueprint('device_logs', __name__)

@log_bp.route('/summary', methods=['GET'])
@token_required
def get_logs_summary():
    """
    Return per-platform summary for a given project and date range:
      - total_devices (based on last_updated date)
      - total_logs (based on logs created within the range)

    Query params:
      - project_id (from g.project_id)
      - start (optional): ISO8601 UTC datetime string, e.g. "2025-11-12T00:00:00Z"
      - end (optional): ISO8601 UTC datetime string, e.g. "2025-11-13T00:00:00Z"

    Sample Request
      - GET /api/logs_summary?start=2025-11-12T00:00:00Z&end=2025-11-13T00:00:00Z
      - GET /api/logs_summary
      
    If start or end are missing, defaults to today UTC (00:00:00 to 23:59:59).
    """

    project_id = g.project_id
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    # Validate project_id
    if not project_id:
        return jsonify({"error": "Missing required parameter: project_id"}), 400

    # Determine start and end datetimes
    try:
        if start_str and end_str:
            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        else:
            # Default to today UTC
            today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            start_dt = today_utc
            end_dt = today_utc + timedelta(days=1)
            start_str = start_dt.isoformat().replace("+00:00", "Z")
            end_str = end_dt.isoformat().replace("+00:00", "Z")
    except ValueError:
        return jsonify({
            "error": "Invalid datetime format. Use ISO 8601 UTC, e.g. 2025-11-12T00:00:00Z"
        }), 400

    # ---- Query 1: Count devices by platform ---
    devices_query = (
        db.session.query(
            Device.platform.label("platform"),
            func.count(Device.instance_id).label("total_devices"),
        )
        .filter(
            Device.project_id == project_id,
            Device.last_updated >= start_dt,
            Device.last_updated < end_dt,
        )
        .group_by(Device.platform)
    )
    device_results = {row.platform: row.total_devices for row in devices_query.all()}

    # ---- Query 2: Count logs by platform ---
    logs_query = (
        db.session.query(
            Device.platform.label("platform"),
            func.count(DeviceLog.log_id).label("total_logs"),
        )
        .join(Device, Device.instance_id == DeviceLog.instance_id)
        .filter(
            Device.project_id == project_id,
            DeviceLog.actual_log_time >= start_dt,
            DeviceLog.actual_log_time < end_dt,
        )
        .group_by(Device.platform)
    )
    log_results = {row.platform: row.total_logs for row in logs_query.all()}

    # ---- Build response and ensure all platforms are included ----
    summary = []
    for p in Platform:
        summary.append({
            "platform": p.value,
            "total_devices": int(device_results.get(p, 0)),
            "total_logs": int(log_results.get(p, 0)),
        })

    summary.sort(key=lambda x: x["platform"])

    return jsonify({
        "project_id": project_id,
        "start": start_str,
        "end": end_str,
        "summary": summary,
    })


@log_bp.route('/by-instance', methods=['GET'])
@token_required
def get_logs_by_instance():
    """
    Get logs for a specific device instance.
    
    Required:
      - project_id
      - instance_id

    Optional:
      - page
      - per_page
      - start_date (YYYY-MM-DD)
      - end_date (YYYY-MM-DD)
      - level (INFO | WARNING | ERROR)

    Example:
      GET /logs/by-instance?instance_id=dvc_abc123&page=1&per_page=20
      GET /logs/by-instance?instance_id=dvc_abc123&start_date=2025-11-01&end_date=2025-11-10&level=ERROR
    """

    # --- 1️⃣ Read parameters ---
    project_id = g.project_id
    instance_id = request.args.get("instance_id")
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    level = request.args.get("level")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    # --- 2️⃣ Validation ---
    if not project_id:
        return jsonify({"error": "Missing required parameter: project_id"}), 400
    if not instance_id:
        return jsonify({"error": "Missing required parameter: instance_id"}), 400

    # --- 3️⃣ Build query ---
    query = (
        db.session.query(DeviceLog)
        .join(Device, Device.instance_id == DeviceLog.instance_id)
        .filter(
            Device.project_id == project_id,
            DeviceLog.instance_id == instance_id
        )
    )

    # --- 4️⃣ Apply optional filters ---
    if level:
        query = query.filter(DeviceLog.level == level.upper())

    if start_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            query = query.filter(DeviceLog.actual_log_time >= start_dt)
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD."}), 400

    if end_date_str:
        try:
            # Include full day
            end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
            query = query.filter(DeviceLog.actual_log_time < end_dt)
        except ValueError:
            return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD."}), 400

    # --- 5️⃣ Ordering ---
    query = query.order_by(desc(DeviceLog.actual_log_time))

    # --- 6️⃣ Pagination ---
    total_items = query.count()
    logs = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total_items + per_page - 1) // per_page

    # --- 7️⃣ Device info ---
    device = Device.query.filter_by(project_id=project_id, instance_id=instance_id).first()
    device_info = None
    if device:
        device_info = {
            "instance_id": device.instance_id,
            "device_id": device.device_id,
            "name": device.name,
            "model": device.model,
            "platform": device.platform.value if device.platform else "unknown",
            "last_updated": device.last_updated.isoformat() if device.last_updated else None
        }

    # --- 8️⃣ Serialize logs ---
    logs_data = [
        {
            "log_id": log.log_id,
            "instance_id": log.instance_id,
            "project_id": project_id,
            "level": log.level.value if log.level else None,
            "tag": log.tag,
            "message": log.message,
            "actual_log_time": log.actual_log_time.isoformat() if log.actual_log_time else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]

    # --- 9️⃣ Response ---
    return jsonify({
        "device": device_info,
        "logs": logs_data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_items": total_items,
        },
        "filters": {
            "project_id": project_id,
            "instance_id": instance_id,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "level": level
        }
    })
        
@log_bp.route('', methods=['POST'])
@token_required
def create_log():
    #instance_id
    #message
    #level = INFO,WARNING,ERROR
    #tag
    #actual_log_time
    
    data = request.get_json()
    device = Device.query.get(data['instance_id'])
    project = Project.query.get(g.project_id)
    if not device or not project:
        return jsonify({'error': 'Device or Project not found'}), 404
    log = DeviceLog(
        instance_id=device.instance_id,
        project_id=g.project_id,
        message=data['message'],
        level=LogLevel[data.get('level').upper()],
        tag=data.get('tag'),
        actual_log_time=data.get('actual_log_time'),
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'message': 'Log created', 'log_id': log.log_id}), 201

@log_bp.route('', methods=['GET'])
@token_required
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
@token_required
def update_log(log_id):
    log = DeviceLog.query.get_or_404(log_id)
    data = request.get_json()
    log.message = data.get('message', log.message)
    if 'level' in data:
        log.level = LogLevel[data['level']]
    db.session.commit()
    return jsonify({'message': 'Log updated'})

@log_bp.route('/<int:log_id>', methods=['DELETE'])
@token_required
def delete_log(log_id):
    log = DeviceLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    return jsonify({'message': 'Log deleted'})
