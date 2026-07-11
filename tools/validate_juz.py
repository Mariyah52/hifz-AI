import json

with open("/home/claude/hifzai/src/data/surahs.json") as f:
    surahs = json.load(f)
with open("/home/claude/hifzai/src/data/juzBoundaries.json") as f:
    juz = json.load(f)

ayah_count = {s["number"]: s["ayahCount"] for s in surahs}
offset = {}
running = 0
for s in surahs:
    offset[s["number"]] = running
    running += s["ayahCount"]

def global_num(surah, ayah):
    return offset[surah] + ayah

prev_end_global = 0
for b in juz:
    start_g = global_num(b["startSurah"], b["startAyah"])
    end_g = global_num(b["endSurah"], b["endAyah"])
    ok_contig = (start_g == prev_end_global + 1)
    size = end_g - start_g + 1
    print(f"juz {b['juz']:>2}: global {start_g:>4}-{end_g:>4} ({size:>3} ayahs) contiguous={ok_contig}")
    assert ok_contig, f"gap/overlap before juz {b['juz']}"
    assert end_g >= start_g
    prev_end_global = end_g

assert prev_end_global == 6236, f"total mismatch: {prev_end_global} != 6236"
print("OK: 30 juz boundaries are contiguous and cover exactly 1-6236")

# cross-check surah.juz arrays against boundaries: every surah's ayahs must be covered by exactly its listed juz set
surah_juz_from_boundaries = {s["number"]: set() for s in surahs}
for b in juz:
    for surah_num in range(b["startSurah"], b["endSurah"] + 1):
        surah_juz_from_boundaries[surah_num].add(b["juz"])

mismatches = []
for s in surahs:
    expected = set(s["juz"])
    derived = surah_juz_from_boundaries[s["number"]]
    if expected != derived:
        mismatches.append((s["number"], s["name"], expected, derived))

if mismatches:
    print("MISMATCHES:")
    for m in mismatches:
        print(m)
else:
    print("OK: every surah's juz[] list matches the boundary table exactly")
