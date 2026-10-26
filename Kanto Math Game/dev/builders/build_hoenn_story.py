"""Hoenn's story beats as in Omega Ruby / Alpha Sapphire (oraswiki.com walkthrough, Quick Guides 1-22).

Opening: home in Littleroot (Birch isn't at his lab), Route 101 (Birch chased by a Poochyena: pick a
starter from his bag, then fight it), the lab (Birch says to meet his kid), the rival on Route 103,
the lab again (Pokedex and 10 Poke Balls), Route 102, then Petalburg: Norman, and Wally catching his
Ralts (an automatic scene with Wally's back sprite, src/states/hoenn.py WallyCatchState).

Then the walkthrough's gates and battles: the Devon errand before Mr. Briney's boat, Steven's Letter
before the ferry to Slateport, the museum before Route 110, Wally at the Mauville Gym (Rock Smash from
his uncle), the rival's Strength on Route 112, Meteor Falls before the Cable Car, Mt. Chimney before
Jagged Pass and Lavaridge, Castform and the rival (Fly) at the Weather Institute, the Devon Scope before
the Fortree Gym, the Lilycove rival before the Team Hideout, Wally before the League and the
post-credits rival on Route 103. Rival and Wally teams and levels are ORAS's (Bulbapedia).

Run from the game folder:  python dev/builders/build_hoenn_story.py
"""
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from textjson import TextJSON  # noqa: E402

CACHE = os.path.join(os.path.dirname(__file__), "bulbapedia_cache")


def fetch(title):
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9_.-]", "_", title) + ".txt")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    text = ""
    for _ in range(3):  # follow #REDIRECTs
        url = "https://bulbapedia.bulbagarden.net/w/index.php?" + urllib.parse.urlencode(
            {"title": title.replace(" ", "_"), "action": "raw"})
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (KantoMathGame story builder)"})
        text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
        time.sleep(1.0)
        m = re.match(r"#REDIRECT\s*\[\[([^\]#|]+)", text, re.I)
        if not m:
            break
        title = m.group(1)
    open(path, "w", encoding="utf-8").write(text)
    return text


def move_key(name):
    return re.sub(r"[^A-Z0-9-]", "", name.strip().upper().replace(" ", "-"))


def battles(text, section):
    """{battle heading: {player's starter or None: [(species, level, [moves])]}} from the party
    tables under `section` (e.g. "Pokémon Omega Ruby and Alpha Sapphire")."""
    start = re.search(r"\n(=+)" + re.escape(section) + r"=+\n", text)
    depth = len(start.group(1))
    body = text[start.end():]
    end = re.search(r"\n={%d}[^=]" % depth + "|\n={1,%d}[^=]" % (depth - 1), body)
    body = body[:end.start()] if end else body
    out, heading, party = {}, None, None
    for block in re.split(r"(?=\n={%d,}[^=\n]|\{\{Party\n|\{\{Pokémon\n)" % (depth + 1), body):
        h = re.match(r"\n=+([^=\n]+)=+", block)
        if h:
            heading = h.group(1).strip()
            continue
        if block.startswith("{{Party\n"):
            pick = re.search(r"PlayerChoice\|0*(\d+)", block)
            party = out.setdefault(heading, {}).setdefault(int(pick.group(1)) if pick else None, [])
        elif block.startswith("{{Pokémon\n") and party is not None:
            nd = int(re.search(r"ndex ?= ?(\d+)", block).group(1))
            lv = int(re.search(r"level ?= ?(\d+)", block).group(1))
            mv = [move_key(x) for x in re.findall(r"move\d ?= ?([^|\n]+)", block)]
            party.append((nd, lv, mv))
    return out


def rival_fields(party_by_choice):
    """team_choice, levels (the same for every starter) and movesets for a rival battle."""
    choice = {str(k): [n for n, _, _ in v] for k, v in party_by_choice.items()}
    first = next(iter(party_by_choice.values()))
    sets = {str(n): mv for v in party_by_choice.values() for n, _, mv in v if mv}
    return {"team": choice[str(next(iter(party_by_choice)))], "team_choice": choice,
            "levels": [lv for _, lv, _ in first], "movesets": sets}


