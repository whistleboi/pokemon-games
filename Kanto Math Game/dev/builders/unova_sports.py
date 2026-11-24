"""python dev/builders/unova_sports.py : Nimbasa's Big Stadium and Small Court from Black 2's own file (batch 4c, 11-24).

Writes assets/b2_sports.json, which src/world/nimbasa_sports.py reads:
- "fields": the five playing fields (zones 81 football, 82 baseball, 83 soccer: Big Stadium; 86 tennis, 87 basketball:
  Small Court), each a room of Nimbasa (unova.py NIMBASA_ROOMS), with the athletes standing on it.
- "athletes": every athlete and Backers pair standing on a field (people with script 3000 + id; a pair's second 5000 + id),
  by tier: Black 2 swaps each one's team by your badges (tier 1: 3-4 badges, Lv ~25; 2: 5-6, ~33, Backers join; 3: 7-8,
  ~47; 4: after the League, ~62). The tiers are the trainer table's entries of the same class and name, sorted by level.
- "visitors": Black 2's 52 post-game visitors (trainer ids 88-132 + 7, 15, 17, 18, 20, 27, 28): three a day, standing on
  the fields' three spare spots (the people drawn 163-165 there: the game's script picks who). Each has its walking look
  (overlay 12's class -> overworld table, as the Subway's) and the item it gives (Bulbapedia's Big Stadium page, 11-24).
- "schedule": the sport by weekday and the game hours (Bulbapedia's table; the fields are shut during a game).
- "prizes": the athletes' item after a win (tier 1 Potion, 2 Super Potion, 3 Hyper Potion; post-game a vitamin by sport;
  Backers give none, as Black 2)."""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import unova_trainers as ut   # noqa: E402  (its path set-up finds kanto_handoff/unova_map_tools)
import g5map                  # noqa: E402
import overlays               # noqa: E402
import utrainers              # noqa: E402

OUT = os.path.join(ut.GAME, "assets", "b2_sports.json")
FIELDS = {81: ("stadium", "football"), 82: ("stadium", "baseball"), 83: ("stadium", "soccer"),
          86: ("court", "tennis"), 87: ("court", "basketball")}
ATHLETE_CLASSES = ("Infielder", "Linebacker", "Striker", "Smasher", "Hoopster", "Backers")
VISITORS = list(range(88, 133)) + [7, 15, 17, 18, 20, 27, 28]
VISITOR_ITEMS = {   # (Bulbapedia, Big Stadium and Small Court, "Items": what each gives after a win)
    "Waiter Clint": "MOOMOO_MILK", "Waitress Bonita": "MOOMOO_MILK", "Nurse Kirsten": "FULL_RESTORE",
    "Doctor Jules": "MAX_REVIVE", "Baker Lilly": "MOOMOO_MILK", "Scientist Simon": "ETHER", "Scientist Blythe": "ETHER",
    "Ace Trainer Lucille": "PP_UP", "Ace Trainer Charlie": "PP_UP", "Veteran Arlen": "PP_MAX", "Veteran Sayuri": "PP_MAX",
    "Nursery Aide Leah": "RARE_CANDY", "Youngster Kevin": "ULTRA_BALL", "Lass Dana": "ULTRA_BALL",
    "Backpacker Alexander": "MAX_REPEL", "Backpacker Patty": "MAX_REPEL", "Socialite Emilia": "BIG_PEARL",
    "Gentleman Renaud": "NUGGET", "Pokefan Darcy": "MAX_POTION", "Pokefan Colin": "MAX_POTION",
    "Battle Girl Janie": "ENERGY_ROOT", "Black Belt Lao": "ENERGY_ROOT", "Ranger Alain": "MAX_REPEL",
    "Ranger Heidi": "MAX_REPEL", "Breeder Owen": "RARE_CANDY", "Breeder Brooke": "RARE_CANDY", "Pilot Leonard": "QUICK_BALL",
    "Roughneck Fletcher": "DUSK_BALL", "Fisherman Devon": "DIVE_BALL", "Lady Sophie": "PEARL", "Rich Boy Anthony": "STARDUST",
    "Preschooler Mia": "POKE_DOLL", "Preschooler Evan": "POKE_TOY", "Worker Matthew": "BLUE_SHARD",
    "Janitor Caleb": "GREEN_SHARD", "Hiker Russel": "RED_SHARD", "Worker Tyler": "YELLOW_SHARD"}
# (everyone else: an Ultra Ball - Artist, the Clerks, Dancer, Depot Agent, Harlequin, Maid, Musician, Parasol Lady,
#  Policeman, the Psychics, the School Kids)
WALK_EXTRA = {"Dancer": 55, "Musician": 56}   # (classes not in overlay 12's table: the Dancer and the Musician as Route 5's own people:
#  Musician Preston is code 56 there, 11-24)
PRIZES = {"1": "POTION", "2": "SUPER_POTION", "3": "HYPER_POTION",
          "4": {"Linebacker": "PROTEIN", "Infielder": "IRON", "Hoopster": "CALCIUM", "Smasher": "ZINC", "Striker": "CARBOS"}}
SCHEDULE = {   # weekday (Monday 0) -> (Big Stadium's sport, Small Court's); game hours [start, end) in 24 h
    "stadium": ["baseball", "soccer", "football", "baseball", "soccer", "football", "baseball"],
    "court": ["tennis", "basketball", "tennis", "basketball", "tennis", "basketball", "tennis"],
    "hours": {"baseball": [14, 17], "soccer": [14, 16], "football": [14, 16], "tennis": [10, 11], "basketball": [10, 12]}}


