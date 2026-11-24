"""Hoenn re-audit batch H4 (11-23): canon fixes laid over the Emerald maps, after oras_fill and oras_extras.

Found by kanto_handoff/hoenn_rom_tools/hcanon.py (kanto_handoff/hoenn_check/CANON.md); Jordan's answers in
kanto_handoff/hoenn_check/DECISIONS.md. Kept here, one place, instead of hand edits in emerald.py (which hdrift.py would
have to carry): each entry names the area, the floor (or a town's room) and the tile.

- PEOPLE: someone (an area option, by its text; or a whole person dict) set on an open tile, as oras_fill does.
- HIDDEN: an item hidden on a tile (dungeon.py "hidden": stepped on / faced, the Itemfinder beeps).
- LISTS: a person who already stands there gets more to say, first come first: [new options..., what they had]. With two
  showing at once the player picks from a small menu (walk_town: a person that is a list).
The options themselves (texts, conditions, lines) are the area data's (hoenn_area_data.json / hoenn_oras.json).
- H4 items (11-23): the missing ORAS / Emerald item balls (PEOPLE, made by _ball: a "found" item stepped into once) and
  hidden items (HIDDEN), each on the tile its walkthrough line or Emerald's map gives. Routes 107, 129 and 130's seabed
  Plates, Orbs and shards are on their seabeds (H6, below).
- H6 seabeds (Jordan 11-24, DECISIONS #24): Routes 107, 129 and 130 get ORAS's seabeds, from the approved draft
  (kanto_handoff/hoenn_check/seabeds), written to dev/builders/data/h6_seabeds.json by
  kanto_handoff/hoenn_rom_tools/h_h6_seabeds.py: _seabeds() below.
- H7 people (Jordan 11-24, DECISIONS #25): Emerald's people still missing on Routes 109 and 110, in the Space Center and
  on Mt. Chimney (PEOPLE, SET); the Seashore House's five ORAS trainers moved inside off the beach (ROOM_TRAINERS) and the
  beach's Soda Pop ball taken away (DROP): _h7() below. The rooms themselves: hoenn_rom_tools/h_h7_rooms.py.
"""
import json
import os

from . import oras_fill as _F

SEABEDS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "h6_seabeds.json")

# Every ORAS Mega Stone obtainable (Jordan 11-23, DECISIONS #20): the stones that were area options with no spot.
# The post-Primal ones (ORAS: "after capturing or defeating Groudon / Kyogre") wait for cave_of_origin_cleared in the data.
PEOPLE = [
    ("LITTLEROOT_TOWN", None, None, 4, 18, "A Glinting Stone: Mewtwonite X"),   # (south-west of Birch's Lab)
    ("LAVARIDGE_TOWN", None, None, 6, 10, "A Glinting Stone: Houndoominite"),   # (by the sand baths)
    ("HOENN_ROUTE_110", 0, None, 29, 15, "MANECTITE"),                           # (east of the Cycling Road's north gate)
    ("HOENN_ROUTE_119", 0, None, 24, 131, "VENUSAURITE"),                        # (the southernmost long grass)
    ("HOENN_ROUTE_123", None, None, 6, 9, "ABOMASITE"),                          # (the Berry fields, west)
    ("HOENN_ROUTE_124", 0, None, 15, 75, "PINSIRITE"),                           # (the lone sandbar in the south-west)
    ("HOENN_PETALBURG_WOODS", None, None, 20, 10, "SCIZORITE"),                  # (past the Cut trees)
    ("HOENN_JAGGED_PASS", None, None, 21, 31, "TYRANITARITE"),                   # (by the southernmost grass)
    # ORAS: the Team grunt in the Oceanic Museum gives TM Thief (oras_fill had put him in Slateport's street as
    # "Team MagmaOR/AquaAS Grunt"; his option is taken out of hoenn_oras.json and stands here instead)
    ("HOENN_OCEANIC_MUSEUM", 0, None, 16, 3,
     {"text": "Bored grunt", "action": "EVENT", "flag_condition": "not oras_slateport_city_6",
      "event": {"lines": ["Grunt: Ugh, guarding a museum. Here, take this TM off my hands. I never use it anyway."],
                "gift_item": {"TM018": 1}, "flag": "oras_slateport_city_6"}}),
    # ORAS (H5, Dev Map clean-hoenn-main-reveal-glass-shop): Mauville's mirror shop owner gives the Reveal Glass once you
    # bring one of the forces of nature (Tornadus, Thundurus, Landorus: the Soaring storm cloud's); main's item and its form switch
    ("MAUVILLE_CITY", None, "shopper_house", 6, 3, [
        {"text": "Mirror shop owner", "action": "EVENT", "flag_condition": "not got_reveal_glass_hoenn",
         "condition": {"any": ["party_has:641", "party_has:642", "party_has:645"]},
         "event": {"lines": ["Mirror shop owner: Oh my! That Pokemon with you... it's one of the forces of nature!",
                             "Mirror shop owner: This old mirror is said to show such Pokemon's true form. It should be yours."],
                   "gift_item": {"REVEAL_GLASS": 1}, "flag": "got_reveal_glass_hoenn"}},
        {"text": "Mirror shop owner", "action": "EVENT",   # (only when the gift can't be given: two shown would be a menu)
         "condition": {"any": [["not:party_has:641", "not:party_has:642", "not:party_has:645"], "got_reveal_glass_hoenn"]},
         "event": {"lines": ["Mirror shop owner: Welcome! Mirrors of every shape. One of them is said to reveal the truth...",
                             "Mirror shop owner: ...but only to a Pokemon that commands the wind, the thunder or the land."]}}]),
]
TRAINERS = [   # (trainers in the area data with no spot on the map: set on open water near the route's others)
    ("HOENN_ROUTE_129", 0, 55, 25, "Scuba Diver Colten"),
    ("HOENN_ROUTE_129", 0, 70, 33, "Free Diver Coral"),
]
# Mauville (Jordan 11-23, #18): ORAS's Ultimate Move Studio and Pledge Move Dojo, in Mauville Hills (Emerald's Mauville has
# no mall); as every tutor now, they sell their moves as TMs (src/pokemon/tutors.py), at the TM's price as Johto's
PEOPLE += [
    ("MAUVILLE_CITY", None, "hills", 10, 5,
     {"text": "Ultimate Move tutor", "action": "EVENT",
      "event": {"lines": ["Tutor: The ultimate moves! Only a fully evolved first partner who loves its Trainer can learn one."],
                "tutor": {"choices": ["FRENZY-PLANT", "BLAST-BURN", "HYDRO-CANNON"], "min_friend": 220, "price": "tm"}}}),
    ("MAUVILLE_CITY", None, "hills", 12, 5,
     {"text": "Pledge tutor", "action": "EVENT",
      "event": {"lines": ["Tutor: Pledge moves! Fire, Water and Grass, each stronger together. Want to learn one?"],
                "tutor": {"choices": ["GRASS-PLEDGE", "FIRE-PLEDGE", "WATER-PLEDGE"], "price": "tm"}}}),
]
# Sootopolis (H5, Jordan #11): after the Cave of Origin Steven gives the Eon Flute (ORAS's timing), by the Center
PEOPLE += [("SOOTOPOLIS_CITY", None, None, 44, 33, "Steven")]
HIDDEN = [
    ("HOENN_GRANITE_CAVE", 1, 36, 11, "STEELIXITE"),   # (1F, the south side east of the big rock: hidden, as ORAS)
]


