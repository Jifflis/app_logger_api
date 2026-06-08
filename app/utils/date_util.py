from datetime import timezone,datetime

def to_iso_utc(dt):
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

def parse_iso_datetime(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)