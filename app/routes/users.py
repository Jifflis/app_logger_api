from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import User
from datetime import datetime
import re

user_bp = Blueprint('users', __name__)

# Simple email regex for validation
EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

@user_bp.route('', methods=['POST'])
def create_user():
    data = request.get_json()

    # Validate required fields
    if 'username' not in data or not data['username']:
        return jsonify({'error': 'Username is required'}), 400
    if 'email' not in data or not data['email']:
        return jsonify({'error': 'Email is required'}), 400
    if not re.match(EMAIL_REGEX, data['email']):
        return jsonify({'error': 'Invalid email format'}), 400

    try:
        user = User(
            username=data['username'],
            email=data['email'],
            created_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created', 'user_id': user.user_id}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Username or email already exists'}), 400


@user_bp.route('', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([
        {
            'user_id': u.user_id,
            'username': u.username,
            'email': u.email,
            'created_at': u.created_at
        } for u in users
    ])


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'user_id': user.user_id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at
    })


@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        if not re.match(EMAIL_REGEX, data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        user.email = data['email']

    try:
        db.session.commit()
        return jsonify({'message': 'User updated'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Username or email already exists'}), 400


@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})
