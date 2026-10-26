"""Galar and Paldea DLC accuracy: the Isle of Armor (Mustard, Kubfu, the Towers), the Crown Tundra
(Peony, the Galarian birds), the Teal Mask (Carmine, Kieran) and the Indigo Disk (Blueberry Academy,
the BB League, the Terarium, Terapagos). Zarude and Enamorus move to where they belong.
Run from the game folder: python build_dlc.py <scratchpad>"""
import re
import sys

sys.path.insert(0, sys.argv[1])
from sublib import Sub, event, trainer, battle, boss  # noqa: E402
from textjson import TextJSON  # noqa: E402

G = TextJSON("assets/galar_area_data.json")
gsp = G.data()["STORY_PROGRESSION"]

# ---- Isle of Armor: no Zarude (a movie Pokemon) and no wild Kubfu. Mustard's dojo gives Kubfu;
# the Towers of Two Fists evolve it into Single Strike or Rapid Strike Urshifu.
ioa = gsp["ISLE_OF_ARMOR"]
if ioa.get("area_boss", {}).get("id") == 893:
    G.remove("ISLE_OF_ARMOR", "area_boss")
    menu = [o for o in ioa["route_menu"] if o.get("action") != "BOSS"]
    exit_i = next(i for i, o in enumerate(menu) if o.get("action") == "EXIT")
    menu[exit_i:exit_i] = [
        event("MASTER DOJO", {
            "lines": ["Mustard: Welcome to the Master Dojo! I used to be the Galar Champion, you know.",
                      "My students Klara and Avery will test you first. Beat them both!"],
            "flag": "met_mustard", "done": ["Mustard: Keep training, my student!"]},
            flag_condition="not mustard_gave_kubfu"),
        event("DOJO TRIAL: KLARA", {
            "requires": ["met_mustard"],
            "lines": ["Klara: Ugh, a new student? I'll show you who's top of the dojo!"],
            "battle": battle("Klara", "DOJO_STUDENT", "lass.png", [2023, 110, 869], [66, 66, 68],
                             ["Klara: No way! I'll get you next time!"]),
            "flag": "beat_klara_dojo"}, condition="met_mustard", flag_condition="not beat_klara_dojo"),
        event("DOJO TRIAL: AVERY", {
            "requires": ["met_mustard"],
            "lines": ["Avery: Psychic power is the only true strength. Prepare yourself!"],
            "battle": battle("Avery", "DOJO_STUDENT", "psychic_m.png", [2030, 64, 856], [66, 66, 68],
                             ["Avery: Impossible... My mind was clouded."]),
            "flag": "beat_avery_dojo"}, condition="met_mustard", flag_condition="not beat_avery_dojo"),
        event("MUSTARD'S GIFT", {
            "requires": ["beat_klara_dojo", "beat_avery_dojo"],
            "lines": ["Mustard: You beat them both! You've earned my most precious partner.",
                      "This is Kubfu. Raise it well, then take it to one of the Towers of Two Fists."],
            "gift_pokemon": 891, "flag": "mustard_gave_kubfu"},
            condition="beat_avery_dojo", flag_condition="not mustard_gave_kubfu"),
        event("TOWER OF DARKNESS", {
            "requires": ["party_has:891"],
            "fail": ["The tower's door won't open. Mustard said only Kubfu can climb it."],
            "lines": ["Kubfu climbs the Tower of Darkness, floor by floor, and reads the scroll at the top..."],
            "evolve": {"891": 8004}}, condition="mustard_gave_kubfu"),
        event("TOWER OF WATERS", {
            "requires": ["party_has:891"],
            "fail": ["The tower's door won't open. Mustard said only Kubfu can climb it."],
            "lines": ["Kubfu climbs the Tower of Waters, floor by floor, and reads the scroll at the top..."],
            "evolve": {"891": 8005}}, condition="mustard_gave_kubfu"),
    ]
    G.set("ISLE_OF_ARMOR", "route_menu", menu)
    pool_key = ioa["wild_pool_percentages"]
    G.s, n = re.subn(r'("' + pool_key + r'": \{ )"891": 10, ', lambda mt: mt.group(1), G.s)
    list_key = pool_key.replace("_PERCENTAGES", "")
    G.s, m = re.subn(r'("' + list_key + r'": \[)891, ', lambda mt: mt.group(1), G.s)
    assert n == 1 and m == 1, "Isle of Armor pool layout changed"

