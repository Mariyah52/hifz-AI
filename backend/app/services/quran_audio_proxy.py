import httpx

"""
Proxies ayah audio from the CDN this app already trusts for all Quran
audio (see frontend's audioService.ts) through this backend instead of
the browser fetching it directly.

Why this exists: playing audio via an <audio> tag doesn't need CORS, but
downloading it into a Blob for offline caching (see frontend's
audioCacheService.ts) does — and this CDN sends no
Access-Control-Allow-Origin header at all, so the browser silently blocks
every download-for-offline attempt while playback keeps working fine.
Fetching server-side sidesteps that: no CORS applies between servers,
and this backend's own response to the browser is same-origin.

Restricted to a fixed reciter + a small whitelist of real bitrates this
CDN actually serves — deliberately not a generic URL-forwarding proxy,
since accepting an arbitrary path/host from the client would turn this
into an open proxy.
"""

CDN_BASE = "https://cdn.islamic.network/quran/audio"
RECITER_EDITION = "ar.husary"  # matches frontend's audioService.ts
ALLOWED_BITRATES = {32, 40, 48, 64, 128, 192}
MIN_GLOBAL_AYAH_NUMBER = 1
MAX_GLOBAL_AYAH_NUMBER = 6236  # total ayahs in the Quran — a fixed fact, not fetched


class AudioProxyError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


async def fetch_ayah_audio(global_ayah_number: int, bitrate: int) -> bytes:
    if not (MIN_GLOBAL_AYAH_NUMBER <= global_ayah_number <= MAX_GLOBAL_AYAH_NUMBER):
        raise AudioProxyError(f"Invalid ayah number {global_ayah_number}", status_code=400)
    if bitrate not in ALLOWED_BITRATES:
        raise AudioProxyError(f"Unsupported bitrate {bitrate}", status_code=400)

    url = f"{CDN_BASE}/{bitrate}/{RECITER_EDITION}/{global_ayah_number}.mp3"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)

    if response.status_code != 200:
        raise AudioProxyError(f"CDN returned HTTP {response.status_code} for ayah {global_ayah_number}")

    return response.content
