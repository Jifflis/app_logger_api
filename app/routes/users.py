from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import User
from datetime import datetime

user_bp = Blueprint('users', __name__)

@user_bp.route('', methods=['POST'])
def create_user():
    data = request.get_json()
    try:
        user = User(username=data['username'], created_at=datetime.utcnow())
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created', 'user_id': user.user_id}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Username already exists'}), 400

@user_bp.route('', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'user_id': u.user_id, 'username': u.username, 'created_at': u.created_at} for u in users])

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({'user_id': user.user_id, 'username': user.username, 'created_at': user.created_at})

@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    user.username = data.get('username', user.username)
    db.session.commit()
    return jsonify({'message': 'User updated'})

@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})
