from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import Token,TokenStatus,User,Project
from datetime import datetime,timezone

token_bp = Blueprint('tokens', __name__)

@token_bp.route('', methods=['POST'])
def create_token():
    data = request.get_json()
    try:
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error':'Project not found'}), 404

        token = Token(
            token=data['token'],
            status=TokenStatus('ACTIVE'),
            user_id=data['user_id'],
            project_id=data['project_id'],
            created_at=datetime.now(timezone.utc))
        db.session.add(token)
        db.session.commit()
        
        return jsonify({'message': 'Token created', 'token': token.token}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Token already exists'}), 400