# Zarude: to Glimwood Tangle (a jungle-like forest), after the Galar title. Same flag as before.
if not gsp["GLIMWOOD_TANGLE"].get("area_boss"):
    menu = list(gsp["GLIMWOOD_TANGLE"]["route_menu"])
    exit_i = next(i for i, o in enumerate(menu) if o.get("action") == "EXIT")
    menu.insert(exit_i, {"text": "Follow the Jungle Call", "action": "BOSS", "color": "GOLD",
                         "condition": ["beat_galar_champion", "boss_not_defeated"]})
    G.set("GLIMWOOD_TANGLE", "route_menu", menu)
    G.set("GLIMWOOD_TANGLE", "area_boss", {"id": 893, "name": "Zarude", "victory_flag": "GLIMWOOD_TANGLE_boss_defeated"})

# Crown Tundra: Peony's expedition, and the road to Dyna Tree Hill (the Galarian birds).
ct = gsp["CROWN_TUNDRA"]
if not any(o.get("text") == "PEONY'S EXPEDITION" for o in ct["route_menu"]):
    menu = list(ct["route_menu"])
    exit_i = next(i for i, o in enumerate(menu) if o.get("action") == "EXIT")
    menu[exit_i:exit_i] = [
        event("PEONY'S EXPEDITION", {
            "lines": ["Peony: Hey hey! I'm Peony, leader of the Peony Expedition Team!",
                      "Legends all over the Crown Tundra: a king who rules the harvest, giants in the ruins,",
                      "and three strange birds seen near the giant tree on Dyna Tree Hill!",
                      "Let's go find 'em all, eh?"],
            "flag": "met_peony"})]
    menu.append({"text": "DYNA TREE HILL", "action": "EXIT", "target_area": "DYNA_TREE_HILL",
                 "condition": "met_peony", "color": "RED"})
    G.set("CROWN_TUNDRA", "route_menu", menu)

# Enamorus and Hisui's space-time distortions are Legends: Arceus, so they move to Hisui.
std = gsp["SPACE_TIME_DISTORTION"]
if std.get("region") == "GALAR":
    G.set("SPACE_TIME_DISTORTION", "region", "SINNOH")
    G.set("SPACE_TIME_DISTORTION", "subregion", "HISUI")
    G.set("SPACE_TIME_DISTORTION", "route_menu",
          [dict(o, target_area="OBSIDIAN_FIELDLANDS", text="Obsidian Fieldlands") if o.get("action") == "EXIT" else o
           for o in std["route_menu"]])
    G.drop_where("SLUMBERING_WEALD", "route_menu", lambda o: o.get("target_area") == "SPACE_TIME_DISTORTION")
    G.drop_where("SLUMBERING_WEALD", "travel_options", lambda o: o.get("target_area") == "SPACE_TIME_DISTORTION")
G.save()

N = TextJSON("assets/sinnoh_area_data.json")
of = N.data()["STORY_PROGRESSION"]["OBSIDIAN_FIELDLANDS"]
if not any(o.get("target_area") == "SPACE_TIME_DISTORTION" for o in of.get("route_menu", [])):
    N.append("OBSIDIAN_FIELDLANDS", "route_menu", {"text": "Space-Time Distortion", "action": "EXIT",
                                                   "target_area": "SPACE_TIME_DISTORTION", "condition": "can_exit",
                                                   "color": "RED"})
    N.save()

# ---- Paldea: the Teal Mask's Carmine and Kieran; Ogerpon after the Loyal Three.
P = TextJSON("assets/paldea_area_data.json")
psp = P.data()["STORY_PROGRESSION"]
LOYAL = ["KITAKAMI_REVELERS_ROAD_boss_defeated", "KITAKAMI_PARADISE_BARRENS_boss_defeated",
         "KITAKAMI_TIMELESS_WOODS_boss_defeated"]