def tier_of(level):
    return 1 if level < 30 else 2 if level < 40 else 3 if level < 55 else 4


def _obj(r):
    for oid, ram, d in overlays.overlays(r):
        if oid == 12:
            a = 0x216d9a8 - ram
            return {c: code for c, code in (struct.unpack_from("<HH", d, a + 4 * i) for i in range(56))}
    return {}


def _pic(r, e, cls_id, obj):
    """The battle picture: a class shared by a man's and a woman's (Ace Trainer, Pokefan...) takes _m / _f by the
    overworld code (the lower is the man's, as unova_subway.py); the Backers pairs: class 68 men, 69 women (a/0/7/1 67/68)."""
    if cls_id in (68, 69):
        e["sprite"] = "b2_backers_%s.png" % ("m" if cls_id == 68 else "f")
        return
    cls_text = utrainers._text(r, 383)
    me = ut._clean(cls_text[cls_id])
    twin = [k for k, t in enumerate(cls_text) if k != cls_id and ut._clean(t) == me and obj.get(k)]
    if twin and obj.get(cls_id):
        slug = ut._slug(me.replace("é", "e")).replace("pokemon_", "")
        pic = "b2_%s_%s.png" % (slug, "m" if obj[cls_id] < obj[twin[0]] else "f")
        if os.path.isfile(os.path.join(ut.SPRITES, pic)):
            e["sprite"] = pic
            return
    if e["sprite"].startswith("b2_") and os.path.isfile(os.path.join(ut.SPRITES, e["sprite"])):
        return
    if not os.path.isfile(os.path.join(ut.SPRITES, e["sprite"])):
        slug = ut._slug(me.replace("é", "e")).replace("pokemon_", "")
        if os.path.isfile(os.path.join(ut.SPRITES, "b2_%s.png" % slug)):
            e["sprite"] = "b2_%s.png" % slug


def main():
    Z = g5map.Zones()
    r = Z.r
    obj = _obj(r)
    fields, athletes = {}, {}
    for z, (arena, sport) in FIELDS.items():
        here = []
        for p in Z.events(z)["people"]:
            s = p["script"]
            if not 3000 <= s < 6000:
                continue
            tid = s - 5000 if s >= 5000 else s - 3000
            t = utrainers.team(r, tid)
            cls = ut._clean(t["class"])
            if cls not in ATHLETE_CLASSES:
                continue
            key = "%s %s" % (cls, ut._clean(t["name"]))
            if key not in athletes:
                tiers = {}
                for i in utrainers.find(r, t["name"]):
                    u = utrainers.team(r, i)
                    if ut._clean(u["class"]) != cls or not u["mons"]:
                        continue
                    e = ut.entry(r, i)
                    _pic(r, e, u["class_id"], obj)
                    e["rewards"] = {"balls": e["rewards"]["balls"]}
                    tier = tier_of(max(m["level"] for m in u["mons"]))
                    prize = PRIZES[str(tier)]
                    prize = prize.get(cls) if isinstance(prize, dict) else prize
                    if prize and cls != "Backers":
                        e["rewards"][prize] = 1
                    tiers.setdefault(str(tier), e)
                athletes[key] = {"class": cls, "sport": sport, "tiers": tiers}
            here.append({"n": p["n"], "key": key, "second": s >= 5000})
        fields[str(z)] = {"arena": arena, "sport": sport, "athletes": here}
    visitors = []
    for k, tid in enumerate(VISITORS):
        e = ut.entry(r, tid)
        cls_id = utrainers.team(r, tid)["class_id"]
        _pic(r, e, cls_id, obj)
        nm = e["name"].replace("Pokémon ", "").replace("é", "e")
        e["name"] = nm
        e["rewards"] = {"balls": e["rewards"]["balls"], VISITOR_ITEMS.get(nm, "ULTRA_BALL"): 1}
        code = obj.get(cls_id) or WALK_EXTRA.get(nm.split()[0])
        visitors.append({"id": tid, "slot": k % 3, "walk": "b2_c%d.png" % code if code else None, "battle": e})
    out = {"_about": "Nimbasa's Big Stadium and Small Court, from Black 2's file: dev/builders/unova_sports.py (batch 4c)",
           "fields": fields, "athletes": athletes, "visitors": visitors, "schedule": SCHEDULE}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(len(athletes), "athletes,", len(visitors), "visitors ->", OUT)
    for k, a in sorted(athletes.items()):
        print(" ", k, {t: (e["levels"], {i: q for i, q in e["rewards"].items() if i != "balls"}) for t, e in sorted(a["tiers"].items())})
    pics = sorted({e["sprite"] for a in athletes.values() for e in a["tiers"].values()} | {v["battle"]["sprite"] for v in visitors})
    print("battle pictures missing:", [p for p in pics if not os.path.isfile(os.path.join(ut.SPRITES, p))])
    chars = os.path.join(ut.GAME, "assets", "dungeon", "characters")
    print("walking sheets missing:", sorted({v["walk"] for v in visitors if v["walk"] and not os.path.isfile(os.path.join(chars, v["walk"]))}))


if __name__ == "__main__":
    main()
