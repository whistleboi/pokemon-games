"""Orre's story on its walkable maps, Colosseum's order (the pilot, 11-20: kanto_handoff/orre_check/PILOT.md). Laid over
the fan-game maps ogen.py writes (orre.py ends by calling apply), so rebuilding those maps keeps the story.

The pilot stretch (Colosseum walkthrough parts 1-2; teams, levels and moves from Jordan's Colosseum disc,
kanto_handoff/orre_rom_tools/out/col_trainers.json; every battle a double, as in Colosseum; the words are ours):
- Outskirt Stand: two men hurry out of the diner with a sack and drive off; inside, Rider Willie (the TV news, then his
  battle); the bartender gives you 5 Poke Balls once you know you need them.
- Phenac City: Folly drops the sack and battles you; Rui is in the sack and comes with you; Mayor Es Cade; Team Snagem's
  Wakin, and Rui learns about your Snag Machine; back from the Stand, Miror B.'s raid on the Mayor's house (Folly, then
  Trudly and the first Shadow Pokemon, Makuhita); the three Mystery Troop guards with the Johto starters - beat one
  and Phenac opens (flag got_snag_machine, the old flag the travel options and Journal already use).
People here are inline options (src/world/story_events.py fields); their looks are dungeon_sprites.json "figures"."""

WHISMUR, LOTAD, DUSKULL, SPINARAK, CORPHISH, KOFFING, GRIMER, SPOINK, ZIGZAGOON = 293, 270, 355, 167, 341, 109, 88, 325, 263
SH_MAKUHITA, SH_BAYLEEF, SH_QUILAVA, SH_CROCONAW = 9406, 9348, 9349, 9350
DOUBLE = {"double": True}


def _battle(name, cls, sprite, team, levels, moves, **kw):
    b = {"name": name, "class": cls, "sprite": sprite, "team": team, "levels": levels, "team_moves": moves,
         "rewards": {"balls": 0}, "double": True}
    b.update(kw)
    return b


def _n_at(art, x, y):
    """The art with a person tile at (x, y)."""
    row = art[y]
    return art[:y] + [row[:x] + "N" + row[x + 1:]] + art[y + 1:]


def _people_at(m):
    """{(x, y): person} in the order the game hands them out (the art's N tiles, row by row)."""
    spots = [(x, y) for y, row in enumerate(m["art"]) for x, c in enumerate(row) if c == "N"]
    return dict(zip(spots, m.get("people", [])))


def _set_people(m, placed):
    """Puts people at tiles: placed {(x, y): person or None (gone)}; the rest stay where they were."""
    now = _people_at(m)
    for spot, who in placed.items():
        if who is None:
            now.pop(spot, None)
            row = m["art"][spot[1]]
            m["art"] = m["art"][:spot[1]] + [row[:spot[0]] + "." + row[spot[0] + 1:]] + m["art"][spot[1] + 1:]
        else:
            if spot not in now:
                m["art"] = _n_at(m["art"], *spot)
            now[spot] = who
    m["people"] = [now[s] for s in sorted(now, key=lambda s: (s[1], s[0]))]


# ------------------------------------------------------------------ Outskirt Stand
WILLIE = {"text": "Rider Willie", "action": "EVENT", "event": {"stages": [{
    "flag": "orre_beat_willie",
    "lines": ["On the diner's TV: \"...an explosion lit up the desert last night. Team Snagem's hideout is in ruins.\"",
              "Rider Willie: Wild, huh? Hey, you rode in on that bike outside? You look like you know your way round a battle.",
              "Rider Willie: How about it? Me and my Zigzagoon, two on two!"],
    "battle": _battle("Rider Willie", "RIDER", "orre_rider_willie.png", [ZIGZAGOON, ZIGZAGOON], [24, 24],
                      [["TACKLE", "GROWL"], ["TACKLE", "TAIL-WHIP"]], music="orre/willie_battle",
                      dialogue={"player_won": ["Rider Willie: Whoa! You're the real deal!"],
                                "player_lost": ["Rider Willie: Ha! Better luck next time!"]}),
}], "done": ["Rider Willie: You're too good for this place. Go sharpen your skills in Phenac City!",
             "Rider Willie: It's the town with the big fountain. You can't miss it."]}}

