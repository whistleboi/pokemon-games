# Helpers that kanto_looks, johto_looks, hoenn_looks shared word for word (Checks C5, 11-24;
# made by dev/checks/share_helpers.py). Each suite runs: exec(open("dev/checks/looks_lib.py", encoding="utf-8").read())
# They use the suite's own globals (g, story, fails, check...). Change one here and every suite gets it.

def people_of(m):
    out = []
    def take(p):
        if isinstance(p, str):
            out.append((p, {}))
        elif isinstance(p, dict):
            if "any" in p:
                for q in p["any"]:
                    take(q)
            else:
                out.append((p.get("text"), p))
    for p in m.get("people") or []:
        take(p)
    for r in (m.get("rooms") or {}).values():
        for p in r.get("people") or []:
            take(p)
    for f in m.get("floors") or []:
        for p in f.get("people") or []:
            take(p)
    for sm_ in m.get("story_maps") or []:
        for p in (sm_.get("map") or {}).get("people") or []:
            take(p)
    return out


def trainer(area, t):
    counted["trainers"] += 1
    name = t.get("sprite") or "rival.png"
    if name in ("{rival_character}",) or "{" in name:
        return
    sh = OWN.get(name)
    if not sh:
        portrait[area].append(f"{t.get('name')} ({name})")
    elif not sheet_ok(sh):
        missing[area].append(f"{t.get('name')}: {sh}")
