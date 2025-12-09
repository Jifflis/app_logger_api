from flask import Blueprint, request, jsonify,g
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import DeviceSession
from datetime import datetime,timezone,timedelta
from app.middleware.auth import token_required
from app.utils.date_util import to_iso_utc

sessions_bp = Blueprint('sessions', __name__)

@sessions_bp.route('',methods=['GET'])
@token_required
def get_sessions_by_instance():

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
            DeviceSession.actual_log_time.label("actual_log_time"),
        )
        .filter(
            DeviceSession.instance_id == instance_id,
            DeviceSession.actual_log_time >= start_dt,
            DeviceSession.actual_log_time < end_dt
        )
        .order_by(
            DeviceSession.actual_log_time.desc().nullslast(), DeviceSession.instance_id.desc()
        )
    )

    result = [
        {
            "actual_log_time": row.actual_log_time.isoformat(),
        }
        for row in query.all()
    ]

    return jsonify(result)



