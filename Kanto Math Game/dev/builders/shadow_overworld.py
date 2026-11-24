"""Shadow Pokemon's own looks outside the battle sprite (Jordan 11-24: "overworld sprites (palette change is ok), can mega
evolve..."): every Shadow form's following-Pokemon sheet, and the Mega battle sprites of the Shadow lines that Mega Evolve,
in the Shadow purple (shadow_evolutions.shade: each pixel's brightness on the purple ramp the battle sprites use).

    assets/dungeon/followers/<dex>_shadow.png (+ shiny/)     DungeonState._follower_img tries <species>_<form> first
    assets/sprites/pokemon/mega/[back/][shiny/]<dex>_shadow_<mega form>.png    forms.apply_form's colour-variant picture

Run from the game folder (again after shadow_lines.py adds forms):  python dev/builders/shadow_overworld.py"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shadow_evolutions as SE  # noqa: E402
import pygame  # noqa: E402

FOLLOW = os.path.join("assets", "dungeon", "followers")
MEGA = os.path.join("assets", "sprites", "pokemon", "mega")


def main():
    pygame.init()
    fm = json.load(open(SE.ORRE, encoding="utf-8"))["FORM_MAP"]
    dex = sorted({int(v["id"]) for v in fm.values() if v.get("form") == "shadow" and int(v["id"]) <= SE.MAX_DEX})
    megas = json.load(open(os.path.join("assets", "mega_forms.json"), encoding="utf-8"))
    made = skipped = 0
    for d in dex:
        for sub in ("", "shiny"):
            src, dst = os.path.join(FOLLOW, sub, f"{d}.png"), os.path.join(FOLLOW, sub, f"{d}_shadow.png")
            if os.path.exists(src) and not os.path.exists(dst):
                SE.shade(src, dst)
                made += 1
            elif not os.path.exists(src):
                skipped += 1
        for f in megas.get(str(d)) or []:
            if f.get("form") == "primal":
                continue
            for sub in ("", "back", "shiny", os.path.join("back", "shiny")):
                src = os.path.join(MEGA, sub, f["sprite"])
                dst = os.path.join(MEGA, sub, f"{d}_shadow_{f['form']}.png")
                if os.path.exists(src) and not os.path.exists(dst):
                    SE.shade(src, dst)
                    made += 1
    print(f"{made} Shadow pictures made ({len(dex)} Shadow species); {skipped} with no follower sheet to colour")


if __name__ == "__main__":
    main()