def _ball(item, text, flag, name):
    """An item ball: a "found" item you step into, once (the area data's found items, worded the same)."""
    return {"text": text, "action": "EVENT", "color": "GOLD", "found": True, "flag_condition": f"not {flag}",
            "event": {"lines": [f"You found {name}!"], "gift_item": {item: 1}, "flag": flag}}


# H4 items (11-23): the ORAS / Emerald item balls and hidden items hcanon.py found missing (CANON.md "item ball",
# "hidden item"). Each sits where ORAS's walkthrough says, or on Emerald's own tile when the check gives one.
PEOPLE += [
    # Magma Hideout (Emerald's tiles; the PP Max's own tile holds the Cameruptite, so it lies one step east)
    ("HOENN_MAGMA_HIDEOUT", 2, None, 21, 7, _ball("MAX_ELIXIR", "MAX ELIXIR far side", "got_h4_magma_max_elixir", "a Max Elixir")),
    ("HOENN_MAGMA_HIDEOUT", 4, None, 6, 9, _ball("PP_MAX", "PP MAX side room", "got_h4_magma_pp_max", "a PP Max")),
    # Route 107: on the beach by Dewford
    ("HOENN_ROUTE_107", None, None, 2, 12, _ball("SUPER_REPEL", "SUPER REPEL beach", "got_h4_r107_super_repel", "a Super Repel")),
    # Route 111: north-east of the south entrance
    ("HOENN_ROUTE_111", None, None, 23, 135, _ball("STARDUST", "STARDUST south", "got_h4_r111_stardust", "some Stardust")),
    # Route 123: south-west of Ace Trainer Julie
    ("HOENN_ROUTE_123", None, None, 133, 15, _ball("PP_UP", "PP UP east", "got_h4_r123_pp_up", "a PP Up")),
    # Route 134: the islet in the south-west
    ("HOENN_ROUTE_134", 0, None, 26, 29, _ball("HEART_SCALE", "HEART SCALE islet", "got_h4_r134_heart_scale", "a Heart Scale")),
    # Granite Cave: B2F's north side (Emerald's Repel and Rare Candy tiles), its south side (the TM by the big rock),
    # and the second Escape Rope east of Hiker Davian
    ("HOENN_GRANITE_CAVE", 3, None, 4, 4, _ball("REPEL", "REPEL north side", "got_h4_granite_repel", "a Repel")),
    ("HOENN_GRANITE_CAVE", 3, None, 29, 4, _ball("RARE_CANDY", "RARE CANDY north side", "got_h4_granite_rare_candy", "a Rare Candy")),
    ("HOENN_GRANITE_CAVE", 3, None, 14, 11, _ball("TM061", "TM061 SHADOW CLAW", "got_h4_granite_tm_shadow_claw", "TM Shadow Claw")),
    ("HOENN_GRANITE_CAVE", 0, None, 10, 7, _ball("ESCAPE_ROPE", "ESCAPE ROPE by the Hiker", "got_h4_granite_escape_rope", "an Escape Rope")),
    # Jagged Pass: south of Hiker Eric, on the middle slope
    ("HOENN_JAGGED_PASS", None, None, 19, 12, _ball("FULL_HEAL", "FULL HEAL slope", "got_h4_jagged_full_heal", "a Full Heal")),
]
HIDDEN += [
    # Pacifidlog: east of the south-east house's door
    ("PACIFIDLOG_TOWN", None, 14, 24, "HEART_SCALE"),
    # Route 106: the water's edge north-east of Fisherman Elliot
    ("HOENN_ROUTE_106", None, 59, 12, "POKE_BALLS"),
    # Route 109: north-west of Sailor Huey (the blue umbrella); the island south of the beach
    ("HOENN_ROUTE_109", None, 15, 11, "HEART_SCALE"),
    ("HOENN_ROUTE_109", None, 31, 30, "HEART_SCALE"),
    # Route 111: east of Picnicker Becky
    ("HOENN_ROUTE_111", None, 28, 132, "STARDUST"),
    # Route 116: the closed-off part by Rusturf Tunnel's east end
    ("HOENN_ROUTE_116", None, 72, 7, "BLACK_GLASSES"),
    # Route 123: north of Psychic Cameron
    ("HOENN_ROUTE_123", None, 30, 13, "PP_UP"),
    # Route 126, the seabed: bare spots in the seaweed
    ("HOENN_ROUTE_126", 1, 11, 4, "HEART_SCALE"),     # (northern area)
    ("HOENN_ROUTE_126", 1, 28, 4, "ULTRA_BALL"),      # (south-east of the north-west dive spot)
    ("HOENN_ROUTE_126", 1, 19, 16, "MIND_PLATE"),     # (the dead end north, then west, of the crater)
    ("HOENN_ROUTE_126", 1, 38, 12, "BIG_PEARL"),      # (north-north-west of the crater)
    ("HOENN_ROUTE_126", 1, 11, 34, "BLUE_SHARD"),     # (north of the western dive spot)
    ("HOENN_ROUTE_126", 1, 22, 60, "PEARL"),          # (the crater's south-west side)
    ("HOENN_ROUTE_126", 1, 37, 67, "STARDUST"),       # (just west of the way into Sootopolis)
    ("HOENN_ROUTE_126", 1, 64, 60, "YELLOW_SHARD"),   # (east-south-east of the crater)
    # Route 128: the sand ring's south side, the sandbar east of it, the south-central island; the Adamant Orb inside
    # the rocky ring by its north wall
    ("HOENN_ROUTE_128", 0, 59, 22, "HEART_SCALE"),
    ("HOENN_ROUTE_128", 0, 68, 26, "HEART_SCALE"),
    ("HOENN_ROUTE_128", 0, 47, 39, "HEART_SCALE"),
    ("HOENN_ROUTE_128", 0, 75, 13, "ADAMANT_ORB"),
    # Route 134: the largest island, east of the Carbos
    ("HOENN_ROUTE_134", 0, 52, 17, "HEART_SCALE"),
    ("HOENN_ROUTE_134", 0, 55, 14, "HEART_SCALE"),
    # Petalburg Woods: a break in the trees up north; the south-east corner below the ledge
    ("HOENN_PETALBURG_WOODS", None, 26, 6, "TINY_MUSHROOM"),
    ("HOENN_PETALBURG_WOODS", None, 44, 22, "TINY_MUSHROOM"),
    # Granite Cave: B1F's dead-end tunnel in the south and its east corner; B2F by the middle ladder, and the Everstone
    # inside the big rock (Emerald's own tile: walk into the rock)
    ("HOENN_GRANITE_CAVE", 2, 15, 22, "PARALYZE_HEAL"),
    ("HOENN_GRANITE_CAVE", 2, 29, 12, "X_DEFENSE"),
    ("HOENN_GRANITE_CAVE", 3, 13, 3, "SUPER_POTION"),
    ("HOENN_GRANITE_CAVE", 3, 15, 11, "EVERSTONE"),
    # Jagged Pass: between Expert Shelby and Hiker Eric
    ("HOENN_JAGGED_PASS", None, 15, 8, "FULL_HEAL"),
    # Shoal Cave: the Ice room's north-west corner (off the ice)
    ("HOENN_SHOAL_CAVE", 4, 4, 7, "ICE_HEAL"),
    # Cave of Origin: 1F north-east of the way down; B1F by the north stairs
    ("HOENN_CAVE_OF_ORIGIN", 1, 14, 16, "X_ATTACK"),
    ("HOENN_CAVE_OF_ORIGIN", 2, 11, 6, "REVIVE"),
]
PATCH = [   # (someone already on the map gets more to their event)
    # H5 (Jordan 11-23, DECISIONS #3): every HM from ORAS's giver, no more HMs on badges (src/world/hms.py)
    ("RUSTBORO_CITY", None, "cut_house", "Cutter",
     {"lines": ["That look in your eye, the way you move... you're a skilled Trainer, I can tell!",
                "Here, take this HM. A Pokemon that knows Cut can clear skinny trees. You'll need the Stone Badge to use it out here."],
      "gift_item": {"HM_CUT": 1}, "flag": "got_cut_hoenn",
      "done": ["Cutter: When Rustboro was growing, my Pokemon cut a path for every new house."]}),
    ("PETALBURG_CITY", None, "wally_home", "Wally's father",
     {"requires": ["has_balance_badge"],
      "fail": ["You're the one who went catching Pokemon with Wally! Thank you.",
               "He's been frail since he was a baby, so we sent him to stay with family in Verdanturf. The air there is cleaner."],
      "lines": ["You beat your father at his own Gym? Wally would be so proud of you.",
                "Please, take this. It's Surf: with it your Pokemon can carry you across the water."],
      "gift_item": {"HM_SURF": 1}, "flag": "got_surf_hoenn",
      "done": ["Wally's father: Wally writes to us about you. Go see the world!"]}),
    ("MOSSDEEP_CITY", None, "steven", "Steven",
     {"requires": ["has_mind_badge"],
      "fail": ["Steven: Mossdeep's Gym Leaders are twins. They battle as one. Win, and come and see me."],
      "lines": ["Steven: You beat Tate and Liza! Then you're ready for this. It's Dive: it takes your Pokemon down into the deep sea.",
                "Steven: The cavern under the sea between Mossdeep and Sootopolis... Dive down from Route 128, and be careful."],
      "gift_item": {"HM_DIVE": 1}, "flag": "got_dive_hoenn",
      "done": ["Steven: Dive down from Route 128. The cavern under the sea is where they've gone."]}),
    # Petalburg Woods: ORAS's Devon researcher gives the Exp. Share; ours retired it, so a Lucky Egg (as Kanto; #22)
    ("HOENN_PETALBURG_WOODS", None, None, "Devon researcher",
     {"lines": ["I came looking for Shroomish, and that thug came after my papers! Thank you for stepping in.",
                "Here, take this. A Pokemon holding it learns faster from every battle."],
      "gift_item": {"LUCKY_EGG": 1}, "flag": "got_lucky_egg_hoenn",
      "done": ["Devon researcher: Thanks again! I'll get these papers back to the company safe and sound."]}),
]
FLOOR_POOLS = [   # (a seabed with its own wild list: ORAS's Route 128 seaweed has Corsola, the shared underwater list doesn't)
    ("HOENN_ROUTE_128", 1, "HOENN_ROUTE_128_DIVE_PERCENTAGES"),
]
DOUBLES = [   # (a pair's person-event battles, written into emerald.py: real doubles, as every ORAS pair; #5)
    ("HOENN_ROUTE_111", "Interviewers Gabby & Ty"),
    ("HOENN_ROUTE_118", "Interviewers Gabby & Ty"),
]
LISTS = [
    # Granite Cave (H5): ORAS's Steven gives TM Steel Wing for the Letter (shown once the letter talk is done)
    ("HOENN_GRANITE_CAVE", 0, None, 7, 8, ["Steven's Steel Wing"]),
    # Rusturf Tunnel: Wanda's boyfriend digs out the Aggronite once the tunnel is cleared (ORAS)
    ("HOENN_RUSTURF_TUNNEL", None, None, 23, 5, ["AGGRONITE"]),
    # Littleroot: after the Delta Episode Mom has your version's Lati stone (ORAS: Latiasite in Omega Ruby, Latiosite in
    # Alpha Sapphire; the options' hoenn_version conditions pick)
    ("LITTLEROOT_TOWN", None, "home", 2, 6, ["Mom's news", "Mom", "Mom's Second Stone"]),   # (H5: Mom's news starts the Delta Episode)
]


