from flask import Blueprint, request, abort
import hmac
import hashlib
import os
import subprocess
from dotenv import load_dotenv

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/github-webhook', methods=['POST'])
def github_webhook():
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    signature = request.headers.get('X-Hub-Signature-256')

    if signature is None:
        abort(403)

    sha_name, signature = signature.split('=')
    mac = hmac.new(secret, msg=request.data, digestmod=hashlib.sha256)

    if not hmac.compare_digest(mac.hexdigest(), signature):
        abort(403)

    # Optional: run commands on push
    subprocess.call(['git', 'pull'])
    # You can also restart gunicorn or run migrations here

    return 'OK', 200
