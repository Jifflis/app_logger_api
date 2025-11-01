from functools import wraps
from flask import request, jsonify, g
from app.models import Token, User
from cache import cache_token, get_user_session

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing"}), 401

        # 1️⃣ Try Redis first
        cache_user_session = get_user_session(token)
        if cache_user_session:
            g.user_id = cache_user_session["user_id"]
            g.project_id = cache_user_session["project_id"]
            return f(*args, **kwargs)

        # 2️⃣ Fallback: query the DB
        token_record = Token.query.filter_by(token=token).first()
        if not token_record or token_record.status.name != "ACTIVE":
            return jsonify({"message": "Invalid or inactive token"}), 401


        # 3️⃣ Cache it for next time
        cache_token(token, token_record.user_id,token_record.project_id)
        g.user_id = token_record.user_id
        g.project_id = token_record.project_id
        return f(*args, **kwargs)

    return decorated