BARTENDER = {"text": "Diner", "action": "EVENT", "event": {"stages": [{
    "requires": ["orre_wakin"], "flag": "orre_got_balls",
    "lines": ["Bartender: Poke Balls? Nobody sells those in Orre these days. There's hardly a wild Pokemon left out here.",
              "Bartender: I've got a few lying around, though. Here, take these on the house.",
              "You received 5 POKE BALLS!"],
    "gift_item": {"POKE_BALL": 5}}],
    "done": ["Bartender: The food's good, and it's the only place for miles."]}}

OS_SCENES = [
    {"trigger": "enter", "condition": "not:orre_os_shady", "flag": "orre_os_shady",
     "cast": [{"sheet": "orre_folly.png", "from": [22, 13], "path": [[22, 17]], "stay": True, "wait": 6,
               "lines": ["Two men hurry out of the diner, hauling a big sack between them. The sack wriggles!"]},
              {"sheet": "orre_trainer_burglar.png", "from": [22, 13], "path": [[23, 17]], "stay": True, "concurrent": True,
               "lines": ["???: Quick! Into the truck before anybody sees us!"]},
              {"as": 0, "path": [[22, 17], [47, 17]], "leave_path": [[52, 17]], "lines": []},
              {"as": 1, "path": [[23, 18], [47, 18]], "leave_path": [[52, 18]], "concurrent": True, "lines": []}]},
]


def _outskirt(maps):
    m = maps["OUTSKIRT_STAND"]
    _set_people(m, {(25, 14): None})   # (Willie waits inside the diner now, at the far end of the counter)
    m["scenes"] = OS_SCENES
    d = m["rooms"]["diner"]
    now = _people_at(d)
    now = {s: (BARTENDER if (p.get("text") if isinstance(p, dict) else p) == "Diner" else p) for s, p in now.items()}
    d["people"] = [now[s] for s in sorted(now, key=lambda s: (s[1], s[0]))]
    _set_people(d, {(27, 4): WILLIE})


# ------------------------------------------------------------------ Phenac City
FOLLY_1 = {"text": "Shady Guy Folly", "action": "EVENT", "flag_condition": "not orre_phenac_folly", "event": {
    "flag": "orre_phenac_folly",
    "lines": ["Shady Guy Folly: Hey! What are you looking at? This sack's none of your business!"],
    "battle": _battle("Shady Guy Folly", "SHADY_GUY", "orre_folly.png", [WHISMUR, WHISMUR], [24, 25],
                      [["POUND", "UPROAR"], ["POUND", "HOWL"]],
                      dialogue={"player_won": ["Shady Guy Folly: No way! Forget the sack, let's get out of here!"]})}}
TRUDLY_1 = {"text": "Shady Guy Trudly", "action": "EVENT", "flag_condition": "not orre_phenac_folly",
            "event": {"lines": ["Shady Guy Trudly: Folly, deal with this kid!"]}}
SACK = {"text": "A big sack", "action": "EVENT", "flag_condition": "not orre_rui_joined", "condition": "orre_phenac_folly", "event": {
    "flag": "orre_rui_joined",
    "lines": ["The sack is tied shut, and something inside is moving. You undo the rope...",
              "???: Thank you! I thought I'd never get out of there!",
              "Rui: I'm Rui. Those men grabbed me because I saw something I shouldn't have.",
              "Rui: Their Pokemon... some of them had a dark glow around them. Like their hearts were shut tight.",
              "Rui: Nobody believes me, but I can see it. Please, let me come with you! The Mayor has to hear about this.",
              "Rui joined you! (She can see the dark aura of Shadow Pokemon.)"]}}
