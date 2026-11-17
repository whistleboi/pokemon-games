"""Build assets/ev_yields.json: each species' effort-point yield (the games' "EV yield"), from Pokemon Essentials'
PBS files (pokemon.txt for Gen 1-8, the Gen 9 Pack's pokemon_base for Gen 9). Both list the species in National Dex
order, so the Nth entry is species N; the name is checked against ours.
  python dev/builders/build_ev_yields.py <Essentials folder>"""
import json
import os
import re
import sys

STAT = {"HP": "HP", "ATTACK": "ATTACK", "DEFENSE": "DEFENSE", "SPECIAL_ATTACK": "SPATK",
        "SPECIAL_DEFENSE": "SPDEF", "SPEED": "SPEED"}


def entries(path):
    out, cur = [], None
    for line in open(path, encoding="utf-8-sig"):
        line = line.strip()
        m = re.match(r"^\[(.+)\]$", line)
        if m:
            cur = {"key": m.group(1), "evs": {}}
            out.append(cur)
        elif cur is not None and line.startswith("EVs"):
            parts = [p.strip() for p in line.split("=", 1)[1].split(",")]
            cur["evs"] = {STAT[parts[i]]: int(parts[i + 1]) for i in range(0, len(parts) - 1, 2)}
    return out


def norm(s):
    return re.sub(r"[^A-Z0-9]", "", str(s).upper().replace("♀", "F").replace("♂", "M"))


def main(root):
    pbs = os.path.join(root, "Generation 9 Pack v3.3.8", "PBS", "Gen 9 backup")
    base = entries(os.path.join(pbs, "Vanilla PBS Files (with updates)", "pokemon.txt"))
    gen9 = entries(os.path.join(pbs, "Gen 9 Content (Standalone)", "pokemon_base_Gen_9_Pack.txt"))
    here = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(here, "..", "..", "assets")
    names = json.load(open(os.path.join(assets, "pokemon_names.json"), encoding="utf-8"))
    by_id = {}
    if isinstance(names, dict):
        for k, v in names.items():
            if str(k).isdigit():
                by_id[int(k)] = v if isinstance(v, str) else (v or {}).get("name", "")
            elif isinstance(v, int):
                by_id[v] = k
    out, odd = {}, []
    for i, e in enumerate(base + gen9, start=1):
        ours = by_id.get(i)
        if ours and norm(ours)[:6] != norm(e["key"]).replace("FE", "F").replace("MA", "M")[:6] and norm(ours)[:4] != norm(e["key"])[:4]:
            odd.append((i, ours, e["key"]))
        out[str(i)] = e["evs"]
    with open(os.path.join(assets, "ev_yields.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    print(len(out), "species; names that look different:", odd[:20])


if __name__ == "__main__":
    main(sys.argv[1])
