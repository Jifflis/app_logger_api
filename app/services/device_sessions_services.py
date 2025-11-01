from app import db
from app.models import DeviceSession


def save_session(data):
    session = DeviceSession(
        instance_id = data.get('instance_id'),
        actual_log_time= data.get('actual_log_time'),
    )
    
    db.session.add(session);
    db.session.commit();