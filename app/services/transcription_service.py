# from faster_whisper import WhisperModel

# model = WhisperModel(
#     "small",
#     device="cpu",
#     compute_type="int8",
# )

# def transcribe_audio(file_path: str):
#     segments, info = model.transcribe(
#         file_path,
#         beam_size=5,
#         vad_filter=True,
#     )

#     text = " ".join(segment.text.strip() for segment in segments)

#     return {
#         "text": text,
#         "language": info.language,
#         "language_probability": info.language_probability,
#     }