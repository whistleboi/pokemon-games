"""Shadow evolution (Jordan, 10-27; not in the games): a Shadow Pokemon evolves into a Shadow form of its
evolution, with the same reverse stats (the loader swaps them for every "shadow" form). This adds the
Shadow forms that were missing (Gen 3 or earlier, Orre's rule), their sprites in the same purple as the
first 131 (each pixel's brightness on a purple ramp), and "<SHADOW X>_SHADOW" entries in the evolution
map. Each new form keeps "origins": the original Shadow species whose line leads to it (for Ho-Oh).

Run from the game folder:  python dev/builders/shadow_evolutions.py"""
import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

ORRE = "assets/orre_area_data.json"
EVOS = "assets/pokemon_evolutions.json"
FIRST_NEW_ID = 9601
MAX_DEX = 386  # Gen 3 or earlier
# The ramp measured from the first Shadow sprites (Bayleef 153 -> 9348): brightness 0..255 onto purple.
DARK, LIGHT = (40, 20, 72), (130, 70, 190)


def shade(src, dst):
    img = pygame.image.load(src)
    w, h = img.get_size()
    has_alpha = any(img.get_at((x, y)).a == 0 for x in range(0, w, 4) for y in range(0, h, 4))
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    for x in range(w):
        for y in range(h):
            c = img.get_at((x, y))
            if c.a == 0 or (not has_alpha and (c.r, c.g, c.b) == (0, 0, 0)):
                continue
            lum = (0.299 * c.r + 0.587 * c.g + 0.114 * c.b) / 255
            out.set_at((x, y), tuple(round(DARK[i] + (LIGHT[i] - DARK[i]) * lum) for i in range(3)) + (c.a,))
    pygame.image.save(out, dst)


def main():
    pygame.init()
    d = json.load(open(ORRE, encoding="utf-8"))
    fm = d["FORM_MAP"]
    evos = json.load(open(EVOS, encoding="utf-8"))
    names = {int(k): v for k, v in json.load(open("assets/pokemon_names.json", encoding="utf-8")).items()}
    by_name = {v.upper(): k for k, v in names.items()}
    shadow_of = {v["id"]: int(k) for k, v in fm.items() if v.get("form") == "shadow"}
    origins = {b: {b} for b in shadow_of}  # base species -> the original Shadow lines that reach it
    queue = list(shadow_of)
    next_id = max([FIRST_NEW_ID - 1] + [int(k) for k in fm if int(k) >= FIRST_NEW_ID]) + 1
    added = []
    while queue:
        b = queue.pop(0)
        for target in evos.get(names[b].upper(), []):
            t = by_name.get(target.split("_")[0].upper())
            if not t or t > MAX_DEX:
                continue
            origins.setdefault(t, set()).update(origins[b])
            if t not in shadow_of:
                shadow_of[t] = next_id
                fm[str(next_id)] = {"id": t, "form": "shadow", "name": f"Shadow {names[t].replace('-', ' ').title()}"}
                added.append(next_id)
                next_id += 1
                queue.append(t)
    for t, fid in shadow_of.items():
        if fid >= FIRST_NEW_ID:
            fm[str(fid)]["origins"] = sorted(origins[t])
            for folder in ("assets/sprites/pokemon", "assets/sprites/pokemon/shiny"):
                src, dst = f"{folder}/{t}.png", f"{folder}/{fid}.png"
                if os.path.exists(src) and not os.path.exists(dst):
                    shade(src, dst)
    # evolution map: SHADOW X_SHADOW -> [Y_SHADOW]
    n = 0
    for b, fid in shadow_of.items():
        targets = [x for x in evos.get(names[b].upper(), [])
                   if by_name.get(x.split("_")[0].upper()) in shadow_of]
        if targets:
            evos[f"{fm[str(fid)]['name'].upper()}_SHADOW"] = [f"{x.split('_')[0].upper()}_SHADOW" for x in targets]
            n += 1
    json.dump(d, open(ORRE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    lines = ",\n".join(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}" for k, v in evos.items())
    open(EVOS, "w", encoding="utf-8").write(" {\n" + lines + "\n}\n")  # the file's own one-line-per-entry style
    print(f"{len(added)} new Shadow forms ({added[0] if added else '-'}..{added[-1] if added else '-'}); {n} Shadow evolution entries")


if __name__ == "__main__":
    main()
