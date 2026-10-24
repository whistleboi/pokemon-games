"""Orre (Pokemon Colosseum, then XD): Phenac City, Pyrite Town, Agate Village, Realgam Tower, and after
Cipher falls, Gateon Port and the XD lairs. No wild Pokemon: snag every Shadow Pokemon from Colosseum and
XD (orre_shadows.py) with the Snag Machine. Shadow Pokemon are a variant: they stay Shadow unless you
choose to purify one at the Relic Stone. Jirachi after Cipher.
Run from the game folder: python dev/builders/build_orre.py dev/builders"""
import json
import os
import re
import sys

sys.path.insert(0, sys.argv[1])
from sublib import Sub, event, trainer, battle, boss  # noqa: E402
from textjson import TextJSON  # noqa: E402
from orre_shadows import SHADOW_LIST  # noqa: E402

S = Sub("ORRE", None, "ORRE", {})
SNAG = "has_item:SNAG_MACHINE"
names = json.load(open("assets/pokemon_names.json", encoding="utf-8"))

# Shadow forms: smart IDs 9301+ (dark sprites made below), one per species, from orre_shadows.py.
def _slug(name):
    return "".join(ch for ch in name.lower().replace(" ", "_") if ch.isalnum() or ch == "_")


def shadow_pool(area):
    """The Shadow Pokemon snagged in an area, in story order (one SNAG button fights the next one)."""
    return [{"id": sid, "name": f"Shadow {name}", "flag": f"snagged_shadow_{_slug(name)}", "trainer": tr}
            for sid, base, name, lv, a, game, tr in SHADOW_LIST if a == area]


def snag_button():
    return {"text": "SNAG SHADOW POKEMON", "action": "SNAG", "color": "PURPLE",
            "condition": [SNAG, "shadows_left"]}


HOME = {"text": "Air Transit to Hoenn (Lilycove)", "target_area": "LILYCOVE_CITY",
        "message": "The plane lifts off over the desert. Next stop: Lilycove City in Hoenn.", "long_ride": True}

# ---- 1. Phenac City: the oasis. Cipher attacks; Rui and the Snag Machine; Phenac Stadium.
S.town("PHENAC_CITY", "Phenac City", 60, [
    event("Trouble at the Fountain", {
        "lines": ["Men in strange uniforms are scaring people at the fountain!",
                  "Cipher Peon: Orre belongs to Cipher! Our Shadow Pokemon can't be stopped!"],
        "battle": battle("Cipher Peons", "CIPHER_PEON", "roughneck.png", [261, 285, 296], [58, 58, 60],
                         ["Peon: Retreat! Tell the admins a trainer with real Pokemon is here!"]),
        "flag": "phenac_cipher_beaten",
        "done": ["The fountain sparkles again. Phenac is safe, for now."]}),
    event("Meet Rui", {
        "requires": ["phenac_cipher_beaten"],
        "lines": ["Rui: You beat them! Did you see that dark aura? Those were Shadow Pokemon.",
                  "Cipher closes Pokemon's hearts so they only want to fight. It's so cruel!",
                  "Team Snagem left this machine behind when Cipher took over: a Snag Machine.",
                  "With it you can catch a Shadow Pokemon from a Cipher trainer and save it!",
                  "Take Shadow Pokemon to the Relic Stone in Agate Village to open their hearts."],
        "gift_item": {"SNAG_MACHINE": 1}, "flag": "got_snag_machine"},
        condition="phenac_cipher_beaten", flag_condition="not got_snag_machine"),
    {"text": "Phenac Stadium", "action": "GYM", "color": "GOLD"},
], local=[("Desert Trail", "ORRE_DESERT", None), ("Pyrite Town", "PYRITE_TOWN", "got_snag_machine"),
          ("Agate Village", "AGATE_VILLAGE", "cleared_the_under"),
          ("Realgam Tower", "REALGAM_TOWER", "met_agate_elder"),
          ("Gateon Port", "GATEON_PORT", "cipher_defeated")],
    extra_travel=[HOME], ships=False,
    gym={"trainers": [
        {"name": "Streetler Dax", "class": "STREETLER", "sprite": "roughneck.png", "team": [262, 302, 319],
         "levels": [59, 59, 60], "rewards": {"balls": 5}, "dialogue": {"intro": ["Round one at Phenac Stadium!"]}},
        {"name": "Civilian Mona", "class": "CIVILIAN", "sprite": "pokefan_f.png", "team": [184, 315, 357],
         "levels": [60, 60, 61], "rewards": {"balls": 5}, "dialogue": {"intro": ["The crowd is cheering for you!"]}}],
        "leader": {"name": "Pree Champion Justy", "class": "STADIUM_CHAMPION", "sprite": "acetrainer_m.png",
                   "is_boss_battle": True, "team": [184, 362, 373, 365], "levels": [62, 62, 63, 64],
                   "rewards": {"balls": 15}, "victory_flag": "phenac_stadium_won",
                   "dialogue": {"intro": ["Justy: The Phenac Stadium final! Show Orre a real battle!"],
                                "player_won": ["Justy: You're the Phenac Stadium champion!"],
                                "player_lost": ["Justy: The stadium is open every day. Come back!"]}},
        "requirements": {"badges": 0}})

