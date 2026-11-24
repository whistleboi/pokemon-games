"""Shadow forms for every stage of every Shadow line (Jordan 11-24, kanto_handoff/questions/ORRE.md 14: a Shadow does
everything its species does - breeding too, a Shadow mother's Egg hatching a Shadow baby). shadow_evolutions.py made the
forms a Shadow evolves into; this adds the stages before them as well - the line's first stage and its baby (Chikorita for
Shadow Bayleef, Pichu for Shadow Pikachu) - so an Egg always has a Shadow form to hatch into, and fills any stage still
missing in between. Same purple sprites (shadow_evolutions.shade), "origins" as there, and the "<X>_SHADOW" evolution
entries for the whole line. Only FORM_MAP in assets/orre_area_data.json is rewritten (the rest of the file byte for byte).

Run from the game folder:  python dev/builders/shadow_lines.py"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow_evolutions as SE  # noqa: E402
import pygame  # noqa: E402

ORRE, EVOS, MAX_DEX = SE.ORRE, SE.EVOS, SE.MAX_DEX


def _span(s, i):
    """End of the JSON object starting at s[i] ('{')."""
    depth, j, instr = 0, i, False
    while True:
        c = s[j]
        if instr:
            if c == "\\":
                j += 1
            elif c == '"':
                instr = False
        elif c == '"':
            instr = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1


def main():
    pygame.init()
    raw = open(ORRE, "rb").read().decode("utf-8")
    crlf = "\r\n" in raw[:4000]
    s = raw.replace("\r\n", "\n")
    k = s.index('"FORM_MAP": ')
    v0 = k + len('"FORM_MAP": ')
    v1 = _span(s, v0)
    fm = json.loads(s[v0:v1])
    evos = json.load(open(EVOS, encoding="utf-8"))
    names = {int(i): n for i, n in json.load(open("assets/pokemon_names.json", encoding="utf-8")).items()}
    by_name = {n.upper(): i for i, n in names.items()}
    pre = {}   # species -> the species it evolves from
    for a, targets in evos.items():
        ai = by_name.get(a.split("_")[0].upper())
        if ai is None or a.endswith("_SHADOW"):
            continue
        for t in targets:
            ti = by_name.get(t.split("_")[0].upper())
            if ti is not None and ti <= MAX_DEX:
                pre.setdefault(ti, ai)
    shadow_of = {int(v["id"]): int(fid) for fid, v in fm.items() if v.get("form") == "shadow"}
    origins = {b: set(fm[str(f)].get("origins") or [b]) for b, f in shadow_of.items()}
    next_id = max(int(f) for f in fm) + 1
    added = []

    def add(t, why):
        nonlocal next_id
        origins.setdefault(t, set()).update(why)
        if t in shadow_of or t > MAX_DEX:
            return False
        shadow_of[t] = next_id
        fm[str(next_id)] = {"id": t, "form": "shadow", "name": f"Shadow {names[t].replace('-', ' ').title()}"}
        added.append(t)
        next_id += 1
        return True

    queue = [b for b in shadow_of if b in names and b <= MAX_DEX]   # (not a form's own id)
    while queue:   # (down to the line's first stage and its baby, up to its last: the whole line)
        b = queue.pop(0)
        why = origins.get(b, {b})
        p = pre.get(b)
        if p is not None and add(p, why):
            queue.append(p)
        for target in evos.get(names[b].upper(), []):
            t = by_name.get(target.split("_")[0].upper())
            if t and add(t, why):
                queue.append(t)
    for t in added:
        fid = shadow_of[t]
        fm[str(fid)]["origins"] = sorted(origins[t])
        for folder in ("assets/sprites/pokemon", "assets/sprites/pokemon/shiny", "assets/sprites/pokemon/back"):
            src, dst = f"{folder}/{t}.png", f"{folder}/{fid}.png"
            if os.path.exists(src) and not os.path.exists(dst):
                SE.shade(src, dst)
    n = 0
    for b, fid in shadow_of.items():
        if b not in names:
            continue
        targets = [x for x in evos.get(names[b].upper(), []) if by_name.get(x.split("_")[0].upper()) in shadow_of]
        if targets:
            evos[f"{fm[str(fid)]['name'].upper()}_SHADOW"] = [f"{x.split('_')[0].upper()}_SHADOW" for x in targets]
            n += 1
    body = json.dumps(fm, ensure_ascii=False, indent=2).replace("\n", "\n  ")
    s = s[:v0] + body + s[v1:]
    json.loads(s)
    open(ORRE, "w", encoding="utf-8", newline="").write(s.replace("\n", "\r\n") if crlf else s)
    lines = ",\n".join(f"    {json.dumps(k_, ensure_ascii=False)}: {json.dumps(v_, ensure_ascii=False)}" for k_, v_ in evos.items())
    open(EVOS, "w", encoding="utf-8").write(" {\n" + lines + "\n}\n")
    ids = sorted(shadow_of[t] for t in added)
    print(f"{len(added)} new Shadow forms ({ids[0] if ids else '-'}..{ids[-1] if ids else '-'}); {n} Shadow evolution entries")


if __name__ == "__main__":
    main()
