"""Orre (Pokemon Colosseum): Phenac City, Pyrite Town, Agate Village, Realgam Tower. No wild Pokemon:
snag Shadow Pokemon from Cipher with the Snag Machine and purify them at the Relic Stone. Jirachi after.
Run from the game folder: python build_orre.py <scratchpad>"""
import json
import os
import re
import sys

sys.path.insert(0, sys.argv[1])
from sublib import Sub, event, trainer, battle, boss  # noqa: E402
from textjson import TextJSON  # noqa: E402

S = Sub("ORRE", None, "ORRE", {})
SNAG = "has_item:SNAG_MACHINE"
names = json.load(open("assets/pokemon_names.json", encoding="utf-8"))

# Shadow forms: smart IDs 9301+ (dark sprites made below). (sid, base, level)
SHADOWS = {"MAKUHITA": (9301, 296, 60), "TEDDIURSA": (9302, 216, 60), "HOUNDOUR": (9303, 228, 61),
           "BAYLEEF": (9304, 153, 62), "QUILAVA": (9305, 156, 62), "CROCONAW": (9306, 159, 62),
           "LEDIAN": (9307, 166, 63), "HITMONTOP": (9308, 237, 64), "URSARING": (9309, 217, 65),
           "SKARMORY": (9310, 227, 66), "SNORLAX": (9311, 143, 67), "TYRANITAR": (9312, 248, 70)}


def snag(key, who):
    sid, base, lv = SHADOWS[key]
    name = names[str(base)].title()
    return boss(f"SNAG SHADOW {key}", sid, f"Shadow {name}", lv, f"snagged_shadow_{key.lower()}",
                [f"{who} sends out a Shadow {name}! A dark aura surrounds it...",
                 "Weaken it, then throw a ball. The Snag Machine will catch it!"],
                [f"The Shadow {name} ran off into the desert..."],
                [SNAG], no_catch=False, color="PURPLE")


HOME = {"text": "Air Transit to Hoenn (Lilycove)", "target_area": "LILYCOVE_CITY",
        "message": "The plane lifts off over the desert. Next stop: Lilycove City in Hoenn."}

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
          ("Realgam Tower", "REALGAM_TOWER", "met_agate_elder")],
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
              snag("MAKUHITA", "Cipher Peon Folly"), snag("TEDDIURSA", "Cipher Peon Nore")])

# ---- 2. Pyrite Town: outlaws, the Colosseum, and Cipher in The Under.
S.town("PYRITE_TOWN", "Pyrite Town", 63, [
    event("Pyrite's Sheriff", {
        "lines": ["Sheriff: Pyrite's a rough town, kid. Outlaws on every corner.",
                  "Lately Cipher's been running things from The Under, the old city below us.",
                  "Clear them out and Agate Village will want to meet you."]}),
    {"text": "Pyrite Colosseum", "action": "GYM", "color": "GOLD"},
], local=[("The Under", "THE_UNDER", None), ("Desert Trail", "ORRE_DESERT", None),
          ("Phenac City", "PHENAC_CITY", None)], ships=False,
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
       extra=[snag("HOUNDOUR", "Cipher Peon Exinn"), snag("BAYLEEF", "Cipher Peon Verde"),
              snag("QUILAVA", "Cipher Peon Rosso"), snag("CROCONAW", "Cipher Peon Bluno"),
              event("SHUT DOWN THE UNDER", {
                  "lines": ["Cipher Admin Venus: How dare you march into my studio!",
                            "My Shadow Pokemon are beautiful, and you'll see how beautiful in battle!"],
                  "battle": battle("Cipher Admin Venus", "CIPHER_ADMIN", "beauty.png", [184, 350, 186, 36],
                                   [64, 65, 65, 66], ["Venus: My makeup... ruined! Fine, The Under is yours!"], balls=15),
                  "flag": "cleared_the_under"},
                  flag_condition="not cleared_the_under")])

# ---- 3. Agate Village: the elders, the Relic Stone, the Relic Forest.
S.town("AGATE_VILLAGE", "Agate Village", 64, [
    event("Village Elder", {
        "lines": ["Elder Eagun: So you're the trainer who saved Pyrite. Rui told me everything.",
                  "The Relic Stone in our forest can open a Shadow Pokemon's heart. Use it whenever you need.",
                  "Cipher's leader hides in Realgam Tower. When you're ready, end this."],
        "flag": "met_agate_elder"}),
    event("Purify at the Relic Stone", {
        "lines": ["You lead your Shadow Pokemon to the Relic Stone. A warm, gentle light fills the forest..."],
        "purify": True}),
], local=[("Relic Forest", "RELIC_FOREST", None), ("Phenac City", "PHENAC_CITY", None)], ships=False)

S.wild("RELIC_FOREST", "Relic Forest", 65, "forest", {},
       [("Agate Village", "AGATE_VILLAGE")],
       [trainer("Nomad Ilda", "NOMAD", "picnicker.png", [357, 315, 182]),
        trainer("Medium Sora", "MEDIUM", "medium.png", [354, 302, 200])],
       extra=[snag("LEDIAN", "Cipher Peon Kloak"), snag("HITMONTOP", "Cipher Admin Dakim's peon"),
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
       extra=[snag("URSARING", "a Cipher Peon guarding the lab"), snag("SKARMORY", "a Cipher Peon in the hangar"),
              snag("SNORLAX", "a Cipher Peon in the storeroom"), snag("TYRANITAR", "Evice's last guard"),
              event("READ CIPHER'S FILES", {
                  "lines": ["The files list every Shadow Pokemon Cipher made. You've found the last of them here.",
                            "One note says: \"A wishing star fell near Agate's Relic Stone. Investigate.\""]})])

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

form_map = {str(sid): {"id": base, "form": "shadow", "name": f"Shadow {names[str(base)].title()}"}
            for sid, base, _ in SHADOWS.values()}
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
made = 0
for sid, base, _ in SHADOWS.values():
    for d in (SP, f"{SP}/back", f"{SP}/shiny"):
        src = f"{d}/{base}.png"
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
