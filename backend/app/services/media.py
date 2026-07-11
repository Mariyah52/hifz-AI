import os
import uuid

from fastapi import UploadFile

from app.config import settings

ALLOWED_EXTENSIONS = {"webm", "ogg", "mp3", "wav", "m4a"}

# Phase 28: messages can attach a voice note (reusing the same audio
# extensions above) or a generic file — kept to common, low-risk types
# rather than accepting anything, since this is user-uploaded content
# served back to other users. No virus scanning or content inspection is
# done; this is the same honest limitation Phase 10's media storage
# already carried (local disk, not production-grade).
ALLOWED_FILE_EXTENSIONS = ALLOWED_EXTENSIONS | {"pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "txt"}
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024  # 20MB


async def save_audio_file(audio: UploadFile, student_id: str) -> str:
    """
    Saves an uploaded recording to `MEDIA_ROOT/practice/<student_id>/<uuid>.<ext>`
    and returns the URL path it's served at (see the StaticFiles mount in
    `main.py`). This is the real storage Phase 7's README flagged as
    missing — still just local disk, not S3/CDN-backed, so treat it as a
    first real step rather than production-grade media storage.
    """
    ext = (audio.filename.rsplit(".", 1)[-1].lower() if audio.filename and "." in audio.filename else "webm")
    if ext not in ALLOWED_EXTENSIONS:
        ext = "webm"

    student_dir = os.path.join(settings.media_root, "practice", student_id)
    os.makedirs(student_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(student_dir, filename)

    contents = await audio.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    return f"/media/practice/{student_id}/{filename}"


async def save_test_audio_file(audio: UploadFile, student_id: str) -> str:
    """Same as `save_audio_file` but under `MEDIA_ROOT/test/<student_id>/` — one continuous recording per Test session."""
    ext = (audio.filename.rsplit(".", 1)[-1].lower() if audio.filename and "." in audio.filename else "webm")
    if ext not in ALLOWED_EXTENSIONS:
        ext = "webm"

    student_dir = os.path.join(settings.media_root, "test", student_id)
    os.makedirs(student_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(student_dir, filename)

    contents = await audio.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    return f"/media/test/{student_id}/{filename}"


class AttachmentError(Exception):
    pass


async def save_message_attachment(file: UploadFile, conversation_id: str) -> tuple[str, str]:
    """
    Saves a message attachment (voice note or generic file) to
    `MEDIA_ROOT/messages/<conversation_id>/<uuid>.<ext>`. Returns
    (url, attachment_type) where attachment_type is 'audio' for the same
    extensions Practice Mode recordings use, otherwise 'file'.
    """
    ext = (file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "")
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise AttachmentError(f"'.{ext}' isn't a supported attachment type.")

    contents = await file.read()
    if len(contents) > MAX_ATTACHMENT_BYTES:
        raise AttachmentError("Attachment is too large (20MB limit).")

    conversation_dir = os.path.join(settings.media_root, "messages", conversation_id)
    os.makedirs(conversation_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(conversation_dir, filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    attachment_type = "audio" if ext in ALLOWED_EXTENSIONS else "file"
    return f"/media/messages/{conversation_id}/{filename}", attachment_type