S.wild("ORRE_DESERT", "Desert Trail", 60, "sand", {},
       [("Phenac City", "PHENAC_CITY"), ("Pyrite Town", "PYRITE_TOWN", "got_snag_machine")],
       [trainer("Rider Vex", "RIDER", "biker.png", [323, 332, 344]),
        trainer("Outlaw Rusty", "OUTLAW", "roughneck.png", [229, 262, 302])],
       extra=[event("RIDE THE MOTORBIKE", {
                  "lines": ["You rev the motorbike and race across the dunes.",
                            "Sand sprays behind you. Orre has no tall grass, only desert, rock and wind."]}),
              snag_button()],
       shadow_pool=shadow_pool("ORRE_DESERT"))

# ---- 2. Pyrite Town: outlaws, the Colosseum, and Cipher in The Under.
S.town("PYRITE_TOWN", "Pyrite Town", 63, [
    event("Pyrite's Sheriff", {
        "lines": ["Sheriff: Pyrite's a rough town, kid. Outlaws on every corner.",
                  "Lately Cipher's been running things from The Under, the old city below us.",
                  "Clear them out and Agate Village will want to meet you."]}),
    {"text": "Pyrite Colosseum", "action": "GYM", "color": "GOLD"},
], local=[("The Under", "THE_UNDER", None), ("Desert Trail", "ORRE_DESERT", None),
          ("Mt. Battle", "MT_BATTLE", None), ("Phenac City", "PHENAC_CITY", None)], ships=False,
    gym={"trainers": [
        {"name": "Thug Brock", "class": "THUG", "sprite": "roughneck.png", "team": [297, 302, 229],
         "levels": [62, 62, 63], "rewards": {"balls": 5}, "dialogue": {"intro": ["Welcome to Pyrite, punk!"]}},
        {"name": "Scrapper Kit", "class": "SCRAPPER", "sprite": "blackbelt.png", "team": [237, 308, 286],
         "levels": [63, 63, 64], "rewards": {"balls": 5}, "dialogue": {"intro": ["Nobody leaves the Colosseum easy!"]}}],
        "leader": {"name": "Miror B.", "class": "CIPHER_ADMIN", "sprite": "guitarist.png", "is_boss_battle": True,
                   "team": [272, 272, 272, 272], "levels": [64, 64, 65, 66], "rewards": {"balls": 15},
                   "victory_flag": "pyrite_colosseum_won",
                   "dialogue": {"intro": ["Miror B.: Ooh, a challenger! Let's dance! My Ludicolo never miss a beat!"],
                                "player_won": ["Miror B.: Aaah! My groove! You win this round, baby!"],
                                "player_lost": ["Miror B.: Ha! Keep dancing and come back!"]}},
        "requirements": {"badges": 0}})

S.wild("THE_UNDER", "The Under", 64, "indoor", {},
       [("Pyrite Town", "PYRITE_TOWN")],
       [trainer("Cipher Peon Litnar", "CIPHER_PEON", "roughneck.png", [262, 336, 342]),
        trainer("Cipher Peon Remil", "CIPHER_PEON", "biker.png", [229, 317, 302])],
       shadow_pool=shadow_pool("THE_UNDER"),
       extra=[snag_button(),
              event("SHUT DOWN THE UNDER", {
                  "lines": ["Cipher Admin Venus: How dare you march into my studio!",
                            "My Shadow Pokemon are beautiful, and you'll see how beautiful in battle!"],
                  "battle": battle("Cipher Admin Venus", "CIPHER_ADMIN", "beauty.png", [184, 350, 186, 36],
                                   [64, 65, 65, 66], ["Venus: My makeup... ruined! Fine, The Under is yours!"], balls=15),
                  "flag": "cleared_the_under"},
                  flag_condition="not cleared_the_under")])