kt = psp["KITAKAMI"]
if not any(o.get("text") == "MEET CARMINE AND KIERAN" for o in kt["route_menu"]):
    menu = []
    for o in kt["route_menu"]:
        if o.get("action") == "BOSS":
            menu += [
                event("MEET CARMINE AND KIERAN", {
                    "lines": ["Carmine: You're the exchange student from Paldea? I'm Carmine. This is my little brother Kieran.",
                              "Kieran: Have you heard about the Loyal Three? They saved Kitakami from an ogre!",
                              "Kieran: ...I like the ogre better, though."],
                    "flag": "met_kitakami_rivals"}, flag_condition="not met_kitakami_rivals"),
                event("BATTLE CARMINE", {
                    "requires": ["met_kitakami_rivals"],
                    "lines": ["Carmine: Outsiders don't get to just wander around Kitakami. Battle me!"],
                    "battle": battle("Carmine", "KITAKAMI_TRAINER", "lass.png", [1013, 1011, 166, 291], [66, 66, 67, 68],
                                     ["Carmine: Hmph. Fine, you're not bad."]),
                    "flag": "beat_carmine_kitakami"}, condition="met_kitakami_rivals",
                    flag_condition="not beat_carmine_kitakami"),
                event("BATTLE KIERAN", {
                    "requires": LOYAL,
                    "fail": ["Kieran: I want to find the ogre... but first, the Loyal Three. Find all of them!"],
                    "lines": ["Kieran: You found the Loyal Three... and you met the ogre too, didn't you?",
                              "Kieran: I'll battle you for it!"],
                    "battle": battle("Kieran", "KITAKAMI_TRAINER", "school_kid_m.png", [1011, 1012, 1015, 1017], [67, 67, 68, 70],
                                     ["Kieran: ...I lost again. I'll get stronger. Just watch."]),
                    "flag": "beat_kieran_kitakami"}, condition="met_kitakami_rivals",
                    flag_condition="not beat_kieran_kitakami"),
                dict(o, condition=list(o["condition"]) + LOYAL)]
        else:
            menu.append(o)
    P.set("KITAKAMI", "route_menu", menu)

# Indigo Disk: Blueberry Academy after Kitakami; Terapagos only after the BB League.
if not any("Blueberry" in o.get("text", "") for o in psp["MESAGOZA"].get("travel_options", [])):
    P.append("MESAGOZA", "travel_options", {
        "text": "Exchange to Blueberry Academy", "target_area": "BLUEBERRY_ACADEMY",
        "condition": ["beat_paldea_champion", "KITAKAMI_boss_defeated"],
        "message": "You fly to Unova for your exchange term. Blueberry Academy floats far out at sea!"})
uz = psp["AREA_ZERO_UNDERDEPTHS"]
P.set("AREA_ZERO_UNDERDEPTHS", "route_menu",
      [dict(o, condition=["boss_not_defeated", "bb_league_champion", "briar_expedition"]) if o.get("action") == "BOSS"
       else o for o in uz["route_menu"]])
P.save()

# ---- New areas: Dyna Tree Hill (Galar), Blueberry Academy and the Terarium (Paldea's Indigo Disk).
S = Sub("GALAR", None, "DLC", {})
S.wild("DYNA_TREE_HILL", "Dyna Tree Hill", 68, "grass",
       {831: 10, 832: 6, 829: 12, 830: 6, 833: 10, 819: 12, 820: 6, 852: 10, 870: 4, 2024: 10, 875: 6, 862: 8},
       [("Crown Tundra", "CROWN_TUNDRA")],
       [trainer("Expedition Member Rae", "EXPEDITION", "hiker.png", [873, 820, 832])],
       extra=[boss("SEE GALARIAN ARTICUNO", 2027, "Galarian Articuno", 70, "dlc_galarian_articuno",
                   ["Something cold and graceful glides between the trees... Galarian Articuno!"],
                   ["Galarian Articuno vanishes in a flash of psychic light."], ["met_peony"], no_catch=False,
                   color="BLUE"),
              boss("SEE GALARIAN ZAPDOS", 2028, "Galarian Zapdos", 70, "dlc_galarian_zapdos",
                   ["Thundering footsteps! Galarian Zapdos sprints across the hill!"],
                   ["Galarian Zapdos dashes away over the hill."], ["met_peony"], no_catch=False, color="ORANGE"),
              boss("SEE GALARIAN MOLTRES", 2029, "Galarian Moltres", 70, "dlc_galarian_moltres",
                   ["The sky darkens. Galarian Moltres lands on the giant tree, burning with dark flames!"],
                   ["Galarian Moltres flies off into the clouds."], ["met_peony"], no_catch=False, color="PURPLE")])
