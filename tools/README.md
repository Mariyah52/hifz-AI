# tools/

Python scripts used to generate and validate `src/data/surahs.json` and
`src/data/juzBoundaries.json`. Not part of the shipped app — kept for
provenance and so the data can be regenerated/re-validated if corrected.

- `build_surahs.py` — writes `surahs.json` from a hand-verified table of
  (number, name, arabicName, englishTranslation, ayahCount, revelationType,
  juz placeholder). Sources: the ayah counts and names were cross-checked
  against Wikipedia's "List of chapters in the Quran"; the total ayah count
  came out to exactly 6,236, matching the standard Kufic count.
- `juzBoundaries.json` (in src/data/) was built from the 30 juz start/end
  points published at quranica.com's "What Is Juz in Quran?" article, then
  cross-verified independently: Juz 21's start (Al-Ankabut 29:45) was
  confirmed against the juz's traditional name "Utlu Ma Uhiya", which is
  literally the opening phrase of that ayah — a strong independent check
  that the boundary table is correct, not just self-consistent.
- `fix_surah_juz.py` — regenerates every surah's `juz` array directly from
  `juzBoundaries.json` rather than trusting a hand-copied per-surah column.
  Running it caught one real mismatch (Al-Furqan was hand-entered as
  juz 18-19; the verified boundary table shows it's entirely in juz 19) and
  corrected it.
- `validate_juz.py` — asserts the 30 boundaries are contiguous with no
  gaps/overlaps and sum to exactly ayahs 1–6236, and that every surah's
  `juz` array matches what the boundary table implies. Run this again if
  either data file is ever hand-edited.

**Resolved differently than planned:** page numbers (604-page Madani
mushaf), hizb, and sajda data were originally flagged here as a gap
needing "a vetted per-ayah dataset" before building page-based Mushaf
navigation. Phase 12 ended up not adding a static file for this at all —
when building it, the live API this app already trusts for ayah text
turned out to block automated tooling (`robots.txt`), which made
verifying a static table here impossible in the first place, and a
cross-referenced Quran-metadata project noted page numbering itself isn't
universal across mushaf print conventions anyway. So `page`/`hizbQuarter`/
`sajda` are fetched live at runtime instead (`src/services/quranPageService.ts`,
same principle as `quranTextService.ts`) — nothing to generate or validate
here. Rub-al-hizb (quarter-hizb) still isn't surfaced in the UI even
though `hizbQuarter` is fetched.
