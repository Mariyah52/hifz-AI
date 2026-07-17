from fastapi import APIRouter, HTTPException, Response

from app.services.quran_audio_proxy import AudioProxyError, fetch_ayah_audio

"""
Unauthenticated on purpose, same reasoning as organizations.py's public
branding endpoint: ayah audio isn't user- or organization-specific data,
it's the same publicly-recitable Quran audio every visitor already hears
via the app's <audio> playback — no reason to require a login just to
proxy-download it. See quran_audio_proxy.py for why this proxy exists.
"""

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/quran-audio/{bitrate}/{global_ayah_number}")
async def get_quran_audio(bitrate: int, global_ayah_number: int) -> Response:
    try:
        audio_bytes = await fetch_ayah_audio(global_ayah_number, bitrate)
    except AudioProxyError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
