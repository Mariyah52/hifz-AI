import json

with open("/home/claude/hifzai/src/data/surahs.json") as f:
    surahs = json.load(f)
with open("/home/claude/hifzai/src/data/juzBoundaries.json") as f:
    juz = json.load(f)

surah_juz = {s["number"]: set() for s in surahs}
for b in juz:
    for surah_num in range(b["startSurah"], b["endSurah"] + 1):
        surah_juz[surah_num].add(b["juz"])

changed = []
for s in surahs:
    derived = sorted(surah_juz[s["number"]])
    if derived != s["juz"]:
        changed.append((s["number"], s["name"], s["juz"], derived))
    s["juz"] = derived

with open("/home/claude/hifzai/src/data/surahs.json", "w", encoding="utf-8") as f:
    json.dump(surahs, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("Corrected entries:", changed if changed else "none")
