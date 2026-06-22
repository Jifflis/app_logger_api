from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from app import db
from app.middleware.auth import token_required
from app.models import Instance


instance_bp = Blueprint('instances', __name__)


def serialize_instance(instance):
    return {
        'id': instance.id,
        'instance_id': instance.instance_id,
    }


@instance_bp.route('', methods=['POST'])
@instance_bp.route('/', methods=['POST'])
@token_required
def create_instance():
    data = request.get_json() or {}
    instance_id = data.get('instance_id')

    if not instance_id:
        return jsonify({'error': 'instance_id is required'}), 400

    existing_instance = Instance.query.filter_by(instance_id=instance_id).first()
    if existing_instance:
        return jsonify({
            'message': 'Instance already exists',
            'instance': serialize_instance(existing_instance)
        })

    instance = Instance(instance_id=instance_id)
    db.session.add(instance)

    try:
        db.session.commit()
        return jsonify({
            'message': 'Instance created',
            'instance': serialize_instance(instance)
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Instance already exists'}), 400


@instance_bp.route('', methods=['GET'])
@instance_bp.route('/', methods=['GET'])
@token_required
def get_instances():
    instance_id = request.args.get('instance_id')

    query = Instance.query

    if instance_id:
        query = query.filter(Instance.instance_id == instance_id)

    instances = query.order_by(Instance.id.desc()).all()

    return jsonify({
        'instances': [serialize_instance(instance) for instance in instances]
    })


@instance_bp.route('/<string:instance_id>', methods=['GET'])
@token_required
def get_instance(instance_id):
    instance = Instance.query.filter_by(instance_id=instance_id).first()
    if not instance:
        return jsonify({'message': 'No record found'}), 404

    deleted_instance = serialize_instance(instance)
    db.session.delete(instance)
    db.session.commit()
    return jsonify({
        'message': 'Record found',
        'instance': deleted_instance
    })


@instance_bp.route('/<int:record_id>', methods=['PUT'])
@token_required
def update_instance(record_id):
    instance = Instance.query.get_or_404(record_id)
    data = request.get_json() or {}
    new_instance_id = data.get('instance_id')

    if not new_instance_id:
        return jsonify({'error': 'instance_id is required'}), 400

    instance.instance_id = new_instance_id

    try:
        db.session.commit()
        return jsonify({
            'message': 'Instance updated',
            'instance': serialize_instance(instance)
        })
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Instance already exists'}), 400


@instance_bp.route('/<int:record_id>', methods=['DELETE'])
@token_required
def delete_instance(record_id):
    instance = Instance.query.get_or_404(record_id)
    db.session.delete(instance)
    db.session.commit()
    return jsonify({'message': 'Instance deleted'})
