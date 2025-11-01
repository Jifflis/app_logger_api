import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def cache_token(token, user_id, project_id):
    """Cache token and user_id for 1 hour"""
    data = {"user_id": user_id,"project_id":project_id}
    r.setex(f"token:{token}", 3600, json.dumps(data))

def get_user_by_token(token):
    """Retrieve user_id from cache"""
    data = r.get(f"token:{token}")
    if data:
        return json.loads(data).get("user_id")
    return None

def get_user_session(token):
    """Retrieve user_id and project_id from cache"""
    data = r.get(f"token:{token}")
    if data:
        return json.loads(data)
    return None