# ---- H7 (Jordan 11-24, DECISIONS #25): Emerald's people still missing on the routes and in the caves, on Emerald's own
# tiles, in our own words (their looks: Emerald's sprite at the tile, dungeon_sprites.json "figures", written by
# kanto_handoff/hoenn_rom_tools/h_h7_data.py). The route buildings themselves (the Seashore House, the Cycling Road
# gates, the Safari Zone gate, Mt. Chimney's cable car station) are rooms in emerald.py (h_h7_rooms.py).
def _say(text, *lines, **more):
    return dict({"text": text, "action": "EVENT", "event": {"lines": list(lines)}}, **more)


_R110_GRUNTS = ["oceanic_museum_cleared", "not:mt_chimney_boss_defeated"]   # (as the three already there)
_INVASION = ["badge_mind_earned", "not:space_center_cleared"]                 # (as the Space Center's notice)
PEOPLE += [
    # Route 109: Mr. Briney at the end of the beach, where his boat ties up once he has sailed you to Slateport
    ("HOENN_ROUTE_109", None, None, 21, 24, _say("Mr. Briney", "Mr. Briney: Ahoy! Peeko and I tie up here when we bring folk to Slateport.",
                                                 "Mr. Briney: Fine sailing weather today, isn't it? Peeko loves a day at the beach!", condition="met_steven")),
    # Route 110: the low road's walkers, the Cycling Road's riders (on the deck, floor 1), its judge by the ramp, and the
    # two grunts the first three stood with
    ("HOENN_ROUTE_110", 0, None, 17, 90, _say("Undecided camper", "Race along the Cycling Road straight to Mauville, or stroll the low road under it? I can't decide!")),
    ("HOENN_ROUTE_110", 1, None, 29, 79, _say("Trick rider", "Learn a few Bike tricks and riding gets even more fun. Some places you can only reach with the right moves!")),
    ("HOENN_ROUTE_110", 0, None, 14, 69, _say("Strolling lady", "I don't have a Bike, so I'm taking a nice slow walk along the low road.")),
    ("HOENN_ROUTE_110", 1, None, 9, 57, _say("Bike fan", "Hey, that Bike's from Rydel's shop, isn't it? His name's right there on the frame!")),
    ("HOENN_ROUTE_110", 0, None, 10, 11, _say("Old man", "Two roads, one up above and one down below. One for people, one for Pokémon. Maybe that's how it should be.")),
    ("HOENN_ROUTE_110", 1, None, 27, 24, _say("Long-haired rider", "See how my hair streams out behind me when I ride? I grew it long just for that!")),
    ("HOENN_ROUTE_110", 0, None, 15, 7, _say("Boy", "Wouldn't it be great to zoom down the Cycling Road at full speed?")),
    ("HOENN_ROUTE_110", 0, None, 27, 92, _say("Cycling Road judge", "This is the Seaside Cycling Road! Ride from Slateport to Mauville as fast as you can, and try not to bump into anyone.")),
    ("HOENN_ROUTE_110", 0, None, 8, 83, _say("Rowdy grunt", "I can't wait to get to Slateport and stir up some trouble!", condition=_R110_GRUNTS)),
    ("HOENN_ROUTE_110", 0, None, 8, 82, _say("Silent grunt", "...Hmph. Keep walking, kid.", condition=_R110_GRUNTS)),
    # Mossdeep's Space Center: the two launch scientists on 1F; on 2F the grunt by the leader, while the team is inside
    ("HOENN_SPACE_CENTER", 0, None, 7, 2, _say("Launch scientist", "The next rocket launch is coming up soon! Every launch so far has gone up safely.")),
    ("HOENN_SPACE_CENTER", 0, None, 2, 2, _say("Launch engineer", "A rocket launch has to be perfect. Not even the tiniest mistake is allowed!")),
    ("HOENN_SPACE_CENTER", 1, None, 0, 8, _say("Fuel thief grunt", "Grunt: We came all this way for the rocket fuel, and you get in our way again!", condition=_INVASION)),
]
# (Mt. Chimney's south end: Emerald's other-team grunt stands where the Lava Cookie lady sells, until the fight is over;
# then she is back. The person on the tile becomes the pair, one at a time)
SET = [
    ("HOENN_MT_CHIMNEY", None, None, 19, 39, [
        _say("Worried grunt", "If they make more land, where will all the Water Pokémon live?", condition="not:mt_chimney_boss_defeated"),
        {"text": "Lava Cookie lady", "action": "SHOP", "stock": ["LAVA_COOKIE"], "condition": "mt_chimney_boss_defeated"}]),
]
# The Seashore House (ORAS: "battling all the Trainers in the building", six Soda Pop from Mr. Sea): the five ORAS
# trainers oras_fill stood on the beach go inside, on Emerald's three trainer tiles and two more of the room's; each one
# beaten sets its flag (hoenn_oras.json "victory_flag"), Mr. Sea's challenge counts them (h_h7_rooms.py MR_SEA)
ROOM_TRAINERS = [   # (area, room, [(name, x, y, how they move, the beach tile's own ground they leave)])
    ("HOENN_ROUTE_109", "seashore_house", [
        ("Sailor Dwayne", 2, 3, {"m": "face", "d": "d", "s": 2}, "="),
        ("Beauty Johanna", 10, 5, {"m": "look", "d": "lr", "s": 2}, "="),
        ("Delinquent Destinee", 4, 7, {"m": "face", "d": "d", "s": 2}, "="),
        ("Street Thug Blair", 12, 7, {"m": "face", "d": "l", "s": 2}, "="),
        ("Tuber Simon", 14, 9, {"m": "face", "d": "l", "s": 2}, "o")]),
]
DROP = [   # (someone oras_fill stood on a map who is now elsewhere: area, floor, text, the tile's own ground)
    ("HOENN_ROUTE_109", None, "SODA POP", "="),   # (ORAS's six Soda Pop are Mr. Sea's prize, not a ball on the beach)
]


