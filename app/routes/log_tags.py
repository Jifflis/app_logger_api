from flask import Blueprint, request, jsonify,g
from sqlalchemy.exc import IntegrityError
from app import db
from sqlalchemy import func
from app.models import DeviceLog, LogTag
from datetime import datetime,timezone,timedelta
from app.middleware.auth import token_required

log_tag_bp = Blueprint('log_tags', __name__)

@log_tag_bp.route('/summary', methods=['GET'])
@token_required
def get_logs_summary():
    
    project_id = g.project_id
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    if not project_id:
        return jsonify({"error": "Missing required parameter: project_id"}), 400

    try:
        if start_str and end_str:
            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        else:
            today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            start_dt = today_utc
            end_dt = today_utc + timedelta(days=1)
            start_str = start_dt.isoformat().replace("+00:00", "Z")
            end_str = end_dt.isoformat().replace("+00:00", "Z")
    except ValueError:
        return jsonify({
            "error": "Invalid datetime format. Use ISO 8601 UTC, e.g. 2025-11-12T00:00:00Z"
        }), 400

    tags_query = (
        db.session.query(
            LogTag.tag.label("tag"),
            LogTag.id.label("id"),
            func.count(DeviceLog.log_id).label("total_count")
        )
        .outerjoin(
            DeviceLog,
            (DeviceLog.log_tag_id == LogTag.id) &
            (DeviceLog.actual_log_time >= start_dt) &
            (DeviceLog.actual_log_time < end_dt)
        )
        .filter(LogTag.project_id == project_id)
        .group_by(LogTag.id, LogTag.tag)
    )

    tag_list = [
        {"id": row.id, "tag": row.tag, "count": row.total_count}
        for row in tags_query.all()
    ]

    tag_list.sort(key=lambda x: x["tag"])

    return jsonify({
        "project_id": project_id,
        "start": start_str,
        "end": end_str,
        "tags": tag_list,
    })