S.region = "PALDEA"
S.town("BLUEBERRY_ACADEMY", "Blueberry Academy", 70, [
    event("Briar's Expedition", {
        "requires": ["bb_league_champion"],
        "fail": ["Briar: I'm planning an expedition deep into Area Zero... but only with the BB League Champion!"],
        "lines": ["Briar: You beat Kieran and the BB Elite Four! You're coming on my expedition.",
                  "There's something sleeping in the Area Zero Underdepths. The legend of Terapagos..."],
        "flag": "briar_expedition"}),
    {"text": "BB League", "action": "GYM", "color": "GOLD"},
], local=[("The Terarium", "TERARIUM", None)],
    extra_travel=[{"text": "Return to Mesagoza", "target_area": "MESAGOZA",
                   "message": "Your exchange term is over for now. You fly home to Paldea."}],
    ships=False,
    gym={"trainers": [
        {"name": "Crispin", "class": "BB_ELITE_FOUR", "sprite": "kindler.png", "team": [479, 663, 103, 323, 467, 257],
         "levels": [69, 69, 70, 70, 71, 72], "rewards": {"balls": 8}, "dialogue": {"intro": ["Crispin: Fire it up! Let's goooo!"]}},
        {"name": "Amarys", "class": "BB_ELITE_FOUR", "sprite": "acetrainer_f.png", "team": [227, 51, 212, 579, 395, 376],
         "levels": [70, 70, 71, 71, 72, 73], "rewards": {"balls": 8}, "dialogue": {"intro": ["Amarys: ...Let's get this over with."]}},
        {"name": "Lacey", "class": "BB_ELITE_FOUR", "sprite": "lass.png", "team": [547, 210, 730, 80, 869, 530],
         "levels": [71, 71, 72, 72, 73, 74], "rewards": {"balls": 8}, "dialogue": {"intro": ["Lacey: Battle rules! Let's play fair and have fun!"]}},
        {"name": "Drayton", "class": "BB_ELITE_FOUR", "sprite": "acetrainer_m.png", "team": [149, 330, 612, 254, 230, 1018],
         "levels": [72, 72, 73, 73, 74, 75], "rewards": {"balls": 8}, "dialogue": {"intro": ["Drayton: Eh, let's battle, I guess."]}}],
        "leader": {"name": "Kieran", "class": "BB_CHAMPION", "sprite": "school_kid_m.png", "is_boss_battle": True,
                   "team": [149, 186, 474, 861, 727, 1019], "levels": [75, 75, 76, 76, 76, 77],
                   "rewards": {"balls": 25, "RARE_CANDY": 5}, "victory_flag": "bb_league_champion",
                   "dialogue": {"intro": ["Kieran: I've been waiting for this. I'm the Champion now. I won't lose to you again!"],
                                "player_won": ["Kieran: ...You're still stronger. I get it now. Thanks for battling me."],
                                "player_lost": ["Kieran: See? I'm the strongest now!"]}},
        "requirements": {"badges": 0}})
S.wild("TERARIUM", "The Terarium", 70, "grass",
       {128: 8, 111: 6, 203: 6, 626: 6, 594: 6, 131: 4, 779: 6, 227: 6, 622: 6, 884: 4, 361: 6, 582: 6,
        974: 6, 1011: 6, 1019: 2, 1018: 2, 133: 6, 669: 8},
       [("Blueberry Academy", "BLUEBERRY_ACADEMY")],
       [trainer("BB Student Nova", "BB_STUDENT", "school_kid_f.png", [1018, 974, 669], balls=6),
        trainer("BB Student Rook", "BB_STUDENT", "school_kid_m.png", [884, 622, 626], balls=6)],
       extra=[event("THE FOUR BIOMES", {
           "lines": ["The Terarium is a giant dome under the sea with four biomes:",
                     "savanna, coastal, canyon and polar. Pokemon from all over the world live here!"]})])
S.mission("dlc_ioa", "SIDE", "The Isle of Armor",
          "Train at Mustard's Master Dojo, beat Klara and Avery, and climb a Tower of Two Fists with Kubfu.",
          {"flag": "beat_galar_champion", "flag_not": "mustard_gave_kubfu"}, "Kubfu")
S.missions[-1]["region"] = S.missions[-1]["condition"]["required_region"] = "GALAR"
S.mission("dlc_ct", "SIDE", "The Crown Tundra",
          "Join Peony's expedition: the King of Bountiful Harvests, the giants, and the Galarian birds on Dyna Tree Hill.",
          {"flag": "beat_galar_champion", "flag_not": "met_peony"}, "Galarian birds")
S.missions[-1]["region"] = S.missions[-1]["condition"]["required_region"] = "GALAR"
S.mission("dlc_id", "SIDE", "The Indigo Disk",
          "Go on exchange to Blueberry Academy, beat the BB League, and join Briar's expedition for Terapagos.",
          {"flag": "KITAKAMI_boss_defeated", "flag_not": "briar_expedition"}, "Terapagos")
S.save("assets/dlc_area_data.json")

g = open("src/core/game.py", encoding="utf-8").read()
if "dlc_area_data.json" not in g:
    g = g.replace('            "orre": "orre_area_data.json",\n',
                  '            "orre": "orre_area_data.json",\n            "dlc": "dlc_area_data.json",\n')
    open("src/core/game.py", "w", encoding="utf-8", newline="").write(g)
print("ok")
