"""Orre's trainers in Pokemon Orre 2.1.1's sprites (Jordan, 11-01): Cipher peons in the fan game's Cipher
grunt (the colour-named ones, Blusix and the rest, in their colour), its own Miror B., Gorigan, Evice,
Gonzap and Willie, and its Orre-style riders, chasers, hunters, cool trainers and so on.

The sprites are copied to assets/sprites/trainers/orre_<name>.png (nothing of ours is replaced) and the
"sprite" of each matching trainer in assets/orre_area_data.json is changed in place (the rest of the
file is left as it is). Kept: Venus (the fan game's "Venus" is its Mt. Battle leader's robed figure),
and the admins and champions it has no sprite for.

    python dev/builders/import_orre_trainers.py ["<Pokemon Orre folder>"]
"""
import json
import os
import re
import shutil
import sys
import zlib

ORRE_GAME = os.path.join(os.path.expanduser("~"), "Downloads", "Pokemon_Orre_2.1.1", "Pokemon_Orre_2.1.1_reupload")
DATA = os.path.join("assets", "orre_area_data.json")
OUT = os.path.join("assets", "sprites", "trainers")

COLOURS = {"Blusix": "CIPHER_BLUE", "Browsix": "CIPHER_BROWN", "Greesix": "CIPHER_GREEN", "Pinksix": "CIPHER_PINK",
           "Purpsix": "CIPHER_PURPLE", "Resix": "CIPHER_RED", "Yellosix": "CIPHER_YELLOW"}
BY_NAME = {"Miror B.": "TRAINER_MIROR_B", "Gorigan": "CIPHER_GORIGAN", "Evice": "LEADER_Evice",
           "Gonzap": "SNAGEM_GONZAP", "Rider Willie": "RIDER_WILLIE", "Curmudgeon": "FUN_OLD_MAN",
           "Rich Boy": "RICH_BOY", "Roller Boy": "ROLLER_BOY_KAIB"}
PAIRS = {"CHASER": ("CHASER_M", "CHASER_F"), "HUNTER": ("HUNTER_M", "HUNTER_F"),
         "BODYBUILDER": ("BODYBUILDER", "BODYBUILDER2")}
BY_CLASS = {"CIPHER_PEON": "CIPHER_PEON", "TEAM_SNAGEM": "SNAGEM_GRUNT", "RIDER": "RIDER",
            "ROLLER_BOY": "ROLLER_BOY_KAIB", "STPERFORMER": "STREET_PERFORMER", "SAILOR": "SAILOR",
            "NAVIGATOR": "SAILOR", "RESEARCHER": "SCIENTIST", "FUN_OLD_MAN": "FUN_OLD_MAN", "WORKER": "ENGINEER"}


def pick(t):
    """The fan game's sprite for one of our trainers, or None (keep ours)."""
    name, cls, sprite = t.get("name", ""), t.get("class", ""), t.get("sprite", "")
    for word, fan in COLOURS.items():
        if word in name:
            return fan
    for word, fan in BY_NAME.items():
        if word in name:
            return fan
    kind = cls if cls in PAIRS else next((k for k in PAIRS if k.title() in name), None)
    if kind:
        return PAIRS[kind][zlib.crc32(name.encode()) % 2]  # the two looks, fixed per trainer
    if cls in ("COOLTRAINER", "COLOSSEUM") and "Cooltrainer" in name:
        return "COOL_TRAINER_F" if sprite == "acetrainer_f.png" else "COOL_TRAINER_M"
    return BY_CLASS.get(cls)


def trainers(x):
    if isinstance(x, dict):
        if isinstance(x.get("sprite"), str) and x.get("name"):
            yield x
        for v in x.values():
            yield from trainers(v)
    elif isinstance(x, list):
        for v in x:
            yield from trainers(v)


def enclosing(text, i):
    """(start, end) of the JSON object around index i."""
    depth, s = 0, i
    while s > 0:
        s -= 1
        if text[s] == "}":
            depth += 1
        elif text[s] == "{":
            if depth == 0:
                break
            depth -= 1
    depth, e = 0, i
    while e < len(text):
        if text[e] == "{":
            depth += 1
        elif text[e] == "}":
            if depth == 0:
                break
            depth -= 1
        e += 1
    return s, e + 1


def main(root):
    text = open(DATA, encoding="utf-8").read()
    data = json.loads(text)
    plan = {}
    for t in trainers(data["STORY_PROGRESSION"]):
        fan = pick(t)
        if fan:
            plan[(t["name"], t["sprite"])] = f"orre_{fan.lower()}.png"
    for fan in {v for v in plan.values()}:
        src = os.path.join(root, "Graphics", "Trainers", fan[5:-4].upper() + ".png")
        if not os.path.isfile(src):  # (the file names keep their own case)
            src = next(os.path.join(root, "Graphics", "Trainers", f) for f in os.listdir(os.path.join(root, "Graphics", "Trainers"))
                       if f.lower() == fan[5:])
        shutil.copyfile(src, os.path.join(OUT, fan))
    changed = 0
    for (name, old), new in plan.items():
        for m in list(re.finditer(r'"name": ' + re.escape(json.dumps(name, ensure_ascii=False)), text)):
            s, e = enclosing(text, m.start())
            block = text[s:e]
            fixed = block.replace(f'"sprite": "{old}"', f'"sprite": "{new}"', 1)
            if fixed != block:
                text = text[:s] + fixed + text[e:]
                changed += 1
    json.loads(text)
    open(DATA, "w", encoding="utf-8").write(text)
    print(f"{len(set(plan.values()))} sprites copied, {changed} trainers changed")
    for (name, old), new in sorted(plan.items()):
        print(f"  {name:32} {old:18} -> {new}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ORRE_GAME)