# ---- Mt. Battle: 10 areas of 4 trainers, then Mt. Battle Master Vander. It can be climbed again and
# again, so purified Pokemon have battles to grow in (Jordan, 10-23).
import random as _r  # noqa: E402
_rng = _r.Random(1003)
_MON = [19, 21, 23, 27, 41, 52, 56, 58, 60, 66, 74, 77, 79, 81, 84, 86, 95, 98, 104, 109, 111, 114, 116, 120,
        123, 125, 126, 127, 128, 131, 133, 137, 142, 147, 163, 165, 167, 170, 177, 179, 183, 185, 190, 193,
        198, 200, 203, 204, 206, 207, 209, 211, 213, 214, 215, 216, 218, 220, 222, 223, 225, 227, 228, 231,
        234, 241, 246, 252, 255, 258, 261, 263, 270, 273, 276, 278, 280, 285, 287, 293, 296, 299, 300, 302,
        303, 304, 307, 309, 311, 312, 315, 318, 320, 322, 324, 325, 327, 328, 331, 333, 335, 336, 337, 338,
        339, 341, 343, 345, 347, 349, 351, 352, 353, 355, 357, 358, 359, 361, 363, 366, 369, 370, 371, 374]
_CLASSES = [("Cooltrainer", "COOLTRAINER", "acetrainer_m.png"), ("Cooltrainer", "COOLTRAINER", "acetrainer_f.png"),
            ("Bodybuilder", "BODYBUILDER", "blackbelt.png"), ("Hunter", "HUNTER", "hiker.png"),
            ("Rider", "RIDER", "biker.png"), ("Chaser", "CHASER", "roughneck.png"),
            ("Teacher", "TEACHER", "beauty.png"), ("Researcher", "RESEARCHER", "scientist.png")]
_NAMES = ["Kai", "Mira", "Dax", "Lena", "Rook", "Tess", "Oren", "Vale", "Juno", "Pike", "Sora", "Bram", "Nell",
          "Cyr", "Ivy", "Tor", "Esme", "Hale", "Rin", "Quill", "Lark", "Moss", "Faye", "Gil", "Sage", "Wren",
          "Ash", "Brin", "Cole", "Dina", "Ezra", "Fern", "Gale", "Holt", "Isla", "Jett", "Kira", "Lyle", "Maya", "Nash"]
_mt = []
for _area in range(1, 11):
    for _k in range(4):
        _title, _cls, _spr = _CLASSES[(_area * 4 + _k) % len(_CLASSES)]
        _size = 2 if _area <= 3 else 3 if _area <= 6 else 4 if _area <= 9 else 6
        _mt.append(trainer(f"Area {_area} {_title} {_NAMES[(_area - 1) * 4 + _k]}", _cls, _spr,
                           _rng.sample(_MON, _size), balls=3 if _area < 10 else 5,
                           is_boss_battle=_area == 10))
S.wild("MT_BATTLE", "Mt. Battle", 64, "field", {}, [("Pyrite Town", "PYRITE_TOWN")], _mt,
       extra=[event("MT. BATTLE MASTER", {
                  "lines": ["Mt. Battle Master Vander: You beat all ten areas? Then face the master of the mountain!"],
                  "battle": battle("Mt. Battle Master Vander", "MT_BATTLE_MASTER", "blackbelt.png",
                                   [289, 248, 373, 376, 230, 242], [70, 70, 71, 71, 72, 73],
                                   ["Vander: What a climb! You're the true master of Mt. Battle!"], balls=15),
                  "flag": "mt_battle_master_beaten"},
                  condition="not:has_trainers", flag_condition="not mt_battle_master_beaten"),
              event("START OVER FROM AREA 1", {
                  "lines": ["Mt. Battle's trainers are ready for another round. Back to Area 1!"],
                  "reset_area": True, "clear_flags": ["mt_battle_master_beaten"]},
                  condition="mt_battle_master_beaten")])
S.areas["MT_BATTLE"]["route_menu"][0]["text"] = "CLIMB MT. BATTLE"