def _h7(maps):
    for key, floor, room, x, y, people in SET:
        m = maps.get(key)
        p = _part(m, floor, room) if m else None
        i = _at(p, x, y) if p else None
        if i is None:
            print(ascii(f"  hoenn_canon: nobody stands on {key} {x},{y} to set"))
            continue
        p["people"][i] = list(people)
    for key, floor, text, ground in DROP:
        m = maps.get(key)
        p = _part(m, floor, None) if m else None
        if not p:
            continue
        spots = [(cx, cy) for cy, r in enumerate(p["art"]) for cx, c in enumerate(r) if c == "N"]
        ppl = list(p.get("people") or [])
        at = [n for n, q in enumerate(ppl) if (q if isinstance(q, str) else (q or {}).get("text") if isinstance(q, dict) else None) == text]
        if not at or at[0] >= len(spots):
            print(ascii(f"  hoenn_canon: no {text} on {key} to take away"))
            continue
        x, y = spots[at[0]]
        rows = [list(r) for r in p["art"]]
        rows[y][x] = ground
        p["art"] = ["".join(r) for r in rows]
        p["people"] = ppl[:at[0]] + ppl[at[0] + 1:]
        (p.get("moves") or {}).pop(f"{x},{y}", None)
    for key, room, moves in ROOM_TRAINERS:
        m = maps.get(key)
        if not m or room not in (m.get("rooms") or {}):
            continue
        f = _part(m, None, None)
        rows = [list(r) for r in f["art"]]
        spots = [(cx, cy) for cy, r in enumerate(rows) for cx, c in enumerate(r) if c == "X"]
        names = list(f.get("trainer_spots") or [])
        keep = []
        for xy, n in zip(spots, names):
            hit = next((t for t in moves if t[0] == n), None)
            if hit:
                rows[xy[1]][xy[0]] = hit[4]
                (f.get("moves") or {}).pop(f"{xy[0]},{xy[1]}", None)
            else:
                keep.append(n)
        left = {t[0] for t in moves} - set(names)
        if left:
            print(ascii(f"  hoenn_canon: {key}: not on the map to move inside: {sorted(left)}"))
        f["art"] = ["".join(r) for r in rows]
        f["trainer_spots"] = keep + names[len(spots):]
        _F._put(m["rooms"][room], "X", "trainer_spots", [[x, y, n, spec] for n, x, y, spec, _g in moves if n not in left])


