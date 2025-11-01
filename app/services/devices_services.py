from app import db
from app.models import Device

def save_or_update_device(data):
    device = Device.query.filter_by(instance_id=data['instance_id']).first()

    if not device:
        device = Device( device_id = data.get('device_id'),
            instance_id = data.get('instance_id'),
            name= data.get('name'),
            model=data.get('model'),
            project_id = data.get('project_id'),
            last_updated = data.get('actual_log_time'))
        db.session.add(device)
    else:
        device.device_id = data.get('device_id', device.device_id)
        device.name = data.get('name', device.name)
        device.model = data.get('model', device.model)
        device.project_id = data.get('project_id', device.project_id)
        device.last_updated = data.get('actual_log_time',device.last_updated)
    db.session.commit()
    return device