# ---- 3. Agate Village: the elders, the Relic Stone, the Relic Forest.
S.town("AGATE_VILLAGE", "Agate Village", 64, [
    event("Village Elder", {
        "lines": ["Elder Eagun: So you're the trainer who saved Pyrite. Rui told me everything.",
                  "The Relic Stone in our forest can open a Shadow Pokemon's heart. Use it whenever you need.",
                  "Cipher's leader hides in Realgam Tower. When you're ready, end this."],
        "flag": "met_agate_elder"}),
    event("Purify at the Relic Stone", {
        "lines": ["Elder Eagun: The Relic Stone can open a Shadow Pokemon's heart, if you wish it.",
                  "Some trainers keep their Shadow Pokemon as they are. Choose one to purify, or none."],
        "purify": "choose"}),
], local=[("Relic Forest", "RELIC_FOREST", None), ("Phenac City", "PHENAC_CITY", None)], ships=False)

S.wild("RELIC_FOREST", "Relic Forest", 65, "forest", {},
       [("Agate Village", "AGATE_VILLAGE")],
       [trainer("Nomad Ilda", "NOMAD", "picnicker.png", [357, 315, 182]),
        trainer("Medium Sora", "MEDIUM", "medium.png", [354, 302, 200])],
       shadow_pool=shadow_pool("RELIC_FOREST"),
       extra=[snag_button(),
              event("THE WISHING STAR", {
                  "requires": ["cipher_defeated"],
                  "fail": ["The Relic Stone glows softly. The forest feels like it's waiting for something."],
                  "lines": ["Every Shadow Pokemon you saved gathers around the Relic Stone.",
                            "A shooting star falls into the forest... and a tiny Pokemon with a star on its head wakes up!",
                            "It's Jirachi, the Wish Pokemon. It looks at you, curious."],
                  "flag": "jirachi_awake"},
                  flag_condition="not jirachi_awake"),
              {"text": "MEET JIRACHI", "action": "BOSS", "color": "GOLD",
               "condition": ["jirachi_awake", "boss_not_defeated"]}],
       area_boss={"id": 385, "name": "Jirachi", "victory_flag": "orre_jirachi_caught"})

# ---- 4. Realgam Tower: the colosseum gauntlet and Cipher's command center.
S.town("REALGAM_TOWER", "Realgam Tower", 68, [
    {"text": "Realgam Colosseum (Cipher)", "action": "GYM", "color": "GOLD"},
], local=[("Cipher Command Center", "CIPHER_COMMAND", "cipher_defeated"), ("Phenac City", "PHENAC_CITY", None)],
    ships=False,
    gym={"trainers": [
        {"name": "Cipher Admin Dakim", "class": "CIPHER_ADMIN", "sprite": "blackbelt.png", "team": [232, 340, 62, 297],
         "levels": [66, 66, 67, 68], "rewards": {"balls": 8},
         "dialogue": {"intro": ["Dakim: Crush! I'll crush you and your Pokemon!"]}},
        {"name": "Cipher Admin Ein", "class": "CIPHER_ADMIN", "sprite": "scientist.png", "team": [376, 82, 289, 344],
         "levels": [67, 67, 68, 69], "rewards": {"balls": 8},
         "dialogue": {"intro": ["Ein: My research made the Shadow Pokemon. You will not undo it!"]}}],
        "leader": {"name": "Cipher Head Evice", "class": "CIPHER_BOSS", "sprite": "gentleman.png", "is_boss_battle": True,
                   "team": [248, 376, 373, 330, 334, 289], "levels": [70, 70, 71, 70, 70, 72],
                   "rewards": {"balls": 25, "RARE_CANDY": 5}, "victory_flag": "cipher_defeated",
                   "dialogue": {"intro": ["Evice: So you're the meddler. Realgam Tower is mine, and so is Orre!"],
                                "player_won": ["Evice: Impossible... Cipher is finished.",
                                               "Rui: You did it! Every Shadow Pokemon can be saved now!"],
                                "player_lost": ["Evice: Cipher cannot be beaten! Leave my tower!"]}},
        "requirements": {"badges": 0, "flag": "met_agate_elder",
                         "fail_text": "Realgam Tower's doors are sealed. Talk to the elder in Agate Village first."}})