ORAS = "Pokémon Omega Ruby and Alpha Sapphire"
brendan = battles(fetch("Brendan (game)"), ORAS)
wally = battles(fetch("Wally (game)"), ORAS)
RIVAL = {"name": "{rival_name}", "class": "RIVAL", "sprite": "{rival_character}", "is_boss_battle": True}
rival2 = rival_fields(brendan["Second battle"])
rival3 = rival_fields(brendan["Third battle"])
rival4 = rival_fields(brendan["Fourth battle"])
rival5 = rival_fields(brendan["Fifth battle"])
wally_mauville = wally["First battle"][None]
wally_vr = wally["Second battle"][None]

P = "assets/hoenn_area_data.json"
tj = TextJSON(P)
sp = tj.data()["STORY_PROGRESSION"]

# ---- REGION_START: the starter is chosen on Route 101; no catching before Birch's Pokedex ----
tj.set("HOENN", "starter_area", "HOENN_ROUTE_101")
tj.set("HOENN", "catch_flag", "received_pokedex_hoenn")

# ---- Text (GAME_TEXT: {team}-style tokens are filled in for the chosen version) ----
TEXT = {
    "hoenn_birch_intro": ["Professor Birch: Quick! My bag! There are Poke Balls in it!",
                          "Professor Birch: Pick one, any one, and help me out here!"],
    "hoenn_birch_starter": ["Professor Birch: Good choice! Now chase that Poochyena off!"],
    "hoenn_birch_lab": ["The lab is quiet. An aide looks up from her notes.",
                        "Aide: The Professor? He's out doing fieldwork on Route 101 again.",
                        "Aide: He says the best research happens in the tall grass, not behind a desk!"],
    "hoenn_rival_won": ["{rival_name}: Wow, you're good! No wonder Dad trusted you with a Pokemon.",
                        "{rival_name}: Let's head back to the lab. Dad will want to hear about this!"],
    "hoenn_devon_parts_stolen": ["A Devon researcher runs up to you, out of breath.",
                                 "Researcher: A {team} grunt stole our Devon Parts!",
                                 "Researcher: He ran east toward Rusturf Tunnel on Route 116. Please get them back!"],
    "hoenn_rusturf_won": ["The grunt gave back the Devon Parts... and Mr. Briney's Wingull, Peeko!",
                          "Peeko flew happily home to Mr. Briney. Take the Devon Parts back to Rustboro!"],
    "hoenn_woods_won": ["Grunt: Fine, keep your stupid papers!",
                        "Devon Researcher: Thank you! They wanted the papers for our new parts.",
                        "Devon Researcher: Please take this Exp. Share. It shares battle experience with your team!"],
    "hoenn_museum_stern": ["Dock: Captain Stern went to the Oceanic Museum to look at an exhibit.",
                           "Dock: Could you bring him the Devon Parts there?"],
}
for k, v in TEXT.items():
    tj.set("GAME_TEXT", k, v)

# ---- Part 1: Littleroot, Route 101, Oldale, Route 103, Petalburg ----
tj.set("LITTLEROOT_TOWN", "on_enter_event", None)  # the rival battle is on Route 103 now
explore = [o for o in sp["LITTLEROOT_TOWN"]["explore_options"] if o.get("target") != "hoenn_neighbor"]
explore.insert(1, {"text": "Visit Next Door", "action": "NPC", "target": "hoenn_neighbor"})
tj.set("LITTLEROOT_TOWN", "explore_options", explore)

tj.set("HOENN_ROUTE_101", "starter_event", {
    "lines": ["Help! Somebody, help me!",
              "A man is running in circles... a wild POOCHYENA is chasing him!",
              "Professor Birch: You there! Please help me!"],
    "boss": {"id": 261, "name": "Poochyena", "level": 2, "exact_level": True, "no_catch": True,
             "victory_flag": "hoenn_birch_rescued",
             "lines": ["The wild POOCHYENA turns to face you!"],
             "won": ["The POOCHYENA ran off into the tall grass!",
                     "Professor Birch: Whew... you saved me! I'm Birch, the Pokemon Professor.",
                     "Professor Birch: Come see me at my lab in Littleroot Town!"]}})