WAKIN = {"text": "Team Snagem Wakin", "action": "EVENT", "flag_condition": "not orre_wakin", "condition": "orre_met_mayor", "event": {
    "flag": "orre_wakin",
    "lines": ["Team Snagem Wakin: Well, well. If it isn't the traitor who blew up our hideout!",
              "Rui: Traitor? You were with Team Snagem?",
              "Team Snagem Wakin: That machine on your arm belongs to the boss. Hand it over!"],
    "battle": _battle("Team Snagem Wakin", "SNAGEM", "orre_snagem_grunt.png", [CORPHISH, KOFFING], [25, 27],
                      [["BUBBLE", "VICE-GRIP"], ["POISON-GAS", "TACKLE"]],
                      dialogue={"player_won": ["Team Snagem Wakin: Gah! The boss won't let this go, you hear me?"]})}}
ES_CADE = {"text": "Mayor Es Cade", "action": "EVENT",
           "condition": {"any": ["not:orre_raid_told", "orre_raid_trudly"]},   # (away while Miror B. holds his house)
           "event": {"stages": [{
    "requires": ["orre_rui_joined"], "flag": "orre_met_mayor",
    "lines": ["Mayor Es Cade: Welcome to Phenac, the jewel of the desert! I'm the mayor here.",
              "Rui: Mayor, people are carrying off Pokemon with a dark aura around them! Their hearts look shut tight!",
              "Mayor Es Cade: Shadow Pokemon... I've heard whispers of them. Pokemon made to fight and nothing else.",
              "Mayor Es Cade: Leave it to me. In the meantime, why not try Phenac Stadium, up north? Strong trainers gather there."]}],
    "done": ["Mayor Es Cade: The Stadium is at the top of the town. Off you go!"]}}
TOWNSMAN = "orre_npc_05.png"
RAID_SCENES = [
    {"trigger": "enter", "condition": ["orre_got_balls", "not:orre_raid_told"], "flag": "orre_raid_told",
     "cast": [{"sheet": TOWNSMAN, "from": [25, 57], "to": "player", "leave": "back",
               "lines": ["Man: You're back! Something terrible's happening at the Mayor's house!",
                         "Man: Men in strange outfits barged in, and they haven't come out!"]}]},
]
GUARD_TEXT = ["Mystery Troop: Miror B.'s orders. Nobody leaves Phenac while we're here!"]


def _guard(text, sheet, shadow, moves, item):
    return {"text": text, "action": "EVENT", "flag_condition": "not got_snag_machine", "condition": "orre_raid_trudly", "event": {
        "flag": "got_snag_machine",
        "lines": [f"{text}: Miror B.'s orders. Nobody leaves Phenac while we're here!",
                  "Rui: That Pokemon has the dark aura! Snag it, quick, before it's too late!"],
        "battle": _battle(text, "CIPHER_PEON", sheet, [shadow, GRIMER, SPOINK], [30, 26, 24],
                          [["SHADOW-RUSH"] + moves[:3], ["SLUDGE", "SCREECH"], ["PSYWAVE", "TORMENT"]],
                          dialogue={"player_won": [f"{text}: Retreat! Everybody out of Phenac!",
                                                   "Rui: They've gone! The way out of town is clear."]})}}


VERDE = _guard("Mystery Troop Verde", "orre_cipher_green.png", SH_BAYLEEF, ["SUNNY-DAY", "SYNTHESIS", "RAZOR-LEAF", "BODY-SLAM"], "MIRACLE_SEED")
ROSSO = _guard("Mystery Troop Rosso", "orre_cipher_red.png", SH_QUILAVA, ["SUNNY-DAY", "SMOKESCREEN", "DIG", "FLAME-WHEEL"], "CHARCOAL")
BLUNO = _guard("Mystery Troop Bluno", "orre_cipher_blue.png", SH_CROCONAW, ["RAIN-DANCE", "SCARY-FACE", "BITE", "SURF"], "MYSTIC_WATER")

