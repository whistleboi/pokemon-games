"""Hyperspace Lumiose (Jordan, 11-06): a hub off Lumiose City (open after the 5th Gym, Clemont's Voltage
Badge) with a Donut Shop, and five themed dungeons, each three big open floors with trainers and wild
Pokemon of its theme, and Legends: Z-A's Mega Stones to win. You get in with a donut (src/world/donuts.py:
its taste picks the zone, its stars how far in you can go); src/states/overworld/hyperspace.py plays them.
Writes the areas and pools into assets/kalos_area_data.json and the recipes into assets/dungeon_routes.json,
as text (the files keep their own layout). Run once: a second run changes nothing.

    python dev/builders/build_hyperspace.py
"""
import json

HUB = "HYPERSPACE_LUMIOSE"
# key, name, style, level, taste, stars needed, wild {dex: %}, trainers [(name, class, sprite, team)], stones
DUNGEONS = [
    ("HYPERSPACE_VERDANT", "Verdant Rift", "hyper_verdant", 38, "SWEET", 0,
     {"153": 16, "70": 16, "544": 16, "651": 14, "670": 14, "35": 12, "682": 12},
     [("Ranger Mila", "PKMN_RANGER", "ranger_m.png", [153, 651]), ("Lass Aimee", "LASS", "lass.png", [670, 35]),
      ("Ace Trainer Rolf", "ACE_TRAINER", "acetrainer_m.png", [544, 70]),
      ("Ace Trainer Dalia", "ACE_TRAINER", "acetrainer_f.png", [682, 153, 651])],
     ["MEGANIUMITE", "VICTREEBELITE", "SCOLIPITE", "CHESNAUGHTITE", "FLOETTITE", "CLEFABLITE"]),
    ("HYPERSPACE_EMBER", "Ember Rift", "hyper_ember", 42, "SPICY", 0,
     {"499": 16, "667": 16, "654": 16, "529": 14, "701": 12, "559": 14, "322": 12},
     [("Hiker Bram", "HIKER", "hiker.png", [529, 322]), ("Veteran Coll", "VETERAN", "veteran.png", [499, 559]),
      ("Ace Trainer Jun", "ACE_TRAINER", "acetrainer_m.png", [667, 701]),
      ("Ace Trainer Odette", "ACE_TRAINER", "acetrainer_f.png", [654, 667, 499])],
     ["EMBOARITE", "PYROARITE", "DELPHOXITE", "EXCADRITE", "HAWLUCHANITE", "SCRAFTINITE"]),
    ("HYPERSPACE_TIDAL", "Tidal Rift", "hyper_tidal", 46, "SOUR", 1,
     {"159": 16, "120": 16, "657": 16, "688": 14, "690": 14, "686": 14, "279": 10},
     [("Swimmer Nils", "SWIMMER", "swimmer_m.png", [159, 120]), ("Swimmer Coralie", "SWIMMER", "swimmer_f.png", [690, 688]),
      ("Psychic Yann", "PSYCHIC", "psychic_m.png", [686, 121]),
      ("Ace Trainer Maelle", "ACE_TRAINER", "acetrainer_f.png", [657, 159, 690])],
     ["FERALIGITE", "STARMINITE", "GRENINJITE", "BARBARACITE", "DRAGALGITE", "MALAMARITE"]),
    ("HYPERSPACE_FROST", "Frost Rift", "hyper_frost", 50, "DRY", 2,
     {"361": 18, "608": 16, "712": 16, "227": 14, "780": 12, "459": 14, "355": 10},
     [("Skier Ines", "SKIER", "skier.png", [361, 712]), ("Psychic Lior", "PSYCHIC", "psychic.png", [608, 355]),
      ("Veteran Ysolde", "VETERAN", "veteranf.png", [227, 459]),
      ("Ace Trainer Pascal", "ACE_TRAINER", "acetrainer_m.png", [362, 609, 227])],
     ["FROSLASSITE", "CHANDELURITE", "SKARMORITE", "DRAMPANITE"]),
    ("HYPERSPACE_VOLT", "Voltage Core", "hyper_volt", 55, "BITTER", 3,
     {"148": 16, "603": 16, "870": 14, "705": 14, "694": 14, "707": 12, "125": 14},
     [("Scientist Remy", "SCIENTIST", "scientist.png", [603, 694]), ("Dragon Tamer Ada", "DRAGON_TAMER", "dragon_tamer.png", [148, 705]),
      ("Veteran Gael", "VETERAN", "veteran.png", [870, 707]),
      ("Ace Trainer Noor", "ACE_TRAINER", "acetrainer_f.png", [149, 604, 706])],
     ["DRAGONINITE", "EELEKTROSSITE", "FALINKSITE", "ZYGARDITE"]),
]
# the star berries lying in each zone: the next zone's taste (so each zone opens the way to the next)
STAR_BERRY = {"SWEET": "WATMEL_BERRY", "SPICY": "PINAP_BERRY", "SOUR": "BELUE_BERRY", "DRY": "NANAB_BERRY",
              "BITTER": "DURIN_BERRY"}