oldale = sp["OLDALE_TOWN"]
travel = [dict(o, condition="received_pokedex_hoenn") if o["target_area"] == "HOENN_ROUTE_102" else o
          for o in oldale["travel_options"]]
tj.set("OLDALE_TOWN", "travel_options", travel)
explore = [o for o in oldale["explore_options"] if o.get("target") not in ("oldale_clerk", "oldale_sketch_boy")]
explore += [{"text": "Poke Mart Clerk", "action": "NPC", "target": "oldale_clerk"},
            {"text": "Path to Route 102", "action": "NPC", "target": "oldale_sketch_boy",
             "condition": "not:received_pokedex_hoenn"}]
tj.set("OLDALE_TOWN", "explore_options", explore)

tj.set("HOENN_ROUTE_103", "on_enter_event", [
    {"type": "trainer_battle", "condition": "hoenn_birch_thanked", "flag_check": "hoenn_rival_103",
     "trainer": {"name": "{rival_name}", "class": "PKMN_TRAINER", "sprite": "{rival_character}",
                 "team": [258], "team_choice": {"252": [255], "255": [258], "258": [252]}, "levels": [5],
                 "rewards": {"balls": 0},
                 "dialogue": {"intro": "hoenn_rival_intro", "player_won": "hoenn_rival_won",
                              "player_lost": "hoenn_rival_lost"}}},
    {"type": "trainer_battle", "condition": "beat_hoenn_champion", "flag_check": "hoenn_rival_postgame",
     "trainer": dict(RIVAL, **rival5, mega=[257, 260, 254], rewards={"balls": 20, "RARE_CANDY": 3},
                     dialogue={"intro": ["{rival_name}: Champion! Before you go anywhere, one more battle.",
                                         "{rival_name}: My partner Mega Evolves now too. Ready?"],
                               "player_won": ["{rival_name}: You really are the best. I'm so glad you moved here!"],
                               "player_lost": ["{rival_name}: Ha! Even Champions can lose. Train some more!"]})}])

petal = sp["PETALBURG_CITY"]
tj.set("PETALBURG_CITY", "on_enter_event", {"type": "event", "event": "norman_wally",
                                            "condition": "received_pokedex_hoenn", "flag_check": "helped_wally"})
tj.set("PETALBURG_CITY", "explore_options", [
    {"text": "Talk to Dad", "action": "NPC", "target": "norman_petalburg"} if o.get("target") == "wally_tutorial"
    else o for o in petal["explore_options"]])


def pool_set(area, who, **changes):
    """Change the trainer `who` (its name or victory flag) in an area's trainer_pool (None removes
    a key)."""
    pool = sp[area]["trainer_pool"]
    t = next(t for t in pool if who in (t["name"], t.get("victory_flag")))
    for k, v in changes.items():
        if v is None:
            t.pop(k, None)
        else:
            t[k] = v
    tj.set(area, "trainer_pool", pool)


def menu_set(area, items, drop=()):
    """Add route_menu entries before the exits (replacing any with the same text)."""
    menu = [m for m in sp[area]["route_menu"] if m["text"] not in drop and m["text"] not in {i["text"] for i in items}]
    at = next((i for i, m in enumerate(menu) if m.get("action") == "EXIT"), len(menu))
    menu[at:at] = items
    sp[area]["route_menu"] = menu
    tj.set(area, "route_menu", menu)


def exit_condition(area, target, *conds):
    menu = sp[area]["route_menu"]
    for m in menu:
        if m.get("action") in ("EXIT", "TRAVEL") and (m.get("target_area") or m.get("target")) == target:
            have = m.get("condition")
            have = have if isinstance(have, list) else [have] if have else []
            m["condition"] = have + [c for c in conds if c not in have]
    tj.set(area, "route_menu", menu)