def _slateport_sub(maps):
    """H5 (ORAS): two grunts hold you up at Slateport's harbour while the sub is stolen - Mightyena Lv 36, then Numel /
    Carvanha with Golbat Lv 34, by version (hoenn.py applies "team_by_version" to a villain's battle)."""
    m = maps.get("SLATEPORT_CITY")
    for sc in (m or {}).get("scenes") or []:
        cast = sc.get("cast") or []
        g = next((c for c in cast if ((c.get("event") or {}).get("battle") or {}).get("name") == "Team Grunt (harbour)"), None)
        if g is None or len(cast) > 2:
            continue
        b = g["event"]["battle"]
        b.update(team=[262], levels=[36], team_by_version={"OMEGA_RUBY": [262], "ALPHA_SAPPHIRE": [262]})
        import copy
        g2 = copy.deepcopy(g)
        g2["lines"] = ["Grunt: And me! You're not getting past either of us!"]
        g2["event"]["flag"] = "slateport_sub_grunt_2"
        g2["event"]["battle"].update(name="Team Grunt (harbour 2)", team=[322, 42], levels=[34, 34],
                                     team_by_version={"OMEGA_RUBY": [322, 42], "ALPHA_SAPPHIRE": [318, 42]})
        g2["event"]["battle"]["dialogue"] = {"player_won": ["Grunt: Too late! The sub's already gone!"]}
        b["dialogue"] = {"player_won": ["Grunt: Hmph. My partner will deal with you!"]}
        cast.append(g2)


