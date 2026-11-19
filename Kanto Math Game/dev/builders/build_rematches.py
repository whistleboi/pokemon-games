"""The games' own rematch teams (11-18, Jordan: "add rematches for all regions", following the games; kanto_handoff/VS_SEEKER.md).

    python dev/builders/build_rematches.py frlg|em <rematches.json> [--write]
em: Emerald's gRematchTable (hoenn_rom_tools/em_rematch.py): Hoenn's trainers; no story point holds a stage back, and
rematches start at 5 badges ("needs": {"badges": 5}), as Emerald's Match Call.

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

FILES = {"frlg": ["pokemon_area_data.json", "sevii_area_data.json"], "em": ["hoenn_area_data.json", "hoenn_oras.json"]}
GATES = {"frlg": [None, None, "visited_CELADON_CITY", "visited_FUCHSIA_CITY", "beat_champion", "sevii_warehouse_cleared"],
         "em": [None] * 6}   # (Emerald: no story point holds a stage back; rematches start at 5 badges: "needs")
SOURCE = {"frlg": "FireRed", "em": "Emerald"}
NEEDS = {"em": {"badges": 5}}   # (Emerald's Match Call: rematches only once you have 5 badges)
TOP = {"pokemon_area_data.json": 151, "sevii_area_data.json": 251, "hoenn_area_data.json": 386, "hoenn_oras.json": 386}
BY_NAME = {"em"}   # (Hoenn's trainers are ORAS's (hoenn_oras.json "add_trainers"), their classes renamed: matched by name)
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
        data = json.loads(texts[f])
        sp = data.get("STORY_PROGRESSION") or data.get("AREAS") or {}
        for area, a in sp.items():
            for i, t in enumerate(((a.get("trainer_pool") or []) + (a.get("add_trainers") or [])) if isinstance(a, dict) else []):
                if isinstance(t, dict) and isinstance(t.get("team"), list) and t["team"] and isinstance(t["team"][0], int):
                    ours.setdefault((norm_class(t.get("class")), str(t.get("name", "")).upper()), []).append((f, area, i, t))
            # (11-18: a trainer battle written into a town, met once: Seven Island's Psychics Dario and Rodette. Its name
            #  carries its class ("Psychic Dario"); the VS Seeker calls it back in town: src/world/vs_seeker.py use_town)
            for o in (a.get("explore_options") or []) if isinstance(a, dict) else []:
                t = ((o.get("event") or {}).get("battle") if isinstance(o, dict) and isinstance(o.get("event"), dict) else None)
                if isinstance(t, dict) and isinstance(t.get("team"), list) and t["team"] and isinstance(t["team"][0], int):
                    words = str(t.get("name", "")).split()
                    if len(words) > 1:
                        ours.setdefault((norm_class(t.get("class")), words[-1].upper()), []).append((f, area, "town", t))
    done, miss = [], []
    edits = {f: [] for f in texts}
    for e in rows:
        first = e["slots"][0]
        cands = ours.get((norm_class(first[1]), first[2].upper()), []) or [
            o for k, v in ours.items() if k[0] == norm_class(first[1]) and k[1].endswith(" " + first[2].upper()) for o in v]
        if not cands and kind in BY_NAME:
            cands = [o for k, v in ours.items() if k[1] == first[2].upper() or k[1].endswith(" " + first[2].upper()) for o in v]
        sp0 = [m[0] for m in first[3]]
        pick = [o for o in cands if o[3]["team"] == sp0] or [o for o in cands if set(o[3]["team"]) & set(sp0)] or (
            cands if kind in BY_NAME and len(cands) == 1 else [])   # (ORAS's first team differs from Emerald's: the one trainer of that name)
        if len(pick) != 1:
            miss.append((first[1], first[2], sp0, len(pick)))
            continue
        f, area, i, t = pick[0]
        top = TOP.get(f, 251)
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
        rem = {"source": SOURCE.get(kind, kind), "tiers": tiers}
        if NEEDS.get(kind):
            rem["needs"] = NEEDS[kind]
        edits[f].append((area, i, t, rem))
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
                b, obj = pos, None
                for _ in range(40):   # (back to the brace of the object this "name" belongs to, past an earlier run's stages)
                    b = s.rfind("{", 0, b)
                    try:
                        cand, _end = json.JSONDecoder().raw_decode(s[b:])
                    except ValueError:
                        continue
                    if isinstance(cand, dict) and cand.get("name") == t.get("name"):
                        obj = cand
                        break
                if obj is None:
                    continue
                if obj.get("team") == t.get("team") and obj.get("class") == t.get("class"):
                    found = b if "rematch" not in obj else "already"
                    break
            if found == "already":   # (written by an earlier run)
                continue
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