# ---- Part 2-3: Petalburg Woods, Rustboro, Rusturf Tunnel, Mr. Briney ----
pool_set("HOENN_PETALBURG_WOODS", "Team Aqua Grunt", villain="grunt", levels=[9],
         rewards={"balls": 5, "EXP_SHARE": 1}, dialogue={"player_won": "hoenn_woods_won"})
pool_set("HOENN_RUSTURF_TUNNEL", "Team Magma Grunt", villain="grunt", dialogue={"player_won": "hoenn_rusturf_won"})
exit_condition("HOENN_ROUTE_104", "DEWFORD_TOWN", "met_mr_stone")

# ---- Part 4: Dewford, Granite Cave (deliver the Letter; Steven doesn't battle here) ----
pool = [t for t in sp["HOENN_GRANITE_CAVE"]["trainer_pool"] if t["name"] != "Steven Stone"]
sp["HOENN_GRANITE_CAVE"]["trainer_pool"] = pool
tj.set("HOENN_GRANITE_CAVE", "trainer_pool", pool)
menu_set("HOENN_GRANITE_CAVE", [{"text": "TALK TO STEVEN", "action": "NPC", "target": "granite_steven",
                                 "condition": "not:met_steven", "color": "GOLD"}])
dew = sp["DEWFORD_TOWN"]
tj.set("DEWFORD_TOWN", "travel_options", [
    dict(o, condition=["has_knuckle_badge", "met_steven"]) if o["target_area"] == "SLATEPORT_CITY" else o
    for o in dew["travel_options"]])

# ---- Part 5: Slateport (the museum before Route 110), the rival on Route 110 ----
slate = sp["SLATEPORT_CITY"]
tj.set("SLATEPORT_CITY", "travel_options", [
    dict(o, condition="oceanic_museum_cleared") if o["target_area"] == "HOENN_ROUTE_110" else o
    for o in slate["travel_options"]])
pool_set("HOENN_ROUTE_110", "defeated_rival_110", name="{rival_name}", sprite="{rival_character}", **rival2,
         rewards={"balls": 10},
         dialogue={"intro": ["{rival_name}: {player_name}! Let's see how much you've grown!"],
                   "player_won": ["{rival_name}: You beat me again! Mauville City is just up ahead."],
                   "player_lost": ["{rival_name}: Ha! Better luck next time!"]})

# ---- Part 6: Mauville: Wally at the Gym door, then Wattson ----
tj.set("MAUVILLE_CITY", "on_enter_event", {"type": "event", "event": "wally_mauville",
                                           "condition": "helped_wally", "flag_check": "defeated_wally_mauville"})
gym = sp["MAUVILLE_CITY"]["gym"]
gym["requirements"] = dict(gym["requirements"], flags=["defeated_wally_mauville"])
tj.set("MAUVILLE_CITY", "gym", gym)

# ---- Part 7-9: Route 112 (Strength), Fiery Path, Meteor Falls, Mt. Chimney, Jagged Pass, Lavaridge ----
menu_set("HOENN_ROUTE_112", [{"text": "TALK TO YOUR RIVAL", "action": "NPC", "target": "rival_route112",
                              "condition": "not:got_strength_hoenn", "color": "GOLD"},
                             {"text": "CABLE CAR", "action": "EXIT", "target_area": "HOENN_MT_CHIMNEY",
                              "condition": ["can_exit", "meteor_falls_cleared"], "color": "RED"}])
exit_condition("HOENN_ROUTE_112", "LAVARIDGE_TOWN", "mt_chimney_boss_defeated")
exit_condition("HOENN_ROUTE_112", "HOENN_JAGGED_PASS", "mt_chimney_boss_defeated")
exit_condition("HOENN_FIERY_PATH", "HOENN_MT_CHIMNEY", "meteor_falls_cleared")
exit_condition("HOENN_ROUTE_111", "HOENN_ROUTE_113", "has_item:HM_STRENGTH")