def _museum_queue(maps):
    """H5 (hoenn_gates #14): the Grunts' queue reaches the Oceanic Museum's door, as Emerald's (its head stands below the
    door at 31,27); ours stopped at x 29, so row 27 let you walk round it and in before seeing the Shipyard."""
    m = maps.get("SLATEPORT_CITY")
    bar = (m or {}).get("barred") or []
    like = next((b for b in bar if "butt in" in str(b.get("lines"))), None)
    if like is None:
        return
    import copy
    taken = {tuple(t) for b in bar for t in b.get("tiles") or []}
    for (x, y), line in (((30, 27), "Grunt: The Boss said wait for the signal. So I'm waiting. In line."),
                         ((31, 27), "Grunt: First in line! Nobody gets in before me!")):
        if (x, y) not in taken:
            b = copy.deepcopy(like)
            b.update(tiles=[[x, y]], face="u", lines=[line])
            bar.append(b)


def _home_tv(maps):
    """Dev Map clean-hoenn-main-swarm-tv: the TV in your house (Emerald's, at 4,4 in the picture) tells today's mass outbreak
    once there is one (swarms.SWARMS["HOENN"], after the Hall of Fame); otherwise it's just the TV."""
    m = maps.get("LITTLEROOT_TOWN")
    room = ((m or {}).get("rooms") or {}).get("home")
    if not room or "!" in "".join(room["art"]):
        return
    row = room["art"][4]
    room["art"][4] = row[:4] + "!" + row[5:]
    room["signs"] = [["The TV's on. A cooking show... Mom's favourite."]]
    room["sign_events"] = {"4,4": {"text": "TV", "action": "EVENT",
                                   "event": {"swarm_news": "HOENN", "lines": ["The TV's on. A cooking show... Mom's favourite."]}}}


def _emerald_paths(maps):
    """H7 layout review (Jordan 11-24): ground you can walk in Emerald that was wall in ours.
    - Routes 111 and 115: the mountain tops past Emerald's muddy slopes ('7': up them on the Bicycle) - "a bike path up to
      the mountaintop";
    - Rustboro: the path along the south-east fence, "a walk path from the route to the south": it meets Route 104's top
      edge at x 33 (Emerald's map join), so both maps get that edge tile.
    The tiles come from hlayout_review (Emerald open and reachable, ours wall): dev/builders/data/h7_emerald_paths.json."""
    import os as _os
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data", "h7_emerald_paths.json")
    tiles = json.load(open(p, encoding="utf-8"))
    for key, spots in tiles.items():
        m = maps.get(key)
        if not m:
            continue
        part = m["floors"][0] if m.get("floors") else m
        art = [list(r) for r in part["art"]]
        for x, y in spots:
            if art[y][x] == "c":
                art[y][x] = "."
        part["art"] = ["".join(r) for r in art]
    for key, (x, y), ch, other, to in (("RUSTBORO_CITY", (33, 59), "v", "HOENN_ROUTE_104", (33, 0)),
                                       ("HOENN_ROUTE_104", (33, 0), "^", "RUSTBORO_CITY", (33, 59))):
        m = maps.get(key)
        if not m:
            continue
        part = m["floors"][0] if m.get("floors") else m
        if part.get("exits", {}).get(ch) != other:
            print(ascii(f"  hoenn_canon: {key} has no {ch!r} exit to {other}: path link left out"))
            continue
        row = list(part["art"][y])
        row[x] = ch
        part["art"][y] = "".join(row)
        part.setdefault("edge_to", {})[f"{x},{y}"] = list(to)
        if key == "RUSTBORO_CITY":
            part["split"] = True   # (the path is its own part, fenced off from the town: reached from Route 104 only, as in Emerald)


# Lavaridge Gym (Emerald 4.1 / 4.2): a warp there is two-way only as a place to land. On 1F only the sand pits drop you
# (behaviour 0x68), on B1F only the vents send you up (0x29); the rest of the warps are where the other floor's pit or
# vent sets you down. Found by the Hoenn playthrough (H8, 11-24): the tile inside the door (13,17) dropped you straight to
# B1F, onto a Kindler. Read from em/4_1.json and em/4_2.json (tile [3] = behaviour).
_LAVARIDGE_LANDINGS = {"gym": [(3, 6), (4, 16), (4, 18), (13, 17)],
                       "gym_2": [(2, 15), (3, 10), (3, 14), (5, 2), (5, 6), (5, 9), (8, 6), (10, 6), (14, 6)]}
_LAVARIDGE_SOLID = {("gym", 4, 16)}   # (Emerald's collision bit: solid)


def _lavaridge_pads(maps):
    rooms = (maps.get("LAVARIDGE_TOWN") or {}).get("rooms") or {}
    for name, spots in _LAVARIDGE_LANDINGS.items():
        r = rooms.get(name)
        if not r:
            continue
        art = [list(row) for row in r["art"]]
        for x, y in spots:
            r.get("links", {}).pop(f"{x},{y}", None)
            if art[y][x] == "1":
                art[y][x] = "c" if (name, x, y) in _LAVARIDGE_SOLID else "."
        r["art"] = ["".join(row) for row in art]


def _route110_grunts(maps):
    """H8 (11-24, the Hoenn playthrough): the five grunts on Route 110 after the Museum stood across the walking path north
    (x 7-10, rows 82-83), so without the Bicycle there was no way to Mauville. They stand in a file along the west wall
    now (the same order, so each keeps their words), looking at the path."""
    m = maps.get("HOENN_ROUTE_110")
    if not m or not m.get("floors"):
        return
    f = m["floors"][0]
    old = [(8, 82), (7, 83), (8, 83), (9, 83), (10, 83)]
    new = [(7, 80), (7, 81), (7, 82), (7, 83), (7, 84)]
    art = [list(r) for r in f["art"]]
    if any(art[y][x] != "N" for x, y in old) or any(art[y][x] not in ".N" for x, y in new):
        print("  hoenn_canon: Route 110's grunts are not where they were: left as they are")
        return
    for x, y in old:
        art[y][x] = "."
    for x, y in new:
        art[y][x] = "N"
    f["art"] = ["".join(r) for r in art]
    mv = f.setdefault("moves", {})
    for x, y in old:
        mv.pop(f"{x},{y}", None)
    for x, y in new:
        mv[f"{x},{y}"] = {"m": "face", "d": "r"}