MIROR_B = {"text": "Miror B.", "action": "EVENT", "flag_condition": "not orre_raid_mirorb", "condition": "orre_raid_told", "event": {
    "flag": "orre_raid_mirorb",
    "lines": ["Miror B.: Oh-ho! Visitors! You've arrived just as the party's ending!",
              "Miror B.: The mayor was such a dull host. My peons will keep you company. Ciao!",
              "Miror B. dances out of the room, and his peons step forward..."]}}
FOLLY_2 = {"text": "Miror B. Peon Folly", "action": "EVENT", "flag_condition": "not orre_raid_folly", "condition": "orre_raid_told", "event": {
    "flag": "orre_raid_folly", "requires": ["orre_raid_mirorb"],   # (all three in the room at once, as in Colosseum; one at a time)
    "fail": ["Miror B. Peon Folly: Hey! The boss is talking. Wait your turn!"],
    "lines": ["Miror B. Peon Folly: It's you again! I've been promoted since then, so watch out!"],
    "battle": _battle("Miror B. Peon Folly", "CIPHER_PEON", "orre_folly_peon.png", [WHISMUR, LOTAD], [26, 25],
                      [["POUND", "UPROAR", "ASTONISH"], ["ABSORB", "GROWL", "ASTONISH"]],
                      dialogue={"player_won": ["Miror B. Peon Folly: Not again! Trudly, you're up!"]})}}
TRUDLY_2 = {"text": "Miror B. Peon Trudly", "action": "EVENT", "flag_condition": "not orre_raid_trudly", "condition": "orre_raid_told", "event": {
    "flag": "orre_raid_trudly", "requires": ["orre_raid_folly"],
    "fail": ["Miror B. Peon Trudly: Folly gets first go. Then you're mine!"],
    "lines": ["Miror B. Peon Trudly: Folly's useless. Let me show you a real Pokemon!",
              "Rui: Look out! That Makuhita... it has the dark aura. It's a Shadow Pokemon!",
              "Rui: Weaken it, then throw a Poke Ball. Your Snag Machine will catch it!"],
    "battle": _battle("Miror B. Peon Trudly", "CIPHER_PEON", "orre_trudly_peon.png", [DUSKULL, SPINARAK, SH_MAKUHITA], [25, 25, 30],
                      [["NIGHT-SHADE", "LEER"], ["CONSTRICT", "STRING-SHOT"], ["SHADOW-RUSH", "FORESIGHT", "FOCUS-ENERGY", "VITAL-THROW"]],
                      dialogue={"player_won": ["Miror B. Peon Trudly: Argh! Miror B. is going to be so mad..."]})}}


def _trainer(text, cls, sprite, team, levels, moves, flag, intro, won):
    """A town trainer of Colosseum's (battles once; after it, a word)."""
    return {"text": text, "action": "EVENT", "event": {"stages": [{
        "flag": flag, "lines": [intro],
        "battle": _battle(text, cls, sprite, team, levels, moves, rewards={"balls": 0}, dialogue={"player_won": [won]})}],
        "done": [won]}}


DRIG = _trainer("Fun Old Man Drig", "FUN_OLD_MAN", "orre_fun_old_man_drig.png", [163, 161], [25, 25],
                [["PECK", "HYPNOSIS"], ["SCRATCH", "DEFENSE-CURL"]], "orre_drig",
                "Fun Old Man Drig: Heh heh! These old bones still love a good battle. Two on two!",
                "Fun Old Man Drig: My, my! You young folks are something else.")
KAIB = _trainer("Roller Boy Kaib", "ROLLER_BOY", "orre_roller_boy_kaib.png", [265, 266], [25, 25],
                [["TACKLE", "STRING-SHOT"], ["TACKLE", "HARDEN"]], "orre_kaib",
                "Roller Boy Kaib: Out of my way! ...Or battle me, I guess. That works too!",
                "Roller Boy Kaib: Aw, man. I'm going back to skating.")