# ---- Part 12-13: the Weather Institute (Castform), the rival on Route 119 (Fly), Fortree, Route 120 ----
menu_set("HOENN_WEATHER_INSTITUTE", [{"text": "TALK TO THE SCIENTISTS", "action": "NPC",
                                      "target": "weather_scientists",
                                      "condition": ["weather_institute_cleared", "not:got_castform"],
                                      "color": "GOLD"}])
tj.set("HOENN_ROUTE_119", "on_enter_event", {
    "type": "trainer_battle", "condition": "weather_institute_cleared", "flag_check": "hoenn_rival_119",
    "trainer": dict(RIVAL, **rival3, rewards={"balls": 10, "HM_FLY": 1},
                    dialogue={"intro": ["{rival_name}: You chased {team} out of the Weather Institute? Amazing!",
                                        "{rival_name}: Then show me how strong you've gotten!"],
                              "player_won": ["{rival_name}: Wow... Here, take this HM. Fly will take you anywhere!",
                                             "{rival_name}: Fortree City is just ahead. Good luck with Winona!"],
                              "player_lost": ["{rival_name}: Got you this time! Heal up and keep going."]})})
exit_condition("HOENN_ROUTE_119", "FORTREE_CITY", "hoenn_rival_119")
menu_set("HOENN_ROUTE_120", [{"text": "INVISIBLE POKEMON", "action": "BOSS", "color": "PURPLE",
                              "condition": ["has_item:DEVON_SCOPE", "not:route120_kecleon"],
                              "boss": {"id": 352, "name": "Kecleon", "victory_flag": "route120_kecleon",
                                       "lines": ["The Devon Scope reveals something on the bridge...",
                                                 "It's a Kecleon! It was hiding in plain sight!"]}}])
gym = sp["FORTREE_CITY"]["gym"]
gym["requirements"] = dict(gym["requirements"], flags=["got_starter_mega_stone"], fail_text=[
    "Something invisible is blocking the Gym door!",
    "Winona needs 5 Hoenn badges, and you'll need a way to see what's in the way.",
    "Steven was heading east to Route 120..."])
tj.set("FORTREE_CITY", "gym", gym)

# ---- Part 14: Lilycove: the rival, then the Team Hideout ----
tj.set("LILYCOVE_CITY", "on_enter_event", {
    "type": "trainer_battle", "condition": "got_mt_pyre_orb", "flag_check": "hoenn_rival_lilycove",
    "trainer": dict(RIVAL, **rival4, rewards={"balls": 10},
                    dialogue={"intro": ["{rival_name}: {player_name}! {team} is hiding out near Lilycove!",
                                        "{rival_name}: Before you go after them, battle me one more time!"],
                              "player_won": ["{rival_name}: You're ready. Their hideout is in the cove east of town!"],
                              "player_lost": ["{rival_name}: Not yet! Train a little more first."]})})
tj.set("LILYCOVE_CITY", "explore_options", [
    dict(o, condition="hoenn_rival_lilycove") if o.get("target_area") == "HOENN_TEAM_HIDEOUT" else o
    for o in sp["LILYCOVE_CITY"]["explore_options"]])

# ---- Part 21: Wally on Victory Road (ORAS team), before the League ----
pool_set("HOENN_VICTORY_ROAD", "Wally", team=[n for n, _, _ in wally_vr], levels=[lv for _, lv, _ in wally_vr],
         movesets={str(n): mv for n, _, mv in wally_vr if mv})
gym = sp["EVER_GRANDE_CITY"]["gym"]
gym["requirements"] = dict(gym["requirements"], flags=["defeated_wally_victory"], fail_text=[
    "The guards at the Pokemon League stop you.",
    "Only Trainers with all 8 Hoenn Badges who made it through Victory Road may enter!"])
tj.set("EVER_GRANDE_CITY", "gym", gym)

tj.save()
print("Wally at Mauville:", wally_mauville)
print("rival 110:", rival2["team_choice"], rival2["levels"])
print("Hoenn story written.")
