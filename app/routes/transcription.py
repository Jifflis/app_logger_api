# import os
# import uuid
# from flask import Blueprint, request, jsonify
# from werkzeug.utils import secure_filename

# from app.services.transcription_service import transcribe_audio

# transcribe_bp = Blueprint("transcribe", __name__)

# UPLOAD_FOLDER = "/tmp/transcriptions"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# @transcribe_bp.route("/transcribe", methods=["POST"])
# def transcribe():
#     if "audio" not in request.files:
#         return jsonify({"error": "Missing audio file"}), 400

#     audio = request.files["audio"]

#     if audio.filename == "":
#         return jsonify({"error": "Empty filename"}), 400

#     filename = secure_filename(audio.filename)
#     ext = os.path.splitext(filename)[1] or ".m4a"

#     temp_name = f"{uuid.uuid4()}{ext}"
#     temp_path = os.path.join(UPLOAD_FOLDER, temp_name)

#     try:
#         audio.save(temp_path)

#         result = transcribe_audio(temp_path)

#         return jsonify(result), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

#     finally:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)