def _phenac(maps):
    m = maps["PHENAC_CITY"]
    _set_people(m, {(30, 44): DRIG, (35, 52): KAIB})   # (Phenac's two trainers, Colosseum's teams)
    _set_people(m, {(26, 53): None, (25, 58): None,   # (the old "Trouble at the Fountain" and "Meet Rui" menu steps)
                    (25, 59): FOLLY_1, (24, 59): TRUDLY_1, (26, 60): SACK,
                    (12, 32): WAKIN,
                    (25, 61): VERDE, (42, 31): ROSSO, (25, 21): BLUNO})
    m["scenes"] = [
        {"who": "Shady Guy Folly", "trigger": "enter", "approach": True, "condition": "not:orre_phenac_folly",
         "flag": "orre_phenac_met_folly", "then": "talk",
         "lines": ["Two men are dragging a big, wriggling sack across the square. One of them spots you..."]},
        {"who": "Team Snagem Wakin", "trigger": {"zone": [9, 30, 14, 32]}, "approach": True,
         "condition": ["orre_met_mayor", "not:orre_wakin"], "flag": "orre_wakin_met", "then": "talk",
         "lines": ["An old man in a Team Snagem jacket blocks your way."],
         "after_lines": ["Rui: So that's a Snag Machine on your arm... It can catch other trainers' Pokemon?",
                         "Rui: Then we can rescue the Shadow Pokemon! We just need Poke Balls.",
                         "Rui: The bartender at the Outskirt Stand might have some. Let's go!"]},
    ] + RAID_SCENES
    mayor = m["rooms"]["mayor"]
    _set_people(mayor, {(9, 6): ES_CADE, (12, 9): MIROR_B, (10, 10): FOLLY_2, (14, 10): TRUDLY_2})
    _set_people(m, {(26, 62): SUPER_POTIONS})   # (Colosseum: 3 Super Potions below the green peon's spot, by the bike)
    mart = m["rooms"]["mart"]   # (Colosseum: upstairs, someone tells you Orre's Marts sell no Poke Balls)
    mart["people"] = [MART_GIRL if isinstance(p, dict) and p.get("text") == "Girl" else p for p in mart["people"]]


SUPER_POTIONS = {"text": "Super Potion ball", "action": "EVENT", "flag_condition": "not orre_phenac_superpotion",
                 "event": {"flag": "orre_phenac_superpotion", "lines": ["You found 3 SUPER POTIONS!"], "gift_item": {"SUPER_POTION": 3}}}
MART_GIRL = {"text": "Girl", "action": "EVENT", "event": {"lines": [
    "Girl: You want Poke Balls? You won't find any here. There are hardly any wild Pokemon in Orre, so nobody sells them.",
    "Girl: Someone at the Outskirt Stand might still have a few."]}}


OLD_SAVE = "not:got_snag_machine"   # (a save already past this stretch: none of it plays again)


def _past_guard(m):
    """Adds the older-save guard to every pilot person and scene on a map (and its rooms)."""
    def guard(o):
        if isinstance(o, dict) and (o.get("event") or o.get("cast") or o.get("who")) and o is not ES_CADE:
            c = o.get("condition")
            o["condition"] = ([OLD_SAVE] + (c if isinstance(c, list) else [c] if c else [])) if c != OLD_SAVE else c
    for p in m.get("people", []):
        if p in (FOLLY_1, TRUDLY_1, SACK, WAKIN, MIROR_B, FOLLY_2, TRUDLY_2):
            guard(p)
    for sc in m.get("scenes", []):
        guard(sc)
    for r in (m.get("rooms") or {}).values():
        _past_guard(r)


def apply(maps):
    if "OUTSKIRT_STAND" in maps:
        _outskirt(maps)
    if "PHENAC_CITY" in maps:
        _phenac(maps)
        _past_guard(maps["PHENAC_CITY"])
