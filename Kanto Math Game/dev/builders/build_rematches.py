"""The games' own rematch teams (11-18, Jordan: "add rematches for all regions", following the games; kanto_handoff/VS_SEEKER.md).

    python dev/builders/build_rematches.py frlg <rematches.json> [--write]

frlg: FireRed's VS Seeker table, read from Jordan's game file by kanto_handoff/kanto_rom_tools/frlg_rematch.py. Each
entry is matched to our Kanto / Sevii trainer by class, name and first team; its rematch stages become the trainer's
"rematch": {"source": "FireRed", "tiers": [stage 1..5: {"team", "levels", "team_moves", "unlock"} | null (skipped)]}.
"unlock": the story point that stage waits for, as FireRed's: the VS Seeker (none), Celadon visited, Fuchsia visited,
the Champion beaten, the Sevii quest done (Ruby and Sapphire delivered). Kanto keeps to #1-151 and Sevii to #1-251
(a species past that is left out of the stage). Prints matches and misses; small span edits keep the files' look.
"""
import json
import os
import re
import sys

FILES = {"frlg": ["pokemon_area_data.json", "sevii_area_data.json"]}
GATES = {"frlg": [None, None, "visited_CELADON_CITY", "visited_FUCHSIA_CITY", "beat_champion", "sevii_warehouse_cleared"]}
CLASS_ALIAS = {"POKMANIAC": "POKEMANIAC", "POKEMANIAC": "POKEMANIAC", "BREEDER": "POKEMONBREEDER", "RANGER": "POKEMONRANGER",
               "GAMER": "GAMBLER"}


def norm_class(c):
    c = re.sub(r"[^A-Z]", "", str(c).upper())
    return CLASS_ALIAS.get(c, c)


def main(kind, rows_path, write):
    rows = json.load(open(rows_path, encoding="utf-8"))["entries"]
    moves = {re.sub(r"[^A-Z]", "", k): k for k in json.load(open(os.path.join("assets", "moves.json"), encoding="utf-8"))}
    gates = GATES[kind]
    ours = {}
    texts = {}
    for f in FILES[kind]:
        path = os.path.join("assets", f)
        texts[f] = open(path, "rb").read().decode("utf-8")
        sp = json.loads(texts[f])["STORY_PROGRESSION"]
        for area, a in sp.items():
            for i, t in enumerate((a.get("trainer_pool") or []) if isinstance(a, dict) else []):
                if isinstance(t, dict) and isinstance(t.get("team"), list) and t["team"] and isinstance(t["team"][0], int):
                    ours.setdefault((norm_class(t.get("class")), str(t.get("name", "")).upper()), []).append((f, area, i, t))
    done, miss = [], []
    edits = {f: [] for f in texts}
    for e in rows:
        first = e["slots"][0]
        cands = ours.get((norm_class(first[1]), first[2].upper()), [])
        sp0 = [m[0] for m in first[3]]
        pick = [o for o in cands if o[3]["team"] == sp0] or [o for o in cands if set(o[3]["team"]) & set(sp0)]
        if len(pick) != 1:
            miss.append((first[1], first[2], sp0, len(pick)))
            continue
        f, area, i, t = pick[0]
        top = 151 if f == "pokemon_area_data.json" else 251
        tiers = []
        for s, slot in enumerate(e["slots"][1:6], start=1):
            if slot is None:
                tiers.append(None)
                continue
            mons = [m for m in slot[3] if m[0] <= top]
            if not mons:
                tiers.append(None)
                continue
            tier = {"team": [m[0] for m in mons], "levels": [m[1] for m in mons]}
            tm = [[moves.get(re.sub(r"[^A-Z]", "", mv.upper())) for mv in m[2]] for m in mons]
            if any(tm):
                tier["team_moves"] = [[x for x in mv if x] for mv in tm]
            if gates[s]:
                tier["unlock"] = gates[s]
            tiers.append(tier)
        if not any(tiers):
            continue
        edits[f].append((area, i, t, {"source": "FireRed" if kind == "frlg" else kind, "tiers": tiers}))
        done.append((area, t.get("name"), [None if x is None else x["levels"] for x in tiers]))
    for f, ed in edits.items():
        s = texts[f]
        for area, i, t, rem in ed:
            a0 = s.index(f'"{area}": {{')
            area_obj, _ = json.JSONDecoder().raw_decode(s[s.index("{", a0):])
            a1 = s.index("{", a0) + len(json.dumps(area_obj)) * 3   # (a generous window: the area's own text)
            key = f'"name": {json.dumps(t.get("name"), ensure_ascii=False)}'
            pos, found = a0, None
            while True:
                pos = s.find(key, pos + 1)
                if pos < 0 or pos > a1:
                    break
                b = s.rfind("{", 0, pos)
                try:
                    obj, end = json.JSONDecoder().raw_decode(s[b:])
                except ValueError:
                    continue
                if obj.get("team") == t.get("team") and obj.get("class") == t.get("class") and "rematch" not in obj:
                    found = b
                    break
            if found is None:
                print("   (couldn't place)", area, t.get("name"))
                continue
            s = s[:found + 1] + f' "rematch": {json.dumps(rem)},' + s[found + 1:]
        json.loads(s)
        texts[f] = s
        if write:
            open(os.path.join("assets", f), "wb").write(s.encode("utf-8"))
    print(f"matched {len(done)}, missed {len(miss)}")
    for m in miss:
        print("   miss", m)
    for d in done[:6]:
        print("  ", d)
    if write:
        print("written")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--write" in sys.argv)
