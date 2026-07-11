import httpx

from app.services.arabic_text import ReferenceWord

"""
Same principle as `src/services/quranTextService.ts` on the frontend:
Quran text is fetched live from the verified API, never hand-typed or
bundled — extended here because Phase 14's recitation comparison needs
the reference text server-side (to diff it against a Whisper
transcription), not just for display in the browser.

Phase 21/22 extend this further to cover juz/page numbers and the full
surah list, needed for analytics bucketing (weakest juz/page) and the
new test modes (match_surah, match_page, etc.) — same "fetch live, cache
in-process, never hand-type positional data" principle Phase 12
established, not a new pattern.
"""

API_BASE = "https://api.alquran.cloud/v1"
TEXT_EDITION = "quran-uthmani"


class ReferenceTextError(Exception):
    pass


# Per-surah ayah position cache (juz/page per ayah number) — these are
# fixed facts about the mushaf, so caching indefinitely per-process is
# safe and avoids re-fetching the same surah on every analytics/test-
# generation call.
_ayah_position_cache: dict[int, dict[int, dict]] = {}
_surah_list_cache: list[dict] | None = None
_juz_ayahs_cache: dict[int, list[tuple[int, int]]] = {}


async def get_reference_words(surah_number: int, from_ayah: int, to_ayah: int) -> list[ReferenceWord]:
    ayahs = await _fetch_surah_ayahs(surah_number)
    words: list[ReferenceWord] = []
    for ayah in ayahs:
        number_in_surah = ayah["numberInSurah"]
        if from_ayah <= number_in_surah <= to_ayah:
            for word in ayah["text"].split(" "):
                if word:
                    words.append(ReferenceWord(word=word, ayah_number=number_in_surah))

    if not words:
        raise ReferenceTextError(f"No ayahs found for {surah_number}:{from_ayah}-{to_ayah}")

    return words


async def _fetch_surah_ayahs(surah_number: int) -> list[dict]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_BASE}/surah/{surah_number}/{TEXT_EDITION}")
    if response.status_code != 200:
        raise ReferenceTextError(f"Failed to fetch reference text (HTTP {response.status_code})")
    return response.json()["data"]["ayahs"]


async def get_surah_ayah_texts(surah_number: int) -> list[tuple[int, str]]:
    """Every (ayah_number, text) pair for a surah — used by recognition test modes (first/last ayah, match_surah)."""
    ayahs = await _fetch_surah_ayahs(surah_number)
    return [(a["numberInSurah"], a["text"]) for a in ayahs]


async def get_ayah_positions(surah_number: int) -> dict[int, dict]:
    """
    `{ayah_number: {"juz": int, "page": int}}` for a whole surah, cached
    per-process after the first fetch — juz/page assignments are fixed
    facts about the mushaf, not something that changes between requests.
    """
    if surah_number in _ayah_position_cache:
        return _ayah_position_cache[surah_number]

    ayahs = await _fetch_surah_ayahs(surah_number)
    positions = {
        a["numberInSurah"]: {"juz": a.get("juz"), "page": a.get("page")}
        for a in ayahs
    }
    _ayah_position_cache[surah_number] = positions
    return positions


async def get_surah_list() -> list[dict]:
    """
    All 114 surahs' number/name/ayah count, fetched once and cached for
    the process's lifetime — used by `match_surah` test questions and
    anywhere else that needs "pick a random other surah" without
    bundling a static surah list backend-side.
    """
    global _surah_list_cache
    if _surah_list_cache is not None:
        return _surah_list_cache

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_BASE}/surah")
    if response.status_code != 200:
        raise ReferenceTextError(f"Failed to fetch surah list (HTTP {response.status_code})")

    data = response.json()["data"]
    _surah_list_cache = [
        {"number": s["number"], "name": s["englishName"], "ayah_count": s["numberOfAyahs"]} for s in data
    ]
    return _surah_list_cache


async def get_juz_ayahs(juz_number: int) -> list[tuple[int, int]]:
    """
    `[(surah_number, ayah_number), ...]` for every ayah in a juz — fetched
    live from the same verified source and cached indefinitely per-process
    (a juz's composition is a fixed fact). Used by Phase 27's real
    juz-completion certificate check: rather than hand-maintaining which
    ayahs fall in which juz, ask the source that already carries that data.
    """
    if juz_number in _juz_ayahs_cache:
        return _juz_ayahs_cache[juz_number]

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{API_BASE}/juz/{juz_number}/{TEXT_EDITION}")
    if response.status_code != 200:
        raise ReferenceTextError(f"Failed to fetch juz {juz_number} (HTTP {response.status_code})")

    ayahs = [(a["surah"]["number"], a["numberInSurah"]) for a in response.json()["data"]["ayahs"]]
    _juz_ayahs_cache[juz_number] = ayahs
    return ayahs
