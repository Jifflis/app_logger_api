from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import Project, User
from datetime import datetime,timezone

project_bp = Blueprint('projects', __name__)

@project_bp.route('', methods=['POST'])
def create_project():
    data = request.get_json()
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        project = Project(name=data['name'], user_id=user.user_id, created_at=datetime.now(timezone.utc))
    
        db.session.add(project)
        db.session.commit()
        return jsonify({'message': 'Project created', 'project_id': project.project_id}), 201
    except IntegrityError:
        return jsonify({'message': 'Project name alread exist!', 'name': project.name}), 400

@project_bp.route('', methods=['GET'])
def get_projects():
    projects = Project.query.all()
    return jsonify([{'project_id': p.project_id, 'name': p.name, 'user_id': p.user_id} for p in projects])

@project_bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify({'project_id': project.project_id, 'name': project.name, 'user_id': project.user_id})

@project_bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    project.name = data.get('name', project.name)
    db.session.commit()
    return jsonify({'message': 'Project updated'})

@project_bp.route('/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted'})