def _slateport_dock(maps):
    """H8 (11-24): the Grunts' queue at the Oceanic Museum steps aside once you have been to the Shipyard
    (slateport_saw_dock, as ORAS: Captain Stern isn't there, he's at the Museum), but nothing set that flag, so the Museum
    could never be entered. Dock tells you, as you come in, and sets it."""
    r = ((maps.get("SLATEPORT_CITY") or {}).get("rooms") or {}).get("shipyard")
    if not r:
        return
    r.setdefault("scenes", []).append(
        {"who": "Dock", "trigger": "enter", "condition": "not:oceanic_museum_cleared", "flag": "slateport_saw_dock",
         "lines": ["Dock: Captain Stern? He went over to the Oceanic Museum.",
                   "Dock: There's a long line of strange-looking people outside it, though. Take care!"]})


def _rusturf_west(maps):
    """H8 (11-24): Rusturf Tunnel has two ways in from Route 116; the thief with the Devon Parts is in the west half (its
    rocks shut the east half off till Rock Smash). The Journal's Devon Parts mission leads to the west way in, then to the
    thief: this shout, as you reach the west half, marks that you're there (rusturf_west_reached)."""
    m = maps.get("HOENN_RUSTURF_TUNNEL")
    if not m:
        return
    part = m["floors"][0] if m.get("floors") else m
    part.setdefault("scenes", []).append(
        {"trigger": {"zone": [3, 1, 23, 10]}, "condition": "not:rusturf_rescued", "flag": "rusturf_west_reached", "cast": [],
         "call": ["Grunt: Hey! Don't come any closer! These Devon Parts are mine now!"]})


_STRAYS = [("RUSTBORO_CITY", "devon", (14, 0)), ("SOOTOPOLIS_CITY", "gym_2", (11, 21)),
           ("HOENN_ROUTE_112", None, (11, 35))]   # (None: the map itself: above Fiery Path's mouth)


def _stray_tiles(maps):
    """H8 (11-24): a lone floor tile beside a room's stairs, with nothing else round it, is where you came down: Devon's
    1F (14,0) above its stairs, Sootopolis Gym B1F (11,21) above its way up - stuck there, no way to walk on. Wall."""
    for key, room, (x, y) in _STRAYS:
        m = maps.get(key) or {}
        r = (m.get("rooms") or {}).get(room) if room else ((m.get("floors") or [m])[0] if m else None)
        if r and r["art"][y][x] == ".":
            row = list(r["art"][y])
            row[x] = "c"
            r["art"][y] = "".join(row)


def _r112_cable_side(maps):
    """H8 (11-24): Route 112's Cable Car stands on its south side; its north end (Jagged Pass, the way down from Route
    111's north) joins it only through Fiery Path. Coming back from Meteor Falls you are on the north end, so the
    Journal's Mt. Chimney mission leads through Fiery Path first, till you're on the south side (this flag)."""
    m = maps.get("HOENN_ROUTE_112")
    if not m:
        return
    part = m["floors"][0] if m.get("floors") else m
    part.setdefault("scenes", []).append(
        {"trigger": {"zone": [0, 20, 39, 59]}, "condition": "meteor_falls_cleared", "flag": "r112_cable_side", "cast": []})


def _fortree_gym_side(maps):
    """H8 (11-24): Fortree's ground is in parts joined by the tree-top walkways (FORTREE_CITY_UPPER); Winona's Gym stands
    in the part under the ladder at 25,6. The Journal's Feather Badge mission leads to that ladder on the walkways till
    you're down beside the Gym (this flag)."""
    m = maps.get("FORTREE_CITY")
    if m:
        m.setdefault("scenes", []).append({"trigger": {"zone": [17, 7, 26, 13]}, "flag": "fortree_gym_side", "cast": []})
        m["scenes"].append({"trigger": {"zone": [32, 7, 39, 10]}, "flag": "fortree_east_side", "cast": []})   # (the part by the way east, to Route 120)


def _sootopolis_wallace(maps):
    """H8 (11-24): Wallace stands in the Cave of Origin's mouth till you've met him (his scene as you come into
    Sootopolis); once the cave is cleared he is never in the way, whichever way you came (else, out of the cave, you are
    shut in on its doorstep)."""
    for b in (maps.get("SOOTOPOLIS_CITY") or {}).get("barred") or []:
        if [31, 17] in b.get("tiles", []) and (b.get("until") or {}).get("flag_condition") == "sootopolis_wallace_met":
            b.pop("until")
            b["until_any"] = [{"flag_condition": "sootopolis_wallace_met"}, {"flag_condition": "cave_of_origin_cleared"}]


def _seafloor_lookout(maps):
    """H8 (11-24): the Seafloor Cavern's lookout stood in the only way on (the passage at 10,1), with nothing to do but
    talk - so the cavern couldn't be crossed. He battles you now, and is gone once beaten (the team's Lv 36-38, as the
    cavern's own grunts)."""
    m = maps.get("HOENN_SEAFLOOR_CAVERN")
    f = (m or {}).get("floors", [None])[0] if m else None
    for p in (f or {}).get("people") or []:
        if isinstance(p, dict) and p.get("text") == "Lookout grunt":
            p["condition"] = ["not:seafloor_cavern_cleared", "not:seafloor_lookout_beaten"]
            p["event"] = {"lines": ["Hey! How did you get down here without a sub?!", "Nobody gets past me!"],
                          "flag": "seafloor_lookout_beaten",
                          "battle": {"name": "Team Grunt (lookout)", "class": "ROCKET", "villain": "grunt",
                                     "sprite": "magma_grunt.png", "team": [262, 42], "levels": [36, 38], "rewards": {"balls": 3},
                                     "team_by_version": {"OMEGA_RUBY": [262, 324], "ALPHA_SAPPHIRE": [262, 319]},
                                     "dialogue": {"player_won": ["Grunt: Gah! Fine, go on in... The Boss will finish you!"]}}}