S.wild("CIPHER_COMMAND", "Cipher Command Center", 70, "indoor", {},
       [("Realgam Tower", "REALGAM_TOWER")],
       shadow_pool=shadow_pool("CIPHER_COMMAND"),
       extra=[snag_button(),
              event("READ CIPHER'S FILES", {
                  "lines": ["The files list the Shadow Pokemon Cipher made here.",
                            "One note says: \"A wishing star fell near Agate's Relic Stone. Investigate.\"",
                            "Another: \"Project XD: ship the new Shadow Pokemon through Gateon Port.\""]})])

# ---- 5. XD: Gale of Darkness. Cipher regroups under Greevil; Gateon Port and its lairs.
S.town("GATEON_PORT", "Gateon Port", 66, [
    event("The Cipher Rumor", {
        "lines": ["Sailor: Cipher's back, they say. New Shadow Pokemon, and a ship nobody can find.",
                  "Start at their lab outside town. Then the ONBS building, the Key Lair... and Citadark Isle."]}),
], local=[("Cipher Lab", "XD_CIPHER_LAB", None), ("ONBS Building", "XD_ONBS", "xd_lovrina_beaten"),
          ("Cipher Key Lair", "XD_CIPHER_KEY_LAIR", "xd_exol_beaten"),
          ("Citadark Isle", "XD_CITADARK_ISLE", "xd_gorigan_beaten"), ("Phenac City", "PHENAC_CITY", None)],
    ships=False)


def xd_lair(key, name, level, battle_type, admin_text, admin, admin_flag):
    ev = {"lines": [admin_text], "battle": admin, "flag": admin_flag}
    S.wild(key, name, level, battle_type, {}, [("Gateon Port", "GATEON_PORT")],
           shadow_pool=shadow_pool(key),
           extra=[snag_button(), event(f"BATTLE {admin['name'].upper()}", ev, flag_condition=f"not {admin_flag}")])


xd_lair("XD_CIPHER_LAB", "Cipher Lab", 66, "indoor",
        "Cipher Admin Lovrina: You found my lab? My lovely Shadow Pokemon will deal with you!",
        battle("Cipher Admin Lovrina", "CIPHER_ADMIN", "beauty.png", [301, 315, 184], [65, 66, 67],
               ["Lovrina: Ugh! Fine, the ONBS building is next. Not that it'll help you!"], balls=12),
        "xd_lovrina_beaten")
xd_lair("XD_ONBS", "ONBS Building", 68, "indoor",
        "Cipher Commander Exol: The Orre news station is ours. Shadow Pokemon on every channel!",
        battle("Cipher Cmdr Exol", "CIPHER_ADMIN", "gentleman.png", [303, 359, 330], [67, 68, 69],
               ["Exol: Broadcast cut... The Key Lair in Pyrite holds the real secrets."], balls=12),
        "xd_exol_beaten")
xd_lair("XD_CIPHER_KEY_LAIR", "Cipher Key Lair", 70, "indoor",
        "Cipher Admin Gorigan: Here's where Cipher keeps its keys. You'll go no further!",
        battle("Cipher Admin Gorigan", "CIPHER_ADMIN", "blackbelt.png", [57, 97, 68, 62], [69, 69, 70, 70],
               ["Gorigan: The key... to Citadark Isle. Take it, then. Greevil is waiting."], balls=15),
        "xd_gorigan_beaten")
xd_lair("XD_CITADARK_ISLE", "Citadark Isle", 72, "field",
        "Grand Master Greevil: So you crossed the sea to my island. Cipher will rule Orre!",
        battle("Grand Master Greevil", "CIPHER_BOSS", "gentleman.png", [112, 103, 128, 373, 376],
               [71, 71, 72, 72, 73], ["Greevil: My Shadow Pokemon... my perfect plan... Cipher is finished!"],
               balls=25),
        "xd_greevil_beaten")

S.mission("orre_m1", "SIDE", "Welcome to Orre",
          "Cipher Peons are attacking Phenac City's fountain. Stop them and meet Rui.",
          {"flag_not": "got_snag_machine"}, "Snag Machine")
S.mission("orre_m2", "SIDE", "Pyrite and The Under",
          "Cipher runs Pyrite Town from The Under. Snag their Shadow Pokemon and beat Admin Venus.",
          {"flag": "got_snag_machine", "flag_not": "cleared_the_under"}, "The way to Agate")
S.mission("orre_m3", "SIDE", "Realgam Tower",
          "Purify your Shadow Pokemon at Agate's Relic Stone, then take down Cipher at Realgam Tower.",
          {"flag": "met_agate_elder", "flag_not": "cipher_defeated"}, "Orre is saved")