NEXT_TASTE = {"SWEET": "SPICY", "SPICY": "SOUR", "SOUR": "DRY", "DRY": "BITTER", "BITTER": "BITTER"}


def line(obj):
    return json.dumps(obj, ensure_ascii=False)


def newline_of(text):
    return "\r\n" if "\r\n" in text else "\n"


def main():
    p = "assets/kalos_area_data.json"
    text = open(p, encoding="utf-8", newline="").read()
    nl = newline_of(text)
    if f'"{HUB}"' in text:
        print("already there")
        return
    areas, pools = [], []
    for key, name, style, level, taste, stars, wild, trainers, stones in DUNGEONS:
        pools.append(f'  "{key}_PERCENTAGES": {line(wild)},')
        areas.append(f'    "{key}": ' + line({
            "area_type": "route", "route_name": f"Hyperspace: {name}", "region": "KALOS", "battle_type": "distortion",
            "level": level, "backgrounds": {"main": "lumiose_city.png"},
            "wild_pool_percentages": f"{key}_PERCENTAGES",
            "hyperspace": {"theme": name, "taste": taste, "stars": stars, "stones": stones, "seconds": 180,
                           "star_berry": STAR_BERRY[NEXT_TASTE[taste]]},
            "trainer_pool": [{"name": n, "class": c, "sprite": s, "team": t, "rewards": {"balls": 2}} for n, c, s, t in trainers],
            "route_menu": [{"text": "HYPERSPACE LUMIOSE", "action": "EXIT", "target_area": HUB, "condition": "can_exit"}],
            "next_area": HUB}) + ",")
    areas.insert(0, f'    "{HUB}": ' + line({
        "area_type": "town", "route_name": "Hyperspace Lumiose", "region": "KALOS",
        "backgrounds": {"main": "lumiose_city.png"},
        "explore_options": [{"text": "Donut Shop", "action": "DONUT", "color": "GOLD"},
                            {"text": "About Hyperspace", "action": "NPC", "target": "hyperspace_guide"}],
        "travel_options": [{"text": "Lumiose City", "target_area": "LUMIOSE_CITY"}]}) + ",")
    first = text.index(nl) + len(nl)
    text = text[:first] + nl.join(pools) + nl + text[first:]
    anchor = '"STORY_PROGRESSION": {' + nl
    i = text.index(anchor) + len(anchor)
    text = text[:i] + nl.join(areas) + nl + text[i:]
    opt = '{"text": "Route 13 (to Laverre)", "target_area": "KALOS_ROUTE_13", "condition": "has_plant_badge"}'
    assert text.count(opt) == 1
    text = text.replace(opt, opt + ", " + line({"text": "Hyperspace Lumiose", "target_area": HUB,
                                                "condition": "has_voltage_badge", "color": "GOLD"}))
    json.loads(text)
    open(p, "w", encoding="utf-8", newline="").write(text)

    p = "assets/dungeon_routes.json"
    text = open(p, encoding="utf-8", newline="").read()
    nl = newline_of(text)
    new = [f'  "{key}": ' + line({"floors": 3, "style": style, "size": [50, 30], "arena": True, "fog": False,
                                  "respawn": False, "wild": [6, 8],
                                  "loot": {"per_floor": [2, 3], "items": {STAR_BERRY[NEXT_TASTE[taste]]: 3, "POKE_BALLS": 2,
                                                                          "SUPER_POTION": 2}}}) + ","
           for key, name, style, level, taste, stars, wild, trainers, stones in DUNGEONS]
    anchor = '  "DEFAULT": {'
    i = text.index(anchor)
    text = text[:i] + nl.join(new) + nl + text[i:]
    json.loads(text)
    open(p, "w", encoding="utf-8", newline="").write(text)
    print("ok", [d[0] for d in DUNGEONS])


if __name__ == "__main__":
    main()
