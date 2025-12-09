from flask import Blueprint, request, jsonify,g
from sqlalchemy.exc import IntegrityError
from app import db
from sqlalchemy import func, desc, and_, asc
from app.models import DeviceLog, Device, Project, LogLevel,Platform,LogTag
from datetime import datetime,timezone,timedelta
from app.middleware.auth import token_required
from app.utils.date_util import to_iso_utc

actions_bp = Blueprint('actions', __name__)

@actions_bp.route('',methods=['GET'])
@token_required
def get_actions_by_instance():
    project_id = g.project_id
    instance_id = request.args.get('instance_id')
    start_str = request.args.get('start')
    end_str = request.args.get('end')

    # Determine date range
    try:
        if start_str and end_str:
            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        else:
            today_utc = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            start_dt = today_utc
            end_dt = today_utc + timedelta(days=1)

            start_str = start_dt.isoformat().replace("+00:00", "Z")
            end_str = end_dt.isoformat().replace("+00:00", "Z")

    except ValueError:
        return jsonify({"error": "Invalid datetime format. Use ISO8601 UTC"}), 400

    query = (
        db.session.query(
            DeviceLog.actual_log_time.label("actual_log_time"),
            LogTag.tag,
        )
        .join(LogTag, DeviceLog.log_tag_id == LogTag.id)
        .filter(
            DeviceLog.project_id == project_id,
            DeviceLog.instance_id == instance_id,
            DeviceLog.actual_log_time >= start_dt,
            DeviceLog.actual_log_time < end_dt
        )
        .order_by(
            DeviceLog.actual_log_time.desc().nullslast(), DeviceLog.instance_id.desc()
        )
    )
    
    sql = query.statement.compile(
    compile_kwargs={"literal_binds": True}
)
    print(str(sql))

    result = [
        {
            "actual_log_time": to_iso_utc(row.actual_log_time),
            "tag": row.tag,
        }
        for row in query.all()
    ]

    return jsonify(result)