S.mission("orre_m4", "SIDE", "The Wishing Star",
          "Cipher's files mention a wishing star near Agate's Relic Stone.",
          {"flag": "cipher_defeated", "flag_not": "orre_jirachi_caught"}, "Jirachi")
S.mission("orre_m6", "SIDE", "Mt. Battle",
          "Climb Mt. Battle near Pyrite Town: 40 trainers in 10 areas, then Mt. Battle Master Vander. Climb again any time.",
          {"flag_not": "mt_battle_master_beaten"}, "Battle practice")
S.mission("orre_m5", "SIDE", "Gale of Darkness",
          "Cipher is back under Greevil. Clear the lairs from Gateon Port and stop him on Citadark Isle.",
          {"flag": "cipher_defeated", "flag_not": "xd_greevil_beaten"}, "Every Shadow Pokemon")

form_map = {str(sid): {"id": base, "form": "shadow", "name": f"Shadow {name}"}
            for sid, base, name, *_ in SHADOW_LIST}
S.save("assets/orre_area_data.json", extra={
    "REGION_START": {"ORRE": {"order": 3.5, "travel_only": True, "storage_region": "HOENN", "no_badges": True, "subtitle": "COLOSSEUM / ORRE",
                              "start_area": "PHENAC_CITY", "dex_range": [0, -1], "dex_extra": []}},
    "FORM_MAP": form_map})

# ---- Shadow art: a dark, purple-tinged version of each sprite.
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame  # noqa: E402

pygame.display.init()
pygame.display.set_mode((1, 1))


def shadow(r, g, b, a):
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    k = lum / 255
    return (int(40 + 90 * k), int(20 + 50 * k), int(70 + 120 * k), a)


SP = "assets/sprites/pokemon"
# Hand-made art that the tint must never overwrite: Jordan's Shadow Lugia (front) and its back sprite.
CUSTOM_ART = {f"{SP}/9424.png", f"{SP}/back/9424.png"}
made = 0
for sid, base, *_ in SHADOW_LIST:
    for d in (SP, f"{SP}/back", f"{SP}/shiny"):
        src = f"{d}/{base}.png"
        if f"{d}/{sid}.png" in CUSTOM_ART:
            continue
        if os.path.exists(src):
            img = pygame.image.load(src).convert_alpha()
            for x in range(img.get_width()):
                for y in range(img.get_height()):
                    c = img.get_at((x, y))
                    if c.a:
                        img.set_at((x, y), shadow(c.r, c.g, c.b, c.a))
            pygame.image.save(img, f"{d}/{sid}.png")
            made += 1
print("shadow sprites:", made)

# ---- Hoenn: air transit from Lilycove after the Hoenn title. Jirachi moves to Orre.
H = TextJSON("assets/hoenn_area_data.json")
if not any("Orre" in o.get("text", "") for o in H.data()["STORY_PROGRESSION"]["LILYCOVE_CITY"]["travel_options"]):
    H.append("LILYCOVE_CITY", "travel_options", {
        "text": "Air Transit to Orre", "target_area": "PHENAC_CITY", "condition": "beat_hoenn_champion",
        "message": "The plane flies far over the sea to the desert region of Orre. Next stop: Phenac City!"})
    H.save()
p = "assets/hoenn_area_data.json"
s = open(p, encoding="utf-8").read()
s2 = re.sub(r'(\"HOENN_SKY_PILLAR_PERCENTAGES\": \{[^}]*?), \"385\": 2', r"\1", s)
if s2 != s:
    open(p, "w", encoding="utf-8", newline="").write(s2)

K = TextJSON("assets/pokemon_area_data.json")
missing = [k for k in ["SNAG_MACHINE"] if k not in K.data()["GAME_CONFIG"]["KEY_ITEMS"]]
if missing:
    K.s = K.s.replace('    "KEY_ITEMS": [\n', '    "KEY_ITEMS": [\n      "SNAG_MACHINE",\n', 1)
    K.save()
g = open("src/core/game.py", encoding="utf-8").read()
if "orre_area_data.json" not in g:
    g = g.replace('            "sinjoh": "sinjoh_area_data.json",\n',
                  '            "sinjoh": "sinjoh_area_data.json",\n            "orre": "orre_area_data.json",\n')
    open("src/core/game.py", "w", encoding="utf-8", newline="").write(g)
print("ok")
