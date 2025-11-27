from datetime import timezone

def to_iso_utc(dt):
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')