def _part(m, floor, room):
    if room:
        return m["rooms"][room]
    if floor is not None and m.get("floors"):
        return m["floors"][floor]
    return m


def _at(part, x, y):
    """The index in the part's people list of the person on (x, y) (people go to the N tiles in reading order)."""
    spots = [(cx, cy) for cy, r in enumerate(part["art"]) for cx, c in enumerate(r) if c == "N"]
    return spots.index((x, y)) if (x, y) in spots else None


def _seabeds(maps):
    """H6: each of Routes 107, 129 and 130 becomes two floors, the sea and its seabed (ORAS's own size and shape, in
    Emerald's seabed tiles). On the sea: ORAS's dark dive patches (":"), its dive links (each patch to its own sunlit patch
    below: dungeon.py's "dive_links"), its own picture with the patches drawn in, and Route 129's Big Pearl and Heart
    Scale on its south-middle island. The seven divers move down to their ORAS tiles on the seabed (figure_floors 1;
    everyone else stays on the sea, 0). The seabed: its sunlit tiles (":"), its hidden items, the seaweed's own wild list,
    and the 129 <-> 130 seabed edge (exits + edge_to; the floor you arrive on follows the floor you left from)."""
    if not os.path.exists(SEABEDS):
        return
    plan = json.load(open(SEABEDS, encoding="utf-8"))
    for key, p in plan.items():
        m = maps.get(key)
        if not m or m.get("floors"):
            continue
        sea = dict(m)
        art = [list(r) for r in sea["art"]]
        names = list(sea.get("trainer_spots") or [])
        spots = [(x, y) for y, r in enumerate(art) for x, c in enumerate(r) if c == "X"]
        moved = set(p["surface"]["divers_moved"])
        keep = []
        for (x, y), name in zip(spots, names):
            if name in moved:
                art[y][x] = "o"
                (sea.get("moves") or {}).pop(f"{x},{y}", None)
            else:
                keep.append(name)
        missing = moved - set(names)
        if missing:
            print(ascii(f"  hoenn_canon: {key}: divers not on the sea to move down: {sorted(missing)}"))
        for x, y in p["surface"]["deep"]:
            if art[y][x] == "o":
                art[y][x] = ":"
        sea["art"] = ["".join(r) for r in art]
        sea["trainer_spots"] = keep
        sea["dive"] = 1
        sea["dive_links"] = p["surface"]["dive_links"]
        sea["roofs"] = dict(sea.get("roofs") or {}, _picture=dict((sea.get("roofs") or {}).get("_picture") or {}, f=p["surface"]["picture"]))
        if p["surface"]["hidden"]:
            sea["hidden"] = dict(sea.get("hidden") or {}, **p["surface"]["hidden"])
        bed = dict(p["seabed"])
        on = {name: 0 for name in keep}
        on.update({name: 1 for name in bed["trainer_spots"]})
        for q in sea.get("people") or []:
            on[q.get("text") if isinstance(q, dict) else q] = 0
        m.clear()
        m.update(floors=[sea, bed], floor_names=[sea.get("name") or key.replace("HOENN_ROUTE_", "Route "), "The seabed"],
                 figure_floors=on)


def apply(maps):
    _slateport_sub(maps)
    _museum_queue(maps)
    _home_tv(maps)
    _emerald_paths(maps)
    _lavaridge_pads(maps)
    _slateport_dock(maps)
    _rusturf_west(maps)
    _stray_tiles(maps)
    _r112_cable_side(maps)
    _fortree_gym_side(maps)
    _sootopolis_wallace(maps)
    _seafloor_lookout(maps)
    _h7(maps)
    for key, floor, room, x, y, who in PEOPLE:
        m = maps.get(key)
        if m:
            _F._put(_part(m, floor, room), "N", "people", [[x, y, who]])
    for key, floor, x, y, name in TRAINERS:
        m = maps.get(key)
        if m:
            _F._put(_part(m, floor, None), "X", "trainer_spots", [[x, y, name]])
    for key, floor, x, y, item in HIDDEN:
        m = maps.get(key)
        if m:
            p = _part(m, floor, None)
            p.setdefault("hidden", {})[f"{x},{y}"] = item
    for key, floor, room, text, ev in PATCH:
        m = maps.get(key)
        if not m:
            continue
        p = _part(m, floor, room)
        who = next((q for q in p.get("people") or [] if isinstance(q, dict) and q.get("text") == text), None)
        if who is None:
            print(ascii(f"  hoenn_canon: no {text} on {key}: left out"))
            continue
        who["event"] = dict(who.get("event") or {}, **ev)
    for key, floor, pool in FLOOR_POOLS:
        m = maps.get(key)
        if m:
            _part(m, floor, None)["pool"] = pool
    for key, name in DOUBLES:
        m = maps.get(key)
        for p in ((m.get("floors") or [m]) if m else []):
            for q in p.get("people") or []:
                b = (q.get("event") or {}).get("battle") if isinstance(q, dict) else None
                if isinstance(b, dict) and b.get("name") == name:
                    b["double"] = True
    for key, floor, room, x, y, more in LISTS:
        m = maps.get(key)
        if not m:
            continue
        p = _part(m, floor, room)
        i = _at(p, x, y)
        if i is None:
            print(ascii(f"  hoenn_canon: nobody stands on {key} {room or floor} {x},{y}: {more} left out"))
            continue
        had = p["people"][i]
        p["people"][i] = list(more) + (had if isinstance(had, list) else [had])
    _seabeds(maps)
    _route110_grunts(maps)   # (after PEOPLE: two of the five are placed there)
