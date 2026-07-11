# data/

- `surahs.json` — all 114 surahs: number, name, arabicName,
  englishTranslation, ayahCount, revelationType, and juz (which of the 30
  juz its ayahs fall in). Generated + validated by the scripts in `/tools`.
- `juzBoundaries.json` — the 30 juz boundaries as surah:ayah start/end
  pairs. This is the source of truth `quranService.getJuzForAyah` uses;
  every surah's `juz` array in `surahs.json` is derived from it, not the
  other way around.

As of Phase 10, this directory no longer has any mock fixtures.
`mockDashboard.ts`, `mockStudents.ts`, and `mockTeachers.ts` (Phases 1, 7,
and 9) were retired once the real FastAPI + PostgreSQL backend existed to
replace them — see `backend/app/seed.py` for the equivalent real data, and
the root `README.md`'s Phase 10 section for the full mapping from "used to
be this mock file" to "now this backend endpoint."

Page and sajda data is not in this directory and never will be — as of
Phase 12 it's fetched live by `src/services/quranPageService.ts`, the same
"never hand-typed" principle as `quranTextService.ts`, rather than backed
by a static file here. See the root `README.md`'s Phase 12 notes for why.
