from flask import Blueprint, request, jsonify, g
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone

from app import db
from app.middleware.auth import token_required
from app.models import Device, Platform, PushToken
from app.utils.date_util import to_iso_utc


push_token_bp = Blueprint('push_tokens', __name__)

"""
Sample requests:

Create or update a push token:
curl -X POST https://your-domain.com/api/pushTokens \
  -H "Authorization: <api-token>" \
  -H "Content-Type: application/json" \
  -d '{"instance_id": "device-instance-id", "token": "push-token-value", "platform": "ios"}'

List push tokens:
curl -X GET https://your-domain.com/api/pushTokens \
  -H "Authorization: <api-token>"

List push tokens for one device:
curl -X GET "https://your-domain.com/api/pushTokens?instance_id=device-instance-id" \
  -H "Authorization: <api-token>"

List push tokens for one platform:
curl -X GET "https://your-domain.com/api/pushTokens?platform=android" \
  -H "Authorization: <api-token>"

Get one push token:
curl -X GET https://your-domain.com/api/pushTokens/1 \
  -H "Authorization: <api-token>"

Update one push token:
curl -X PUT https://your-domain.com/api/pushTokens/1 \
  -H "Authorization: <api-token>" \
  -H "Content-Type: application/json" \
  -d '{"token": "new-push-token-value", "platform": "android"}'

Delete one push token:
curl -X DELETE https://your-domain.com/api/pushTokens/1 \
  -H "Authorization: <api-token>"
"""


def serialize_push_token(push_token):
    return {
        'id': push_token.id,
        'instance_id': push_token.instance_id,
        'token': push_token.token,
        'platform': push_token.platform.value if push_token.platform else None,
        'created_at': to_iso_utc(push_token.created_at),
        'updated_at': to_iso_utc(push_token.updated_at),
    }


def parse_platform(platform):
    if not platform:
        return Platform.UNKNOWN

    try:
        return Platform(platform.lower())
    except ValueError:
        return None


def get_project_device(instance_id):
    return Device.query.filter_by(
        instance_id=instance_id,
        project_id=g.project_id
    ).first()


def get_project_push_token_or_404(push_token_id):
    return (
        PushToken.query
        .join(Device, PushToken.instance_id == Device.instance_id)
        .filter(
            PushToken.id == push_token_id,
            Device.project_id == g.project_id
        )
        .first_or_404()
    )


@push_token_bp.route('', methods=['POST'])
@push_token_bp.route('/', methods=['POST'])
@token_required
def create_push_token():
    data = request.get_json() or {}
    instance_id = data.get('instance_id')
    token = data.get('token')
    platform = parse_platform(data.get('platform'))

    if not instance_id or not token:
        return jsonify({'error': 'instance_id and token are required'}), 400

    if platform is None:
        return jsonify({'error': 'Invalid platform'}), 400

    device = get_project_device(instance_id)
    if not device:
        return jsonify({'error': 'Device not found'}), 404

    existing_push_token = PushToken.query.filter_by(
        instance_id=device.instance_id,
        token=token
    ).first()

    if existing_push_token:
        existing_push_token.platform = platform
        existing_push_token.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify({
            'message': 'Push token updated',
            'pushToken': serialize_push_token(existing_push_token)
        })

    push_token = PushToken(
        instance_id=device.instance_id,
        token=token,
        platform=platform
    )
    db.session.add(push_token)

    try:
        db.session.commit()
        return jsonify({
            'message': 'Push token created',
            'pushToken': serialize_push_token(push_token)
        }), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Push token already exists for this device'}), 400


@push_token_bp.route('', methods=['GET'])
@push_token_bp.route('/', methods=['GET'])
@token_required
def get_push_tokens():
    instance_id = request.args.get('instance_id')
    platform_str = request.args.get('platform')

    query = (
        PushToken.query
        .join(Device, PushToken.instance_id == Device.instance_id)
        .filter(Device.project_id == g.project_id)
    )

    if instance_id:
        query = query.filter(PushToken.instance_id == instance_id)

    if platform_str:
        platform = parse_platform(platform_str)
        if platform is None:
            return jsonify({'error': 'Invalid platform'}), 400
        query = query.filter(PushToken.platform == platform)

    push_tokens = query.order_by(PushToken.created_at.desc()).all()

    return jsonify({
        'pushTokens': [serialize_push_token(push_token) for push_token in push_tokens]
    })


@push_token_bp.route('/<int:push_token_id>', methods=['GET'])
@token_required
def get_push_token(push_token_id):
    push_token = get_project_push_token_or_404(push_token_id)
    return jsonify({'pushToken': serialize_push_token(push_token)})


@push_token_bp.route('/<int:push_token_id>', methods=['PUT'])
@token_required
def update_push_token(push_token_id):
    push_token = get_project_push_token_or_404(push_token_id)
    data = request.get_json() or {}

    if 'instance_id' in data:
        device = get_project_device(data['instance_id'])
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        push_token.instance_id = device.instance_id

    if 'token' in data:
        if not data['token']:
            return jsonify({'error': 'token cannot be empty'}), 400
        push_token.token = data['token']

    if 'platform' in data:
        platform = parse_platform(data['platform'])
        if platform is None:
            return jsonify({'error': 'Invalid platform'}), 400
        push_token.platform = platform

    try:
        db.session.commit()
        return jsonify({
            'message': 'Push token updated',
            'pushToken': serialize_push_token(push_token)
        })
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Push token already exists for this device'}), 400


@push_token_bp.route('/<int:push_token_id>', methods=['DELETE'])
@token_required
def delete_push_token(push_token_id):
    push_token = get_project_push_token_or_404(push_token_id)
    db.session.delete(push_token)
    db.session.commit()
    return jsonify({'message': 'Push token deleted'})
