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
    "gift_item": {"balls": 5}}],
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
MART_GIRL = {"text": "Girl", "action": "EVENT", "event": {"stages": [   # (11-24: the Mart stocks balls from the Snag Machine on)
    {"requires": ["not:got_snag_machine"], "lines": [
        "Girl: You want Poke Balls? You won't find any here. There are hardly any wild Pokemon in Orre, so nobody sells them.",
        "Girl: Someone at the Outskirt Stand might still have a few."]},
    {"requires": ["got_snag_machine"], "lines": [
        "Girl: Poke Balls are back on the shelves! Funny - nobody wanted them for years, and now everyone's asking."]}]}}


# ================================================================== batch 1: Pyrite (Colosseum parts 3-4; BATCH_1.md)
import json as _json
import os as _os

_TRAINERS = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "data", "orre_trainers.json")


def T(key, **kw):
    """A disc trainer's battle (dev/builders/data/orre_trainers.json, made by kanto_handoff/orre_rom_tools/otrainers.py)."""
    b = dict(_json.load(open(_TRAINERS, encoding="utf-8"))[key])
    b.pop("disc", None)
    b.update(kw)
    return b


def _fight(text, key, flag, intro, won, done=None, **kw):
    """Someone who battles once (a disc trainer), then says a word."""
    return dict({"text": text, "action": "EVENT", "event": {"stages": [{
        "flag": flag, "lines": intro if isinstance(intro, list) else [intro],
        "battle": T(key, dialogue={"player_won": [won]})}], "done": [done or won]}}, **kw)


SQUARE = {   # (the duel square: the fan game's own spots, map 82; Colosseum's trainers, their first battles)
    (15, 46): _fight("Chaser Calda", "col:51", "orre_sq_calda", "Chaser Calda: Fresh face! Let's see what you've got.",
                     "Chaser Calda: Not bad. Not bad at all."),
    (17, 45): _fight("Chaser Emok", "col:54", "orre_sq_emok", "Chaser Emok: This is the duel square. Nobody walks through without a fight!",
                     "Chaser Emok: Okay, okay, you can walk through."),
    (19, 48): _fight("Rider Nover", "col:57", "orre_sq_nover", "Rider Nover: Some guy gave me a really strong Pokemon. Wanna see it?",
                     "Rider Nover: My Noctowl... it just kept attacking. Was that normal?"),
    (15, 47): _fight("St.Performer Diogo", "col:63", "orre_sq_diogo", "St.Performer Diogo: Step right up! My Pokemon and I put on the best show in Pyrite!",
                     "St.Performer Diogo: That's showbiz, I guess."),
    (22, 47): _fight("Rider Leba", "col:69", "orre_sq_leba", "Rider Leba: I won this Pokemon in a battle at the Colosseum. Let's try it out!",
                     "Rider Leba: Huh. My prize didn't help much."),
    (20, 46): _fight("Bandana Guy Divel", "col:75", "orre_sq_divel", "Bandana Guy Divel: A strange dude gave me a new Pokemon. He wasn't so bad after all!",
                     "Bandana Guy Divel: Aw, man."),
    (21, 49): _fight("Rider Vant", "col:81", "orre_sq_vant", "Rider Vant: My new Pokemon gives me the creeps. Good thing it fights for me!",
                     "Rider Vant: Ugh, you're tough."),
    (16, 48): _fight("Roller Boy Lon", "col:87", "orre_sq_lon", "Roller Boy Lon: Some dude gave me a really strong Pokemon. Afraid?",
                     "Roller Boy Lon: Whoa. You're strong!"),
    (18, 47): _fight("Bodybuilder Hader", "col:775", "orre_sq_hader", "Bodybuilder Hader: Heard you won the Colosseum. Let's see if it was luck!",
                     "Bodybuilder Hader: No luck about it. You're the real thing.", condition="has_pyrite_badge"),   # (the disc's later Pyrite battle)
}
THUG = {"text": "Thug", "action": "EVENT", "event": {"stages": [{"flag": "orre_heard_cail", "lines": [
    "Thug: You here for the tournament? Ha! The real prize in this town is what Cail's got.",
    "Thug: Beat him and he hands out an awesome Pokemon. He's hanging around the bottom of town."]}],
    "done": ["Thug: Cail's down at the bottom of town. Go get your prize, if you can."]}}
CAIL = {"text": "Rogue Cail", "action": "EVENT", "event": {   # ("requires" + "fail": not yet; "done": after - plain event, not stages)
    "requires": ["orre_heard_cail"], "flag": "orre_beat_cail",
    "lines": ["Rogue Cail: So you heard about my prize? Win, and maybe you get to see it up close."],
    "battle": T("col:93", dialogue={"player_won": ["Rogue Cail: Tch. Fine, fine."]}),
    "fail": ["Rogue Cail: Get lost. I don't battle nobodies."],
    "done": ["Rogue Cail: Don't you have somewhere else to be?"]}}
COP_SCENE = {"trigger": "enter", "condition": "not:orre_pyrite_cop", "flag": "orre_pyrite_cop",
             "cast": [{"sheet": "orre_npc_01.png", "from": [29, 80], "path": [[29, 83]], "stay": True,
                       "lines": ["Officer: You there! Did you just take something from that stall?"]},
                      {"sheet": "orre_trainer_burglar.png", "from": [31, 80], "path": [[31, 83]], "stay": True, "concurrent": True,
                       "lines": ["Thief: Me? Officer, I'd never! Look, my hands are empty."]},
                      {"as": 0, "lines": ["Officer: Hm. Well, all right then. Off you go."], "leave_path": [[29, 70]]},
                      {"as": 1, "lines": ["Thief: Heh heh heh... Too easy."], "leave_path": [[33, 78], [36, 78]]}]}
POWER_SCENE = {"trigger": {"zone": [10, 66, 18, 69]}, "condition": ["orre_beat_cail", "not:orre_power_out"], "flag": "orre_power_out",
               "cast": [{"sheet": "orre_trainer_scientist.png", "from": [12, 65], "path": [[12, 67]], "stay": True,
                         "lines": ["A man in a lab coat stumbles out of Duking's door and falls flat.",
                                   "Scientist: Ugh... It's Silva... He took the Gear right out of the windmill!",
                                   "Scientist: Without the windmill there's no power. The Colosseum is dark!"]},
                        {"as": 0, "lines": ["Rui: Silva? He must have gone off somewhere with it. Let's look around Orre!"],
                         "leave_path": [[12, 65]]}]}
NORE = _fight("Cipher Peon Nore", "col:99", "orre_beat_nore",
              ["Cipher Peon Nore: Psst, champ! Follow me. We've got a special prize for winners like you...",
               "Cipher Peon Nore: Wait... You're the one who's been giving Miror B. all that trouble!",
               "Rui: That Yanma has the dark aura!"],
              "Cipher Peon Nore: Gah! Miror B. is going to dance all over me...",
              done="Cipher Peon Nore: ...", condition="has_pyrite_badge", flag_condition="not orre_beat_nore")
BRIDGE_SCENE = {"who": "Cipher Peon Nore", "trigger": {"zone": [24, 28, 28, 37]}, "approach": True,
                "condition": ["has_pyrite_badge", "not:orre_beat_nore"], "flag": "orre_nore_met", "then": "talk"}
PLUSLE_SCENE = {"trigger": "enter", "condition": ["orre_beat_nore", "not:orre_plusle_taken"], "flag": "orre_plusle_taken",
                "cast": [{"sheet": "orre_npc_duking.png", "from": [26, 38], "to": "player", "leave": "back",
                          "lines": ["Duking: There you are! So that's where they've been handing out Shadow Pokemon to the winners...",
                                    "Duking: And there's worse. My Plusle... Miror B.'s gang took her!",
                                    "Rui: Then we'll get her back. Cipher's hideout is right by the bridge: the Pyrite Building!"]}]}
SILVA = {"text": "Silva", "action": "EVENT", "flag_condition": "not orre_power_out", "event": {"lines": [
    "Silva: Duking won't do anything about Miror B.! Everyone just lets that afro creep walk all over Pyrite!",
    "Silva: I'm Silva. If nobody else will stand up to Cipher, I will."]}}
MARCIA = {"text": "Marcia", "action": "EVENT", "event": {"lines": [
    "Marcia: I'm Marcia. Duking looks after us kids here. Leave him be, okay? He's got a lot on his mind."]}}
DUKING_STAGES = {"text": "Duking", "action": "EVENT", "event": {"stages": [
    {"requires": ["orre_got_gear"], "flag": "orre_power_on",
     "lines": ["Duking: You found the Gear? So Silva really did take it... I trusted that boy.",
               "Duking: You two are no ordinary trainers. Here, help me set it back in the windmill.",
               "You put the GEAR back in place. The windmill creaks, then turns. Pyrite Colosseum has power again!",
               "Duking: Go on up to the Colosseum. Show this town what a real trainer looks like."]},
    # (his Plusle, back from Miror B.: the gift that was already Duking's - CANON_SPECIES.md - kept as his next step)
    {"requires": ["orre_miror_cave"], "flag": "orre_duking_plusle", "gift_pokemon": 311, "gift_level": 20,   # (11-24: Lv 20 fits after Miror B. - the disc's 13 predates the stage levels)
     "lines": ["Duking: You got my Plusle back from Miror B.! I owe you everything.",
               "Duking: It wants to go with you. Take good care of it, kid."]}],
    "done": ["Duking: Pyrite's been rough lately. Keep your eyes open, kid."]}}
JAIL_KEY = {"text": "Jail Key", "action": "EVENT", "flag_condition": "not orre_got_jail_key",
            "event": {"flag": "orre_got_jail_key", "lines": ["There's a key on the desk... You took the JAIL KEY!"], "gift_item": {"JAIL_KEY": 1}}}
PRISONER = {"text": "Prisoner", "action": "EVENT", "event": {
    "requires": ["orre_got_jail_key"], "flag": "orre_jail_prisoner",
    "lines": ["Prisoner: Hey! Is that the key? Get me out of here!",
              "You unlocked the cell.", "Prisoner: Thanks, pal. Here, take this. I won't be needing it where I'm going.",
              "You received TM18 (THIEF)!"],
    "gift_item": {"TM018": 1},
    "fail": ["Prisoner: Psst! The sheriff keeps the key on his desk. Get me out of here!"],
    "done": ["(The cell is empty now.)"]}}

# (batch 4: after Dakim, Duking has caught two of Miror B.'s peons - in the sheriff's cells. Reath sleeps; her Elevator Key
#  is on her belt: Colosseum part 6. Ferma stays put even with the cell open.)
REATH_CELL = {"text": "Miror B. Peon Reath (asleep)", "action": "EVENT", "condition": "orre_dakim_mt_battle", "event": {"stages": [
    {"requires": ["not:orre_got_jail_key"], "lines": ["Two of Miror B.'s peons, locked in a cell. One is fast asleep, a key on her belt.",
                                                     "The cell's locked. The sheriff keeps a key on his desk..."]},
    {"requires": ["orre_got_jail_key", "not:orre_elevator_key"], "flag": "orre_elevator_key", "gift_item": {"ELEVATOR_KEY": 1},
     "lines": ["You unlock the cell. Reath is fast asleep, snoring.", "On her belt hangs a key marked ELEVATOR. You ease it off...",
               "You got the ELEVATOR KEY! It must work the Pyrite Building's giant lift."]}],
    "done": ["Reath: Zzz... Miror B.... more music... zzz..."]}}
FERMA_CELL = {"text": "Miror B. Peon Ferma", "action": "EVENT", "condition": "orre_dakim_mt_battle", "event": {"lines": [
    "Ferma: Duking caught us fair and square. Hmph.", "Ferma: The cell's open? ...Where would I even go? I'll wait for Miror B."]}}


def _pyrite(maps):
    m = maps["PYRITE_TOWN"]
    _set_people(m, {**SQUARE, (24, 23): THUG, (30, 84): CAIL, (26, 33): NORE})
    m["scenes"] = [COP_SCENE, POWER_SCENE, BRIDGE_SCENE, PLUSLE_SCENE, FATEEN_SCENE]
    m["locked"] = dict(m.get("locked") or {}, XD_ONBS="A sign on the ONBS door: \"Closed for a live broadcast. No visitors today.\"")   # (R1: XD's ONBS door, Q21)
    m["barred"] = list(m.get("barred") or []) + [   # (Cipher's hideout: shut till you've won the Colosseum - Colosseum's order)
        {"tiles": [[32, 40]], "look": "sheet:orre_trainer_cipher_grunt.png", "face": "d", "until": {"condition": "has_pyrite_badge"},
         "lines": ["Cipher Peon: Members only! Come back when you're somebody, like a Colosseum champ."]},
        {"tiles": [[33, 40]], "look": "sheet:orre_trainer_cipher_grunt.png", "face": "d", "until": {"condition": "has_pyrite_badge"},
         "lines": ["Cipher Peon: You heard him. Beat it!"]}]
    dk = m["rooms"]["duking"]
    now = _people_at(dk)
    now = {s: (DUKING_STAGES if (p.get("text") if isinstance(p, dict) else p) == "Duking" else p) for s, p in now.items()}
    dk["people"] = [now[s] for s in sorted(now, key=lambda s: (s[1], s[0]))]
    _set_people(dk, {(4, 8): SILVA, (12, 9): MARCIA})
    _set_people(m["rooms"]["sheriff"], {(14, 3): JAIL_KEY, (30, 7): PRISONER, (33, 7): REATH_CELL, (33, 12): FERMA_CELL})


# ================================================================== batch 2: Pyrite Cave, Agate (Colosseum part 5; BATCH_2.md)
FATEEN_SCENE = {"trigger": {"zone": [27, 83, 33, 86]}, "condition": ["orre_miror_cave", "not:orre_fateen"], "flag": "orre_fateen",
                "cast": [{"sheet": "orre_npc_fortune_lady.png", "from": [25, 76], "to": "player", "leave": "back",
                          "lines": ["Fateen: Leaving so soon? Wait. I see something in the north... a village by the falls, and trouble coming to it.",
                                    "Rui: In the north... that's Agate Village! My grandparents live there.",
                                    "Rui: Let's ride to Agate. I want to make sure they're all right."]}]}
SKOF = _fight("Fun Old Man Skof", "col:191", "orre_agate_skof", "Fun Old Man Skof: These old bones still have a battle or two in them!",
              "Fun Old Man Skof: Heh heh. That's what I call a workout.")
DURY = _fight("Cooltrainer Dury", "col:201", "orre_agate_dury", "Cooltrainer Dury: Agate's the place to train. The air's clean and the battles are fair.",
              "Cooltrainer Dury: You trained hard to get that good.")
QUICK_CLAW = {"text": "Quick Claw", "action": "EVENT", "flag_condition": "not orre_agate_quick_claw",
              "event": {"flag": "orre_agate_quick_claw", "lines": ["You found a QUICK CLAW!"], "gift_item": {"QUICK_CLAW": 1}}}
EIN_FILE_C = {"text": "Ein File C", "action": "EVENT", "flag_condition": "not orre_ein_file_c", "condition": "orre_beat_skrub",
              "event": {"flag": "orre_ein_file_c", "lines": ["Skrub dropped something by the Relic Stone... You found EIN FILE C!"],
                        "gift_item": {"EIN_FILE_C": 1}}}
BELUH = {"text": "Beluh", "action": "EVENT", "event": {"stages": [{
    "requires": ["orre_beat_skrub"], "flag": "orre_beluh_tablet",
    "lines": ["Beluh: You saved my husband! Thank you, both of you.",
              "Beluh: The Relic Stone can open a Shadow Pokemon's heart, once its gauge is empty. Take your Pokemon there.",
              "Beluh: And there was an e-mail for you, Rui... Something about Mt. Battle being attacked!"]},
    {"requires": ["xd_beluh_mail"], "flag": "xd_le_asked",   # (XD's Lucky Egg quest, batch 8b: after Orre Colosseum round 1)
     "lines": ["Beluh: {player_name}, thank you for coming. Some of the village's Pokemon have stopped making any sound at all.",
               "Beluh: Senilor's Wobbuffet was the first. His house is just down the hill, between ours and the Mart.",
               "Beluh: Would you look into it? Eagun says you have a knack for helping Pokemon."]},
    {"requires": ["xd_le_lotad"], "flag": "xd_lucky_egg", "gift_item": {"LUCKY_EGG": 1},
     "lines": ["Beluh: Wobbuffet's chattering again, and the others too! And that Lotad was only shy? Ho ho!",
               "Beluh: You've done the whole village a kindness. Please, take this Lucky Egg.",
               "Beluh: A Pokemon holding it learns more from every battle. Use it well, {player_name}."]}],
    "done": ["Beluh: Rui, dear, you look so grown up. Take care of each other."]}}
CAVE_GUARD = {"tiles": [[36, 27]], "look": "sheet:orre_npc_10.png", "face": "d", "until": {"condition": "met_agate_elder"},
              "lines": ["Man: Sorry, nobody goes into the Relic Cave. The elder's orders."]}


def _agate(maps):
    m = maps["AGATE_VILLAGE"]
    _set_people(m, {(52, 22): SKOF, (70, 27): DURY, (60, 27): QUICK_CLAW, (37, 28): EIN_FILE_C})
    m["barred"] = list(m.get("barred") or []) + [CAVE_GUARD]
    _set_people(m["rooms"]["elder"], {(3, 5): BELUH})
    _agate_garden(m["rooms"]["gym"])


# The Agate Gym's number garden (Jordan 11-24, questions/ORRE.md 6 - "our own puzzle", not the fan game's mirrors): three
# gardens in the hall; walk over beds whose numbers make each garden's target (too much and its vines grow back); all three
# in bloom and Blaine burns the vines off the way in to the Leaders (src/world/number_garden.py). Targets up to about 30.
AGATE_GARDENS = {"flag": "agate_garden_done", "gardens": [
    {"target": 10, "label": [2, 5], "beds": {"2,6": 2, "3,6": 7, "4,6": 4, "2,7": 6, "3,7": 3, "4,7": 5}},
    {"target": 18, "label": [9, 6], "beds": {"9,7": 8, "10,7": 3, "11,7": 6, "9,8": 4, "10,8": 9, "11,8": 5}},
    {"target": 27, "label": [16, 2], "beds": {"16,3": 9, "17,3": 5, "18,3": 12, "16,4": 7, "17,4": 8, "18,4": 6}}],
    "done": ["Every garden in the hall is in full bloom!",
             "Blaine: Hah! Not bad at all. Erika's flowers like you - so I'll clear the way.",
             "Blaine burns the vines off the door to the inner garden!"]}
AGATE_VINES = {"tiles": [[21, 7]], "flag": "agate_garden_done", "look": "img:orre_garden/vines.png",
               "lines": ["Thick vines cover the door. Erika's sign says the gardens must bloom first."]}
AGATE_SIGNS = [["AGATE GYM - Leaders: Blaine and Erika", "Walk over a garden's flower beds: each one you step on blooms and adds its number.",
                "Make the garden's number exactly and it stays in bloom. Go over, and the vines grow back!"],
               ["AGATE GYM", "Three gardens in bloom, and the way to the Leaders opens."]]


def _agate_garden(room):
    room["gardens"] = AGATE_GARDENS
    room["barred"] = list(room.get("barred") or []) + [AGATE_VINES]
    room["signs"] = [list(x) for x in AGATE_SIGNS[:len(room.get("signs") or [])]]


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


# ================================================================== batch 4: The Under and its subway (Colosseum part 6; BATCH_4.md)
# Played-out scenes on The Under's floors (dungeon floor "scenes", src/dungeon/npc.py); its people and battles are route
# options in orre_area_data.json (kanto_handoff/orre_rom_tools/obatch4.py). Floors: 0 the Under, 2 the studio basement,
# 10 the subway stairway, 11 the station, 12 the far station (reached only by train: its "landings").
REACH = ".,N"


def _open(fl):
    return [(x, y) for y, r in enumerate(fl["art"]) for x, c in enumerate(r) if c in REACH]


def _link_to(fl, floor):
    return next((tuple(map(int, k.split(","))) for k, v in (fl.get("links") or {}).items() if v[0] == floor), None)


def _near(fl, t, far=False):
    """The open tile nearest t (or farthest from it)."""
    op = [u for u in _open(fl) if fl["art"][u[1]][u[0]] != "N"]
    return (max if far else min)(op, key=lambda u: abs(u[0] - t[0]) + abs(u[1] - t[1]))


def _under(maps):
    fl = maps["THE_UNDER"]["floors"]
    VENUS, PEON, LOCAL = "orre_trainer_cipher_venus.png", "orre_trainer_cipher_grunt.png", "orre_npc_02.png"
    up = next(((x, y) for y, r in enumerate(fl[0]["art"]) for x, c in enumerate(r) if c == "^"), (15, 15))
    fl[0]["scenes"] = [{"trigger": "enter", "condition": ["not:orre_under_spies"], "flag": "orre_under_spies",
                        "cast": [{"sheet": LOCAL, "from": list(_near(fl[0], up, far=True)), "to": "player", "leave": "back",
                                  "lines": ["Every screen in the Under lights up. Venus, all pink and smiles:",
                                            "Venus: Darlings, there are SPIES in the Under! Turn them in within thirty seconds!",
                                            "Under kid: Spies? Ha. Nobody down here would tell Venus a thing. Welcome to the Under."]}]}]
    door = _link_to(fl[2], 10)
    if door:
        fl[2]["scenes"] = [{"trigger": "enter", "condition": ["cleared_the_under", "not:orre_venus_fled"], "flag": "orre_venus_fled",
                            "cast": [{"sheet": VENUS, "from": list(_near(fl[2], door, far=True)), "path": [list(_near(fl[2], door))],
                                      "face": "u", "lines": ["Venus: You'll never catch me! The subway's mine!"], "leave_path": [list(door)]}]}]
    q = _link_to(fl[11], 10) or (4, 3)
    far = _near(fl[11], q, far=True)
    fl[11]["scenes"] = [{"trigger": "enter", "condition": ["cleared_the_under", "not:orre_venus_station"], "flag": "orre_venus_station",
                         "cast": [{"sheet": VENUS, "from": list(_near(fl[11], (q[0] + 6, q[1] + 2))), "to": list(_near(fl[11], (q[0] + 8, q[1] + 2))),
                                   "lines": ["Venus: Still following me? How tiresome. Boys!"], "stay": True},
                                  {"sheet": PEON, "from": list(_near(fl[11], (q[0] + 9, q[1] + 1))), "to": list(_near(fl[11], (q[0] + 10, q[1] + 1))),
                                   "lines": ["Cipher Peon: This way, Venus! Over the tracks!"], "stay": True},
                                  {"as": 0, "lines": ["Venus: Ta-ta, darling!"], "leave_path": [list(far)]},
                                  {"as": 1, "lines": [], "leave_path": [list(far)], "concurrent": True}]}]
    back = next(((x, y) for y, r in enumerate(fl[12]["art"]) for x, c in enumerate(r) if c == "N"), None)
    if back:
        land = _near(fl[12], (back[0], back[1] + 1))
        fl[12]["landings"] = [list(land)]
        bars = [b for b in fl[12].get("barred") or []]
        boom = bars[0]["tiles"][0] if bars else list(land)
        fl[12]["scenes"] = [{"trigger": "enter", "condition": ["not:orre_subway_bomb"], "flag": "orre_subway_bomb",
                             "cast": [{"sheet": PEON, "from": list(_near(fl[12], (boom[0] - 2, boom[1] - 1))), "to": list(_near(fl[12], (boom[0] - 1, boom[1] - 1))),
                                       "lines": ["Cipher Peon: The kid's on the train! Set the charge on the door!"], "stay": True},
                                      {"sheet": PEON, "from": list(_near(fl[12], (boom[0] + 2, boom[1] - 1))), "to": list(_near(fl[12], (boom[0] + 1, boom[1] - 1))),
                                       "lines": ["Cipher Peon: Done! Nobody's getting through that. Run!"], "stay": True},
                                      {"as": 0, "lines": [], "leave_path": [list(_near(fl[12], land, far=True))]},
                                      {"as": 1, "shake": 900, "leave_path": [list(_near(fl[12], land, far=True))],
                                       "lines": ["KA-BOOM! The charge went off too soon - the door is blown wide open!"]}]}]


# ================================================================== batch 5a: XD's opening act with Wes (BATCH_5A.md)
# Jordan 11-20: Wes reaches the HQ Lab (after Ein's Lab) as Naps carries Professor Krane off; Lily asks for help; the
# Machine Part from Gateon's Parts Shop (Perr's dad Makan is at Kaminko's, past Chobin); Datan traces Cipher's car to the
# Cipher Lab. XD's teams, raised to fit (DECISIONS: levels keep climbing). The words are ours.
LILY, JOVI, NAPS = "orre_npc_04.png", "orre_npc_cute_hair_girl.png", "orre_trainer_cipher_grunt.png"
KIDNAP_SCENE = {"trigger": "enter", "condition": ["orre_part2", "not:xd_kidnap_seen", "not:xd_lovrina_beaten"], "flag": "xd_kidnap_seen",
                "cast": [{"sheet": NAPS, "from": [10, 9], "path": [[10, 10]], "face": "d", "stay": True,
                          "lines": ["Three men in Cipher uniforms burst out of the lab, dragging an old man in a white coat.",
                                    "Spy Naps: Move it, Professor! Our boss wants a word about that Purify Chamber of yours."]},
                         {"sheet": LILY, "from": [10, 9], "to": "player", "wait": 20,
                          "lines": ["Lily: Professor Krane! ...You! You're a trainer, aren't you? Please, stop them!"], "stay": True}]}
NAPS_FIGHT = {"text": "Spy Naps", "action": "EVENT", "condition": ["xd_kidnap_seen"], "flag_condition": "not xd_krane_taken",
              "event": {"flag": "xd_krane_taken", "lines": ["Spy Naps: A hero, huh? My Teddiursa will tear you apart!"],
                        "battle": T("xd:Story:17", dialogue={"player_won": [
                            "Spy Naps: My Teddiursa... you snagged it?! Forget it - the Professor's what we came for!",
                            "The men shove Krane into a car and race off down the pipe road."]})}}
LILY_LAB = {"text": "Lily", "action": "EVENT", "event": {"stages": [
    {"requires": ["not:xd_krane_taken"], "lines": ["Lily: I'm Lily. I run the Pokemon HQ Lab with Professor Krane."]},
    {"requires": ["xd_krane_taken", "not:xd_lily_asked"], "flag": "xd_lily_asked",
     "lines": ["Lily: Thank you for trying... They've taken the Professor. He was close to finishing the Purify Chamber.",
               "Lily: It can open a Shadow Pokemon's heart. Cipher must not have it.",
               "Lily: We still need one Machine Part. Gateon Port's Parts Shop should have it - ask for Perr.",
               "Jovi: I'm coming too! Professor Krane always lets me help!"]},
    {"requires": ["has_item:MACHINE_PART", "not:xd_machine_part_given"], "flag": "xd_machine_part_given",
     "take_item": {"MACHINE_PART": 1},
     "lines": ["Lily: The Machine Part! Jovi, run it down to the Chamber.",
               "Datan: Lily! I traced Cipher's car. It went to the old Shadow Pokemon Lab, out in the desert.",
               "Lily: The lab Cipher abandoned five years ago... They've opened it again. {player_name}, please - bring the Professor home."]},
    {"requires": ["xd_lovrina_beaten", "not:xd_krane_home"], "flag": "xd_krane_home", "gift_item": {"XD_DATA_ROM": 1},
     "lines": ["Lily: You brought him back! Thank you, {player_name}. The Purify Chamber is nearly done - the Professor will finish it.",
               "Professor Krane: {player_name}, one more favour. Take my research data to Nett at ONBS, in Pyrite. Keep it out of Cipher's hands."]}],
    "done": ["Lily: The Professor's working day and night on the Purify Chamber."]}}
AFERD = {"text": "Supertrainer Aferd", "action": "EVENT", "event": {"stages": [{
    "flag": "xd_aferd", "lines": ["Supertrainer Aferd: I test the lab's training data. Spar with me?"],
    "battle": T("xd:Story:8", dialogue={"player_won": ["Supertrainer Aferd: Good data. Thanks!"]})}],
    "done": ["Supertrainer Aferd: The Professor says strong trainers make the best data."]}}

ZOOK_SCENE = {"trigger": "enter", "condition": ["xd_lily_asked", "not:xd_zook_scene"], "flag": "xd_zook_scene",
              "cast": [{"sheet": JOVI, "from": [30, 56], "path": [[30, 50]], "face": "u", "stay": True,
                        "lines": ["Jovi: Gateon Port! Come on, the Parts Shop is this w- oof!"]},
                       {"sheet": "orre_trainer_biker.png", "from": [30, 46], "path": [[30, 49]], "face": "d", "stay": True,
                        "lines": ["Thug Zook: Watch where you're going, brat! Maybe my Zangoose should teach you some manners..."]},
                       {"sheet": "orre_trainer_gentleman.png", "from": [36, 50], "path": [[32, 50]], "face": "l", "stay": True,
                        "lines": ["Mr. Verich: That will do. Gateon Port is no place for bullies."]},
                       {"sheet": "orre_trainer_psychic_m.png", "from": [37, 51], "path": [[32, 51]], "face": "l", "stay": True,
                        "lines": ["Ardos: Alakazam. ...It's over. Your Zangoose is in no state to fight."]},
                       {"as": 1, "lines": ["Thug Zook: Grr... This isn't over!"], "leave_path": [[30, 40]]},
                       {"as": 2, "lines": ["Mr. Verich: Children should be careful. Orre is full of... surprises. Good day."],
                        "leave_path": [[44, 50]]},
                       {"as": 3, "lines": [], "leave_path": [[44, 51]], "concurrent": True},
                       {"as": 0, "lines": ["Jovi: Who were THEY? ...Anyway! Parts Shop!"], "leave_path": [[30, 56]]}]}
PERR = {"text": "Perr", "action": "EVENT", "event": {"stages": [
    {"requires": ["not:xd_lily_asked"], "lines": ["Perr: Welcome to the Parts Shop! If it's got gears, we've got it."]},
    {"requires": ["xd_lily_asked", "not:xd_perr_asked"], "flag": "xd_perr_asked",
     "lines": ["Perr: A Machine Part for the Purify Chamber? We've got one in the stockroom, but Dad has the key.",
               "Perr: Dad - Makan - went to Kaminko's House. He fixes the old man's inventions. It's up the road north of town."]},
    {"requires": ["xd_bonsly_asked", "not:xd_perr_grandpa"], "flag": "xd_perr_grandpa",
     "lines": ["Perr: Cross the deep sand? Grandpa could do it - he rebuilds engines. He's at Kaminko's, down on the crane floor.",
               "Perr: Chobin guards the way down. Tell him I sent you!"]},
    {"requires": ["xd_makan_back", "not:has_item:MACHINE_PART", "not:xd_machine_part_given"], "gift_item": {"MACHINE_PART": 1},
     "flag": "xd_machine_part",
     "lines": ["Makan: Here's your Machine Part. Tell Lily it's on the house.",
               "Makan: And while I was at it, I got Gateon's movable bridges working again. Have a look around!"]}],
    "done": ["Perr: Come back any time!"]}}

GATEON_TRAINERS = {
    (49, 36): _fight("Navigator Berk", "xd:Story:11", "xd_gateon_berk", "Navigator Berk: The Krabby Club's for sailors. Prove you belong!",
                     "Navigator Berk: Fair enough. In you go."),
    (17, 45): _fight("Sailor Bost", "xd:Story:13", "xd_gateon_bost",
                     "Sailor Bost: Oh, the sea, the sea... You've heard of me, haven't you? No? Then I'll show you!",
                     "Sailor Bost: Here, take this. TM240: Attract. Make 'em swoon!"),
    (30, 40): _fight("Chaser Laken", "xd:Story:16", "xd_gateon_laken", "Chaser Laken: I race the ferries along the pier. Race me in a battle!",
                     "Chaser Laken: You're fast."),
}   # (Cyle and Kilen: on the islands, _gateon_islands)
GATEON_TRAINERS[(17, 45)]["event"]["stages"][0]["battle"]["rewards"] = {"balls": 0, "TM240": 1}   # (a battle's prize: a gift on its stage isn't handed out)


def _xd5a(maps):
    if "POKEMON_HQ_LAB" in maps:
        m = maps["POKEMON_HQ_LAB"]
        m["scenes"] = list(m.get("scenes") or []) + [KIDNAP_SCENE]
        _set_people(m, {(10, 10): NAPS_FIGHT})
        _set_people(m["rooms"]["lab"], {(9, 6): LILY_LAB, (11, 10): AFERD})
    if "GATEON_PORT" in maps:
        m = maps["GATEON_PORT"]
        m["scenes"] = list(m.get("scenes") or []) + [ZOOK_SCENE]
        _set_people(m, GATEON_TRAINERS)
        _set_people(m["rooms"]["bikeshop"], {(10, 5): PERR})


# ------------------------------------------------------------------ 11-24: Gateon's islands (XD's Bridge System) and the lighthouse Gym
# Jordan 11-24 (review/gateon_islands_plan.png in kanto_handoff/orre_map_tools): six movable bridges, raised till Makan fixes
# them (xd_gateon_bridges); Cyle on the north island (XD's cliff), Kilen on the lighthouse roof (XD's). The fan game's
# lighthouse Gym kept ("keep the gym"): three guardians by each floor's stairs, then Jasmine on the roof. S3 (11-24): it is
# badge 5, the Gateon Badge, in Part 2 (Lv 36-41, Kanto's caps); her prize HGSS Jasmine's TM, Iron Tail.
GATEON_BRIDGES = [(37, 22, 40, 23), (23, 22, 26, 23), (31, 18, 32, 21), (17, 18, 18, 21), (31, 25, 32, 28), (17, 28, 18, 31)]   # (towns.py "bridges")


def _guardian(name, pid, flag, level):
    return {"text": f"Lighthouse {name}", "action": "BOSS", "color": "RED", "condition": "orre_part2",   # (S3: the Gym of badge 5)
            "flag_condition": f"not {flag}",
            "boss": {"id": pid, "name": name, "level": level, "victory_flag": flag,
                     "lines": [f"{name} crackles with stored power. It guards the stairs!"]}}


JASMINE = {"text": "Gym Leader Jasmine", "action": "EVENT", "color": "GOLD", "condition": "orre_part2", "event": {"stages": [
    # (S3, 11-24: badge 5 - her team, prize and badge are GATEON_PORT's "gym" in orre_area_data.json; src/world/orre_gym.py runs
    #  the Gym's math game, then her battle; the three guardians first, as the fan game has it)
    {"requires": ["gateon_lh_electabuzz", "gateon_lh_electrode", "gateon_lh_ampharos"],
     "fail": ["Jasmine: The lighthouse's Pokemon guard the stairs for me. Get past all three, then we'll battle."],
     "world": "orre_gym"}]}}
KILEN_ROOF = _fight("Bodybuilder Kilen", "xd:Story:14", "xd_gateon_kilen",
                    "Bodybuilder Kilen: Up here every day while the bridge was out... and you finally climbed up. Fight!",
                    "Bodybuilder Kilen: Lost to a kid. Back to my push-ups.", condition="xd_gateon_bridges")
CYLE_CLIFF = _fight("Casual Guy Cyle", "xd:Story:12", "xd_gateon_cyle", "Casual Guy Cyle: The bridges work again! First one across gets a battle - that's you!",
                    "Casual Guy Cyle: Huh. My Ledyba felt... strange.", condition="xd_gateon_bridges")


def _by_text(m, text, who):
    """Swaps the person whose entry is the placeholder text (towns.py room_people) for who."""
    m["people"] = [who if p == text else p for p in m.get("people", [])]


def _gateon_islands(maps):
    if "GATEON_PORT" not in maps:
        return
    m = maps["GATEON_PORT"]
    _set_people(m, {(17, 15): CYLE_CLIFF})   # (Cyle and Kilen waited at (23, 40), (24, 40) on the mainland till the islands were built)
    bars = list(m.get("barred") or [])
    for (x0, y0, x1, y1) in GATEON_BRIDGES:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                bars.append({"tiles": [[x, y]], "flag": "xd_gateon_bridges", "look": f"img:orre_bridge/80_{x}_{y}.png",
                             "lines": ["The movable bridge is raised. It's been stuck like that for ages."]})
    m["barred"] = bars
    r = m["rooms"]
    _by_text(r["lighthouse"], "Lighthouse Electabuzz", _guardian("Electabuzz", 125, "gateon_lh_electabuzz", 36))
    _by_text(r["lighthouse_2f"], "Lighthouse Electrode", _guardian("Electrode", 101, "gateon_lh_electrode", 37))
    _by_text(r["lighthouse_3f"], "Lighthouse Ampharos", _guardian("Ampharos", 181, "gateon_lh_ampharos", 38))
    _by_text(r["lighthouse_roof"], "Gym Leader Jasmine", JASMINE)
    _by_text(r["lighthouse_roof"], "Bodybuilder Kilen", KILEN_ROOF)


# ------------------------------------------------------------------ batch 5a: Battle CDs (kanto_handoff/orre_check/BATTLE_CDS.md)
# The player at the HQ Lab (src/world/battle_cd.py); the CDs in the places built so far, where XD hides them (Serebii's list).
def CD_PICK(n, where, cond=None):
    o = {"text": f"Battle CD {n}", "action": "EVENT", "flag_condition": f"not got_battle_cd_{n}",
         "event": {"flag": f"got_battle_cd_{n}", "gift_item": {f"BATTLE_CD_{n}": 1},
                   "lines": [f"{where} You found Battle CD {n}!", "It can be played on the Battle CD player at the Pokemon HQ Lab."]}}
    if cond:
        o["condition"] = cond
    return o


CD_PLAYER = {"text": "Battle CD player", "action": "EVENT", "event": {
    "battle_cd_player": True, "lines": ["The Battle CD player. Each CD is a battle puzzle, with a team lent for it."]}}


def _free_spot(m, near=None):
    """An open floor tile with open ground around it and nobody on it (near a point, else the room's middle)."""
    art = m["art"]
    taken = set(_people_at(m))
    exits = {(x, y) for y, r in enumerate(art) for x, c in enumerate(r) if c not in ".,N" and c in (m.get("exits") or {})}
    h, w = len(art), len(art[0])
    cx, cy = near or (w // 2, h // 2)
    ok = []
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if art[y][x] != "." or (x, y) in taken:
                continue
            if sum(art[y + dy][x + dx] == "." for dx in (-1, 0, 1) for dy in (-1, 0, 1)) < 8:
                continue
            if any(abs(x - ex) + abs(y - ey) < 3 for ex, ey in exits) or any(abs(x - tx) + abs(y - ty) < 2 for tx, ty in taken):
                continue
            ok.append((abs(x - cx) + abs(y - cy), y, x))
    _d, y, x = min(ok)
    return (x, y)


def _battle_cds(maps):
    if "POKEMON_HQ_LAB" in maps:
        lab = maps["POKEMON_HQ_LAB"]["rooms"]["lab"]
        _set_people(lab, {_free_spot(lab, (3, 6)): CD_PLAYER})
        _set_people(lab, {_free_spot(lab, (12, 10)): CD_PICK("33", "On a bookshelf:", "xd_greevil_beaten")})
    if "GATEON_PORT" in maps:
        r = maps["GATEON_PORT"]["rooms"]["krabby"]
        _set_people(r, {_free_spot(r): CD_PICK("06", "On the desk:")})
    if "AGATE_VILLAGE" in maps:
        r = maps["AGATE_VILLAGE"]["rooms"]["house_centre"]
        _set_people(r, {_free_spot(r): CD_PICK("14", "The house's Wobbuffet was sitting on something:")})
    if "PYRITE_TOWN" in maps:
        r = maps["PYRITE_TOWN"]["rooms"]["duking"]
        _set_people(r, {_free_spot(r): CD_PICK("22", "On Duking's bookshelf:")})
        r = maps["PYRITE_TOWN"]["rooms"]["house_tower"]
        _set_people(r, {_free_spot(r): CD_PICK("40", "On the bookshelf:", "xd_greevil_beaten")})


# ================================================================== batch 5b: XD parts 3-5 (BATCH_5B.md)
# Pyrite's duel square in XD's time (after Lovrina, raised to fit); the Cave Poke Spot's scene before Miror B.; Gorigan on
# the S.S. Libra's bridge. Everything else of 5b is in orre_area_data.json (kanto_handoff/orre_rom_tools/obatch5b.py).
XD_SQUARE = [("Rogue Cail", "xd:Story:62", "Rogue Cail: Five years, and Pyrite's still my town. Let's see what you've learned!", "Rogue Cail: Heh. You've still got it."),
             ("Worker Dobit", "xd:Story:63", "Worker Dobit: On my break! A quick battle, then back to work.", "Worker Dobit: Break's over."),
             ("Chaser Finol", "xd:Story:64", "Chaser Finol: The duel square's busy again since Cipher came back. Battle!", "Chaser Finol: Busy and tough!"),
             ("Rider Dert", "xd:Story:65", "Rider Dert: I ride in from the desert every day just for this.", "Rider Dert: Worth the ride."),
             ("Hunter Raling", "xd:Story:66", "Hunter Raling: I hunt strong trainers. Found one!", "Hunter Raling: You're the hunter, not me."),
             ("Chaser Labet", "xd:Story:67", "Chaser Labet: My team's all rare finds. Bet you've never seen them.", "Chaser Labet: Rare finds, common loss."),
             ("Bodybuilder Doby", "xd:Story:68", "Bodybuilder Doby: Muscles! Battles! Muscles!", "Bodybuilder Doby: ...Muscles.")]
GORIGAN_SCENE = {"trigger": "enter", "condition": ["not:xd_libra_gorigan"], "flag": "xd_libra_gorigan",
                 "cast": [{"sheet": "orre_trainer_bodybuilder.png", "from": [10, 3], "to": [10, 4], "face": "d", "stay": True,
                           "lines": ["A huge man in a Cipher coat is shouting at two peons.",
                                     "Cipher Admin Gorigan: You LOST a Pokemon? On a ship stuck in the sand?! Find it, or else!"]},
                          {"sheet": "orre_trainer_cipher_grunt.png", "from": [12, 3], "to": [12, 4], "face": "u", "stay": True,
                           "lines": ["Cipher Peon Snidle: S-sorry, Gorigan! ...Hey, a kid! Smarton, get them!"]},
                          {"as": 0, "lines": ["Gorigan: Hmph. Deal with it. I've got bigger things to do in the Key Lair."],
                           "leave_path": [[2, 4]]},
                          {"as": 1, "lines": [], "leave_path": [[2, 4]], "concurrent": True}]}
CAVE_SCENE = {"trigger": "enter", "condition": ["xd_spot_cave", "not:xd_cave_folly"], "flag": "xd_cave_folly",
              "cast": [{"sheet": "orre_folly.png", "from": [6, 14], "to": [7, 12], "face": "r", "stay": True,
                        "lines": ["Folly: This Miror B. Radar finds Miror B. anywhere, Trudly! He's gonna take us back for sure!"]},
                       {"sheet": "orre_trainer_burglar.png", "from": [9, 14], "to": [9, 12], "face": "l", "stay": True,
                        "lines": ["Trudly: It's beeping! He's close! ...Huh? Who's that kid?"]},
                       {"as": 0, "lines": ["Folly: Uh-oh. Boss, it's that snagging kid!"], "leave_path": [[6, 18]]},
                       {"as": 1, "lines": [], "leave_path": [[9, 18]], "concurrent": True}]}


def _xd5b(maps):
    if "PYRITE_TOWN" in maps:
        m = maps["PYRITE_TOWN"]
        for i, (text, key, intro, won) in enumerate(XD_SQUARE):
            _set_people(m, {_free_spot(m, (13 + 3 * i, 52)): _fight(text, key, f"xd_sq_{key.split(':')[-1]}", intro, won,
                                                                  condition="xd_lovrina_beaten")})
    if "SS_LIBRA" in maps:
        fl = maps["SS_LIBRA"]["floors"]
        fl[2]["scenes"] = list(fl[2].get("scenes") or []) + [GORIGAN_SCENE]
    if "CAVE_POKE_SPOT" in maps:
        fl = maps["CAVE_POKE_SPOT"]["floors"]
        fl[0]["scenes"] = list(fl[0].get("scenes") or []) + [CAVE_SCENE]


# ================================================================== batch 6: Phenac in Cipher's hands; the Outskirt Stand (BATCH_6.md)
# XD part 4 with Wes, after ONBS (S4: the S.S. Libra optional): Cipher's peons wear the townsfolk's faces. The gate lady's Battle CDs; the Music Disc
# for the mayor's secretary (a peon) and Es Cade's note to Justy (Jordan 11-21: Es Cade "missing", no Trest); the six Justy
# impersonators (the Hexagon Brothers) with their CDs; Ertlig on the way to the stadium; the stadium's ambush and Snattle's
# lackey. XD part 5: Miror B., Hordel's Shadow Togepi and Willie at the Outskirt Stand. XD's teams +28 (Snattle's ace 56).
TAKEOVER = ["xd_exol_beaten", "not:orre_snattle_phenac"]   # (S4, 11-24: from Exol's defeat - the S.S. Libra is optional)
MUSIC_MAN = {"text": "Music lover", "action": "EVENT", "event": {"stages": [
    {"requires": ["xd_exol_beaten", "not:xd_music_disc"], "flag": "xd_music_disc", "gift_item": {"MUSIC_DISC": 1},
     "lines": ["Music lover: The mayor's secretary wants music? Here, take this Music Disc. Phenac's been so quiet lately."]}],
    "done": ["Music lover: Music makes everything better. Even whatever's going on in this town."]}}
SECRETARY = {"text": "Mayor's secretary", "action": "EVENT", "condition": TAKEOVER, "flag_condition": "not xd_secretary",
             "event": {"stages": [
                 {"requires": ["not:has_item:MUSIC_DISC"], "lines": ["Secretary: The mayor is busy. Very busy. Upstairs is off limits.",
                                                                     "Secretary: It's so dull in here... If only I had some music."]},
                 {"requires": ["has_item:MUSIC_DISC"], "flag": "xd_secretary", "take_item": {"MUSIC_DISC": 1},
                  "lines": ["Secretary: A Music Disc? How lovely! ...La la la...",
                            "While she dances, you slip upstairs. The mayor's office is empty. A note lies on the desk:",
                            "'Justy - Cipher means to take Phenac. They'll wear our faces. I must-' The note stops there. The mayor is nowhere to be seen.",
                            "Secretary: Snooping, are we? Then you've seen too much!"],
                  "battle": T("xd:Story:91", dialogue={"player_won": ["Cipher Peon Pellim: My disguise... Fenton, get the kid!"]})}]}}
FENTON = _fight("Cipher Peon Fenton", "xd:Story:92", "xd_fenton", "Cipher Peon Fenton: Nobody leaves the mayor's house!",
                "Cipher Peon Fenton: Ugh. The Justys will get you!", condition=["xd_secretary", "not:orre_snattle_phenac"])
GATE_LADY = {"text": "Gate lady", "action": "EVENT", "condition": "xd_exol_beaten", "event": {"stages": [
    {"requires": ["not:xd_gate_cds"], "flag": "xd_gate_cds", "gift_item": {"BATTLE_CD_01": 1, "BATTLE_CD_07": 1, "BATTLE_CD_20": 1},
     "lines": ["Gate lady: Welcome to Phenac! Everything is perfectly normal here. Have some Battle CDs. Go to Realgam Tower and play them!",
               "You got Battle CDs 01, 07 and 20!"]}],
    "done": ["Gate lady: Everything's perfectly normal. Perfectly."]}}
IMPOSTORS = [("Resix", "xd:Story:118", "19"), ("Blusix", "xd:Story:119", "08"), ("Browsix", "xd:Story:120", "16"),
             ("Yellosix", "xd:Story:121", "28"), ("Purpsix", "xd:Story:122", None), ("Greesix", "xd:Story:123", None)]


def _impostor(name, key, cd):
    won = [f"'Justy': Our perfect disguise! ...I'm {name}, of the Hexagon Brothers. Curses!"]
    if cd:
        won.append(f"He dropped Battle CD {cd}!")
    rewards = {"balls": 0}
    if cd:
        rewards[f"BATTLE_CD_{cd}"] = 1
    return {"text": f"'Justy' ({name})", "action": "EVENT", "condition": ["xd_fenton", "not:orre_snattle_phenac"],
            "flag_condition": f"not xd_impostor_{name.lower()}",
            "event": {"flag": f"xd_impostor_{name.lower()}", "lines": ["Justy: I'm Justy of the Pre Gym! ...Probably. Battle me!"],
                      "battle": T(key, rewards=rewards, dialogue={"player_won": won})}}


ERTLIG = _fight("Cipher Peon Ertlig", "xd:Story:96", "xd_ertlig", "Cipher Peon Ertlig: The stadium's closed. Snattle's orders!",
                "Cipher Peon Ertlig: Fine, go. You'll regret it.", condition=["xd_fostin", "not:orre_snattle_phenac"])
STADIUM = [("Cipher Peon Exinn", "xd:Story:88", "xd_st_exinn", "Cipher Peon Exinn: Ambush! Get the kid!"),
           ("Cipher Peon Gonrag", "xd:Story:89", "xd_st_gonrag", "Cipher Peon Gonrag: Two on one - sort of!"),
           ("Cipher Peon Ezin", "xd:Story:101", "xd_st_ezin", "Cipher Peon Ezin: The stadium belongs to Snattle now!"),
           ("Cipher Peon Faltly", "xd:Story:102", "xd_st_faltly", "Cipher Peon Faltly: You won't reach the boss!"),
           ("Cipher Peon Egrog", "xd:Story:103", "xd_st_egrog", "Cipher Peon Egrog: Snattle sent me to deal with you. Personally!")]
PHENAC_XD_FOLK = [("Fun Old Man Eroll", "xd:Story:105", "Eroll: Phenac's back to normal! Let's celebrate with a battle!"),
                  ("Cooltrainer Equin", "xd:Story:106", "Equin: The Pre Gym's open again, and I'm in top form!"),
                  ("Cooltrainer Quelor", "xd:Story:129", "Quelor: Fancy a match by the water?"),
                  ("Cooltrainer Teslor", "xd:Story:130", "Teslor: Phenac's trainers are the best in Orre. Prove me wrong!"),
                  ("Supertrainer Nopel", "xd:Story:131", "Nopel: Super by name, super by nature!"),
                  ("Matron Kalus", "xd:Story:132", "Kalus: My Plusle and Minun want to play!")]
CD_15 = {"text": "Runner's Castform", "action": "EVENT", "condition": "orre_snattle_phenac", "flag_condition": "not got_battle_cd_15",
         "event": {"flag": "got_battle_cd_15", "gift_item": {"BATTLE_CD_15": 1},
                   "lines": ["The runner's Castform has something stuck to it... Battle CD 15! 'Take it,' he puffs, 'I don't play.'"]}}

HORDEL = {"text": "Researcher Hordel", "action": "EVENT", "condition": "xd_pregym_freed", "event": {"stages": [
    {"requires": ["not:xd_hordel"], "flag": "xd_hordel",
     "gift_shadow": {"id": 9357, "level": 55},
     "lines": ["Hordel: You're {player_name}? I worked for Cipher... until I saw what they do. I ran, and took this one with me.",
               "Hordel: A Togepi from their factory. Its heart is shut. Please - open it.",
               "Hordel: And one more thing: Team Snagem is back in their old hideout, out in the desert. I'll mark it on your map."]}],
    "done": ["Hordel: Take good care of that Togepi."]}}
MIROR_OUTSKIRT = {"text": "Wanderer Miror B.", "action": "EVENT", "condition": "xd_pregym_freed", "flag_condition": "not xd_miror_outskirt",
                  "event": {"flag": "xd_miror_outskirt", "lines": ["Folly: Miror B.! It's that kid again!",
                                                                    "Miror B.: The snagger! Let's see if you can keep up with THIS rhythm!"],
                            "battle": T("xd:Story:134", music="orre/miror_b_battle", dialogue={
                                "player_won": ["Miror B.: My Nosepass... You snagged it?! Folly, Trudly - we dance away!"]})}}
WILLIE_AGAIN = _fight("Rider Willie (again)", "xd:Story:135", "xd_willie_again",
                      "Willie: You again! I've been training. Four Pokemon this time!", "Willie: Wild... You're the real deal.",
                      condition="xd_hordel")


def _xd6(maps):
    if "PHENAC_CITY" in maps:
        m = maps["PHENAC_CITY"]
        _set_people(m, {_free_spot(m, (42, 31)): GATE_LADY, _free_spot(m, (27, 40)): ERTLIG,
                        _free_spot(m, (24, 54)): CD_15})
        for i, (name, key, cd) in enumerate(IMPOSTORS):
            _set_people(m, {_free_spot(m, (14 + 5 * i, 46)): _impostor(name, key, cd)})
        for i, (text, key, intro) in enumerate(PHENAC_XD_FOLK):
            _set_people(m, {_free_spot(m, (12 + 5 * i, 58)): _fight(text, key, f"xd_ph_{key.split(':')[-1]}", intro,
                                                                    f"{text.split()[-1]}: Well battled!", condition="orre_snattle_phenac")})
        rooms = m["rooms"]
        _set_people(rooms["house_ne"], {_free_spot(rooms["house_ne"]): MUSIC_MAN})
        _set_people(rooms["house_ne"], {_free_spot(rooms["house_ne"], (2, 3)): {
            "text": "Battle CD 10", "action": "EVENT", "flag_condition": "not got_battle_cd_10",
            "event": {"flag": "got_battle_cd_10", "gift_item": {"BATTLE_CD_10": 1}, "lines": ["On the bookshelf: Battle CD 10!"]}}})
        _set_people(rooms["mayor"], {_free_spot(rooms["mayor"]): SECRETARY})
        _set_people(rooms["mayor"], {_free_spot(rooms["mayor"], (2, 3)): FENTON})
        for n, where in (("12", "On the mayor's bookshelf:"), ("27", "Under the mayor's desk:"), ("32", "In the mayor's cabinet:")):
            r = rooms["mayor_2f"]
            _set_people(r, {_free_spot(r, (3 + int(n) % 7, 4)): {
                "text": f"Battle CD {n}", "action": "EVENT", "condition": "xd_secretary", "flag_condition": f"not got_battle_cd_{n}",
                "event": {"flag": f"got_battle_cd_{n}", "gift_item": {f"BATTLE_CD_{n}": 1}, "lines": [f"{where} Battle CD {n}!"]}}})
        gym = rooms["arena"]   # (R2: the stadium itself; "gym" is its new lobby)
        for i, (text, key, flag, intro) in enumerate(STADIUM):
            _set_people(gym, {_free_spot(gym, (6 + 3 * i, 12)): _fight(text, key, flag, intro, f"{text.split()[-1]}: Ugh...",
                                                                       condition=["xd_ertlig", "not:orre_snattle_phenac"])})
        _set_people(gym, {_free_spot(gym, (14, 6)): {
            "text": "Battle CD 44", "action": "EVENT", "condition": "orre_snattle_phenac", "flag_condition": "not got_battle_cd_44",
            "event": {"flag": "got_battle_cd_44", "gift_item": {"BATTLE_CD_44": 1}, "lines": ["On the empty stadium's floor: Battle CD 44!"]}}})
    if "PRESTIGE_PRECEPT_CENTER" in maps:
        fl = maps["PRESTIGE_PRECEPT_CENTER"]["floors"]
        down = _link_to(fl[0], 1)
        if down:
            fl[0]["barred"] = list(fl[0].get("barred") or []) + [
                {"tiles": [list(down)], "look": "unseen", "until": {"flag_condition": "orre_snattle_phenac"},   # (his key: a battle's also_flags aren't set)
                 "lines": ["The lift to the basement is locked. It needs an Elevator Key."]}]
    if "OUTSKIRT_STAND" in maps:
        m = maps["OUTSKIRT_STAND"]
        _set_people(m, {_free_spot(m, (30, 20)): MIROR_OUTSKIRT, _free_spot(m, (24, 20)): WILLIE_AGAIN})
        _set_people(m["rooms"]["diner"], {_free_spot(m["rooms"]["diner"]): HORDEL})


# ================================================================== batch 7b: Realgam Tower's lobby (BATCH_7B.md)
# Colosseum part 8: the trainers in the tower's lobby (Aline, Luper, Klest, raised to fit); the door up to the rooftop arena
# stays shut until Gonzap is beaten inside (the way up is the roof lift at the end of the Tower Halls).
REALGAM_LOBBY = [("Hunter Aline", "col:418", "col_aline_realgam", "Hunter Aline: Realgam's lobby is my hunting ground!", "Hunter Aline: You got me."),
                 ("St.Performer Luper", "col:419", "col_luper_realgam", "St.Performer Luper: Welcome to the greatest show in Orre!",
                  "St.Performer Luper: The show's over..."),
                 ("Bandana Guy Klest", "col:420", "col_klest_realgam", "Bandana Guy Klest: Nobody gets to the tower without going through me!",
                  "Bandana Guy Klest: Okay, okay, go through.")]


def _col7b(maps):
    if "REALGAM_TOWER" not in maps:
        return
    room = maps["REALGAM_TOWER"]["rooms"]["realgam"]
    for i, (text, key, flag, intro, won) in enumerate(REALGAM_LOBBY):
        _set_people(room, {_free_spot(room, (4 + 6 * i, 6)): _fight(text, key, flag, intro, won)})
    up = next(((x, y) for y, row in enumerate(room["art"]) for x, c in enumerate(row) if c == "^"), None)
    if up:
        room["barred"] = list(room.get("barred") or []) + [
            {"tiles": [list(up)], "flag": "col_gonzap_realgam", "look": "unseen",
             "lines": ["The door to the arena on the roof is locked. Cipher's people must be inside the tower."]}]


# ================================================================== batch 8a: before Citadark Isle (BATCH_8A.md)
# XD part 7: after the title, Krane shows Wes a secret staircase in the lab and gives him the Master Ball (one in the game) -
# for XD001, whose heart only the Purify Chamber can open (8b).
KRANE_MASTER_BALL = {"text": "Professor Krane (the stairs)", "action": "EVENT", "condition": "xd_gorigan_beaten", "event": {"stages": [
    {"requires": ["not:xd_master_ball"], "flag": "xd_master_ball", "gift_item": {"MASTER_BALL": 1},
     "lines": ["Professor Krane: {player_name}, come with me. There's a staircase here even Lily rarely uses.",
               "Professor Krane: Cipher has gathered on Citadark Isle. Greevil's 'XD001' - our readings say it's a Shadow Pokemon unlike any other.",
               "Professor Krane: This is a Master Ball. There's only one. It catches any Pokemon without fail. Save it for XD001.",
               "Professor Krane: Makan and Perr have a robot at Gateon Port that can cross the sea. Good luck, {player_name}."]}],
    "done": ["Professor Krane: Save the Master Ball for XD001. Its heart... I fear only the Purify Chamber could reach it."]}}


def _xd8a(maps):
    if "POKEMON_HQ_LAB" in maps:
        lab = maps["POKEMON_HQ_LAB"]["rooms"]["lab"]
        _set_people(lab, {_free_spot(lab, (6, 4)): KRANE_MASTER_BALL})



# ================================================================== batch 8b: XD after Greevil (BATCH_8B.md)
# XD part 8 (Jordan 11-21: XD's nine-chamber Purify Chamber, all seven Orre Colosseum rounds, raised to fit, the Lucky Egg
# quest with the Voice Cases only). Eagun battles you outside the HQ Lab and the Colosseum opens; its desk runs the rounds
# (src/world/xd_colosseum.py); Miror B. waits on Gateon's harbour wall with the last Shadow Pokemon (src/world/xd_post.py);
# Beluh's quest: Senilor's silent Wobbuffet, the old man's translators, Kaminko's Voice Cases (his stages: obatch8b.py).
EAGUN_LAB = {"text": "Eagun", "action": "EVENT", "condition": "xd_greevil_beaten", "event": {"stages": [
    {"flag": "xd_eagun_lab",
     "lines": ["Eagun: {player_name}! I heard you beat Greevil himself. Then you've earned this - one more battle, with me!",
               "Eagun: My Pikachu and I haven't lost our spark. Show me everything!"],
     "battle": T("xd:Story:222", dialogue={"player_won": [
         "Eagun: Ha! You and your Pokemon fight as one. Listen - the Orre Colosseum is running again.",
         "Eagun: Seven rounds, the strongest trainers in Orre. Go and show them what you've shown me."]})}],
    "done": ["Eagun: The Orre Colosseum's waiting for you, {player_name}. Beluh sends her love."]}}

COLO_FINALS = {1: "Lovrina: {player_name}! I'm here to win, not to make friends. My new Pokemon are perfect!",
               2: "Snattle: The next governor of Orre doesn't lose twice. Watch me!",
               3: "Gorigan: Hmph. The Colosseum's honest work. Let's see if you can beat me fair and square.",
               4: "Chobin: My Robo Groudon's at home, but my Pokemon came! Prepare yourself!",
               5: "Gonzap: Snagem's turned over a new leaf, kid. Doesn't mean I've gone soft!",
               6: "Ardos: Grand Master Greevil is gone. My strength isn't. Face it!",
               7: "Eldes: I hoped we'd meet here. No Cipher, no orders - only a battle. I won't hold back."}


def _colo_rounds():
    out = []
    for r in range(1, 8):
        rnd = []
        for m in range(1, 5):
            b = T(f"xdcolo:{r}:{m}")
            if m == 4:
                b["intro"] = [COLO_FINALS[r]]
                b["is_boss_battle"] = True
            rnd.append(b)
        out.append(rnd)
    return out


COLOSSEUM_DESK = {"text": "Colosseum desk", "action": "EVENT", "condition": "xd_greevil_beaten", "event": {
    "xd_colosseum": {"rounds": _colo_rounds()},
    "lines": ["Clerk: Welcome to the Orre Colosseum! Seven rounds, four battles each, the toughest trainers in Orre."]}}

MIROR_LAST = {"text": "Wanderer Miror B.", "action": "EVENT", "condition": "xd_miror_last_due", "event": {"stages": [
    {"flag": "xd_miror_last",
     "lines": ["Miror B. strikes a pose at the lighthouse door. Miror B.: Ooh, look who found me! Every Shadow Pokemon in Orre, snagged... all but one.",
               "Miror B.: Remember the Key Lair? While you were busy, I took the best one for myself. Dragonite!",
               "Miror B.: It's the last Shadow Pokemon there is. Want it? Then out-dance me!"],
     "battle": T("xd:Story:221", music="orre/miror_b_battle", is_boss_battle=True, dialogue={"player_won": [
         "Miror B.: No! My final number, ruined! I'm out of here!",
         "Miror B. dashes for the stairs... and stops. He pulls a tiny gadget out of his hair.",
         "Miror B.: A bug? In MY hair? So that's how you kept finding me! Hmph!",
         "He crushes it under his heel and dances off."]})}],
    "done": ["The harbour wall is empty. The wind smells of the sea."]}}

SENILOR = {"text": "Senilor", "action": "EVENT", "event": {"stages": [
    {"requires": ["xd_le_asked"], "flag": "xd_le_senilor",
     "lines": ["Senilor: Beluh sent you? Bless her. It's my Wobbuffet - it hasn't made a sound in days.",
               "Senilor: My son put a little machine on it, a 'Pokemon Translator'. An old man at the Pokemon Center gave it to us.",
               "Senilor: Since then: nothing. Not a 'wob', not a 'buffet'."]},
    {"requires": ["xd_le_kaminko_done"], "flag": "xd_le_spoken",
     "lines": ["You tell Senilor what Dr. Kaminko said: no machine can do it - Wobbuffet needs to hear its own trainer.",
               "Senilor: My voice? Well... I'll try. Wobbuffet! Hey! It's me, you big blue lump!",
               "Wobbuffet: ...Wob... WOBBUFFET!",
               "Senilor: It spoke! Ha ha! Thank you, {player_name}. Go and tell Beluh the good news."]}],
    "done": ["Senilor: My Wobbuffet won't leave my side these days."]}}

WOBBUFFET = {"text": "Wobbuffet", "action": "EVENT", "event": {"stages": [
    {"requires": ["xd_le_vc4", "has_item:VOICE_CASE"], "flag": "xd_le_c4", "take_item": {"VOICE_CASE": 1},
     "lines": ["You play the Voice Case for Wobbuffet. A recorded 'Wobbuffet!' fills the room...",
               "...Wobbuffet sways. Not a sound. The Voice Case didn't work on it!"]}],
    "done": ["Wobbuffet sways."]}}


def _voice(text, n, poke_said):
    """A Pokemon stuck in a translator: Kaminko's Voice Case n frees it."""
    return {"text": text, "action": "EVENT", "condition": "xd_le_asked", "event": {"stages": [
        {"requires": [f"xd_le_vc{n}", "has_item:VOICE_CASE"], "flag": f"xd_le_c{n}", "take_item": {"VOICE_CASE": 1},
         "lines": [f"You play the Voice Case. The machine on {text} clicks off and drops away.", poke_said]}],
        "done": [f"{text} is silent. A small machine is stuck to it."]}}


# Gateon's Eevee expert (11-19, "every species in one playthrough": XD's stones): a stone a day for Vaporeon, Jolteon or
# Flareon
EEVEE_EXPERT = {"text": "Eevee expert", "action": "EVENT", "event": {
    "lines": ["I know all about Eevee! It can become so many things.",
              "Here, take a stone to evolve yours. Which one? Come back tomorrow for another!"],
    "flag": "xd_eevee_stone_day",
    "choose": {"flag": "xd_eevee_stone", "ask": "WHICH STONE?", "gift": True,
               "choices": [{"text": "WATER STONE (Vaporeon)", "value": "WATER_STONE"},
                           {"text": "THUNDER STONE (Jolteon)", "value": "THUNDER_STONE"},
                           {"text": "FIRE STONE (Flareon)", "value": "FIRE_STONE"}],
               "cancel": ["Come back when you've made up your mind!"],
               "done": ["Eevee in the sun becomes Espeon, under the moon Umbreon - if it really loves you!"]},
    "done": ["That's today's stone! Come back tomorrow and I'll have another for you."],
    "daily": True}}


VOICES = [("Combusken", 1, "Combusken: Combusken! Busken!"), ("Poochyena", 2, "Poochyena: Yip! Yip yip!"),
          ("Taillow", 3, "Taillow: Tail-low!"), ("Shroomish", 5, "Shroomish: Shroo-mish!")]


def _voiced(text, n, poke_said):
    """Once freed it chatters (the "done" line follows the flag)."""
    v = _voice(text, n, poke_said)
    v["event"]["then"] = {"lines": [poke_said], "requires": [f"xd_le_c{n}"], "fail": v["event"]["done"]}
    return v


TRANSLATOR_MAN = {"text": "Old man", "action": "EVENT", "condition": "xd_le_asked", "event": {"stages": [
    {"requires": ["xd_le_senilor"], "flag": "xd_le_oldman",
     "lines": ["Old man: The translators? Aye, I handed a few out. Got them from a Dr. Kaminko, years ago.",
               "Old man: Where he lives I couldn't tell you. Somewhere out in the desert, on the way to Gateon..."]}],
    "done": ["Old man: I meant well, giving those out. Truly."]}}

LOTAD = {"text": "Lotad", "action": "EVENT", "condition": "xd_le_asked", "event": {"stages": [
    {"requires": ["xd_le_spoken"], "flag": "xd_le_lotad",
     "lines": ["Lotad floats by the falls, silent. You look it over for a translator...",
               "...There isn't one. This Lotad is just a very quiet Pokemon!"]}],
    "done": ["Lotad bobs on the water without a sound."]}}


def _xd8b(maps):
    if "POKEMON_HQ_LAB" in maps:
        m = maps["POKEMON_HQ_LAB"]
        _set_people(m, {(9, 12): EAGUN_LAB})   # (the lab's front step: the strip is only three tiles wide)
    if "ORRE_COLOSSEUM" in maps:
        g = maps["ORRE_COLOSSEUM"]["rooms"]["gym"]   # (R2: in the new lobby, beside the tournament's receptionist)
        _set_people(g, {_free_spot(g, (10, 6)): COLOSSEUM_DESK})
    if "GATEON_PORT" in maps:
        g = maps["GATEON_PORT"]   # (Jordan 11-21: a lighthouse at the north end of the east harbour wall - the slim white one from
        #  the Journeys Johto sheet, assets/tiles/orre_ride/lighthouse.png, 3 x 8 tiles; Miror B. waits at its door: XD's tower)
        #  It stands on the sandy wall's north tip (x60-62, rows 10-17: a full-map layer, orre_ride/gateon_lighthouse.png); the wall
        #  itself (x61-62, rows 18-33) is opened to walk up to it.
        for y in range(18, 34):
            row = g["art"][y]
            g["art"][y] = row[:61] + "".join("." if row[x] == "c" else row[x] for x in (61, 62)) + row[63:]
        g["overheads"] = list(g.get("overheads") or []) + [{"kind": "picture", "f": "orre_ride/gateon_lighthouse.png", "at": [0, 0], "size": [75, 70]}]
        _set_people(g, {(61, 18): MIROR_LAST})
        _set_people(g["rooms"]["house_west"], {(8, 5): EEVEE_EXPERT})   # (11-24: back - Gateon's R3 rebuild dropped him; he was
        #  written into the built files on 11-19, so he lives here now)
    if "AGATE_VILLAGE" in maps:
        a = maps["AGATE_VILLAGE"]
        rooms = a["rooms"]
        _set_people(rooms["house_centre"], {(2, 5): SENILOR, (3, 4): WOBBUFFET})
        _set_people(rooms["house_west"], {_free_spot(rooms["house_west"], (6, 6)): _voiced(*VOICES[0])})
        _set_people(a, {(37, 13): _voiced(*VOICES[1]), (66, 8): _voiced(*VOICES[2]), (70, 23): LOTAD})
        _set_people(rooms["center"], {_free_spot(rooms["center"], (3, 6)): TRANSLATOR_MAN})
    if "XD_ONBS" in maps:
        lobby = maps["XD_ONBS"]["floors"][0]
        _set_people(lobby, {(12, 3): dict(_voiced(*VOICES[3]), condition="xd_le_vc5")})   # (by the lobby's front desk)



# ================================================================== batch 8c: Colosseum after the title (BATCH_8C.md)
# Colosseum walkthrough part 9 (Jordan 11-21: raised to fit; the Deep Colosseum as rounds at a desk; Colosseum's missed
# Shadows go to the Snagem raid; Realgam rematches any time, healed). Nett's tip (obatch8c.py) -> the kid behind Pyrite's
# bookcase -> Cail -> the Snagem raid (the Shadows you missed, a coloured peon, six grunts) -> Nett -> Gurks on the Junk
# Shop balcony -> the Lab's coloured peon -> Biden's Smeargle, Agrev's Ursaring, Gonzap's Skarmory and the D-Disk -> the
# Deep Colosseum (The Under's floating platform). Fein at the Outskirt Stand once every other Colosseum Shadow is snagged.
def C(i, **kw):
    return T(f"c8c:{i}", **kw)


def C2(with_shadow, without, flag, **kw):
    """Colosseum's second chance: the team with the Shadow you missed, else the one without it."""
    b = C(with_shadow, **kw)
    b["if_snagged"] = {"flag": flag, "battle": C(without, **kw)}
    return b


def _spot(m, near=None):
    """_free_spot, else any open tile with nobody beside it (narrow floors)."""
    try:
        return _free_spot(m, near)
    except ValueError:
        art = m["art"]
        taken = set(_people_at(m))
        cx, cy = near or (len(art[0]) // 2, len(art) // 2)
        ok = [(abs(x - cx) + abs(y - cy), y, x) for y in range(1, len(art) - 1) for x in range(1, len(art[0]) - 1)
              if art[y][x] == "." and all(abs(x - tx) + abs(y - ty) > 1 for tx, ty in taken)
              and sum(art[y + dy][x + dx] == "." for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 3]
        _d, y, x = min(ok)
        return (x, y)


CAIL_POST = {"text": "Rogue Cail", "action": "EVENT", "event": {"stages": [
    {"requires": ["not:orre_heard_cail"], "lines": ["Rogue Cail: Get lost. I don't battle nobodies."]},
    {"requires": ["orre_heard_cail"], "flag": "orre_beat_cail",
     "lines": ["Rogue Cail: So you heard about my prize? Win, and maybe you get to see it up close."],
     "battle": T("col:93", dialogue={"player_won": ["Rogue Cail: Tch. Fine, fine."]})},
    {"requires": ["col_post_kid"], "flag": "col_cail_post",
     "lines": ["Rogue Cail: Yeah, I battled a guy with one of those creepy Pokemon. So what? Beat me and I'll tell you more."],
     "battle": C2(441, 442, "snagged_shadow_furret", dialogue={"player_won": [
         "Rogue Cail: Alright, alright. He was one of Snagem's - they've moved back into their old hideout in the desert.",
         "Rogue Cail: Half the trainers you let get away are holed up there too, if you ask me."]})}],
    "done": ["Rogue Cail: Don't you have somewhere else to be?"]}}

PYRITE_KID = {"text": "Kid (behind the bookcase)", "action": "EVENT", "condition": "orre_part2", "event": {"stages": [
    {"requires": ["col_post_nett"], "flag": "col_post_kid",
     "lines": ["Kid: Shh! I'm hiding. I saw Cail battle a guy with a really scary Pokemon - all dark and glowing.",
               "Kid: Cail's down at the bottom of town. Don't tell him I told you!"]}],
    "done": ["Kid: This is my secret spot. Go away!"]}}

RAID_MISSED = [   # (Colosseum's missed Shadows, back with their trainers: shown only while still missed)
    ("Cipher Peon Nore", 102, "snagged_shadow_yanma"), ("Cipher Peon Skrub", 199, "snagged_shadow_hitmontop"),
    ("Cipher Peon Kloak", 323, "snagged_shadow_ledian"), ("Hunter Frena", 332, "snagged_shadow_gligar"),
    ("Chaser Liaks", 335, "snagged_shadow_stantler"), ("Bodybuilder Lonia", 338, "snagged_shadow_piloswine"),
    ("Rider Nelis", 341, "snagged_shadow_sneasel"), ("Cipher Peon Baila", 410, "snagged_shadow_sunflora"),
    ("Cipher Peon Arton", 413, "snagged_shadow_delibird"), ("Cipher Peon Dioge", 416, "snagged_shadow_heracross")]
RAID_GRUNTS = [("Team Snagem Niver", 473), ("Team Snagem Fuston", 474), ("Team Snagem Colas", 475), ("Team Snagem Crudo", 476),
               ("Team Snagem Driton", 477), ("Team Snagem Rions", 478)]


def _raid_missed(text, i, flag):
    return {"text": text, "action": "EVENT", "condition": ["col_cail_post", f"not:{flag}"], "event": {"stages": [
        {"flag": f"col_raid_{i}", "lines": [f"{text.split()[-1]}: You! You let this one get away once. Not this time!"],
         "battle": C(i, dialogue={"player_won": [f"{text.split()[-1]}: Ugh... I should have stayed lost."]})}],
        "done": [f"{text.split()[-1]}: ..."]}}


def _raid_grunt(text, i):
    return _fight(text, f"c8c:{i}", f"col_raid_{i}", f"{text.split()[-1]}: Snagem's back in business! Who let you in?",
                  f"{text.split()[-1]}: Business is bad...", condition="col_cail_post")


def _coloured_peon(teams, cond):
    return {"text": "Coloured Cipher Peon", "action": "EVENT", "condition": cond, "event": {
        "col_peon": teams, "lines": [], "done": ["The peon's gone."]}}


PEON_SNAGEM = {k: C(i) for k, i in (("bayleef", 816), ("quilava", 812), ("croconaw", 814))}
PEON_LAB = {k: C(i) for k, i in (("bayleef", 817), ("quilava", 813), ("croconaw", 815))}

GURKS_POST = {"text": "Gurks", "action": "EVENT", "condition": "col_post_nett2", "event": {"stages": [
    {"flag": "col_gurks_post",
     "lines": ["Gurks: Nett sent you? Yeah, I know things. Battle me first - my Wailord have been bored for weeks."],
     "battle": C(456, dialogue={"player_won": [
         "Gurks: Okay, okay! I battled a peon in a bright suit down here - with one of those Shadow Pokemon.",
         "Gurks: Don't bother looking for him in The Under, though. He was headed for that old lab out past Phenac."]})}],
    "done": ["Gurks: Nice view from up here, huh?"]}}

SNAGEM_LATE = [   # (after Gurks: two Shadows that weren't anywhere before, and Gonzap with his Skarmory)
    ("Snagem's Biden", 460, "snagged_shadow_smeargle", "Biden: The boss let me keep a special Smeargle. Wanna see what it can draw?"),
    ("Snagem's Agrev", 461, "snagged_shadow_ursaring", "Agrev: My Ursaring's been waiting for a fight. A dark one.")]
GONZAP_POST = {"text": "Snagem Head Gonzap", "action": "EVENT", "condition": "col_gurks_post", "event": {"stages": [
    {"flag": "col_gonzap_post",
     "lines": ["Gonzap: You again? Fine. Snagem's mine again and I'm not giving it up. Let's settle it!"],
     "battle": C2(426, 427, "snagged_shadow_skarmory", is_boss_battle=True, rewards={"balls": 10, "D_DISK": 1}, dialogue={"player_won": [
         "Gonzap: Ha... you never change. Here - I took this off a Cipher crate. A D-Disk.",
         "Gonzap: Slot it into that floating thing in The Under. They say it goes down to a colosseum nobody's seen."]})}],
    "done": ["Gonzap: Go see what's down there. Tell me if it's worth snagging."]}}

DEEP_FINALS = {1: "Miror B.: Ooh, the deepest dance floor in Orre! Let's boogie!",
               2: "Dakim: Down here, nobody holds back. Crush or be crushed!",
               3: "Venus: Even here, I'm the star. Shall we put on a show?",
               4: "Ein: My research continues, even in the dark. You'll make a fine test.",
               5: "Agnol: So. You've come all the way down. I am the Deep King. Kneel - or battle."}
DEEP_ADMINS = [(165, 166, "snagged_shadow_sudowoodo"), (214, 215, "snagged_shadow_entei"), (329, 330, "snagged_shadow_suicune"),
               (406, 407, "snagged_shadow_raikou"), (378, 818, "snagged_shadow_shuckle")]
DEEP_THREE = [[363, 364, 365], [366, 367, 368], [369, 370, 371], [372, 373, 374], [375, 376, 377]]


def _deep_rounds():
    out = []
    for r, three in enumerate(DEEP_THREE):
        rnd = [C(i) for i in three]
        w, wo, flag = DEEP_ADMINS[r]
        last = C2(w, wo, flag, is_boss_battle=True)
        last["intro"] = [DEEP_FINALS[r + 1]]
        rnd.append(last)
        out.append(rnd)
    return out


DEEP_DESK = {"text": "Deep Colosseum desk", "action": "EVENT", "event": {
    "xd_colosseum": {"rounds": _deep_rounds(), "cleared": "col_deep_cleared", "open": "col_gonzap_post", "all_flag": "col_deep_all",
                     "name": "the Deep Colosseum",
                     "prizes": [[None, None], ["SKILL-SWAP", None], [None, None], ["DRAGON-CLAW", None], [None, "Deep King's Equal"]],
                     "money": [12000, 20936, 15000, 18118, 25000]},
    "lines": ["A cloaked figure: Welcome to the Deep Colosseum. Five rounds. The Deep King waits at the bottom of them."]}}

FEIN = {"text": "Shady man", "action": "EVENT", "condition": "col_fein_due", "event": {"stages": [
    {"flag": "col_fein",
     "lines": ["Shady man: Heh... You've snagged every Shadow Pokemon there is. Or so you think.",
               "He tears off his coat. Underneath: a Cipher uniform!",
               "Fein: Cipher Peon Fein, master of disguise! I kept one last Shadow Pokemon hidden - and you'll never take it!"],
     "battle": C(472, name="Cipher Peon Fein", sprite="orre_cipher_peon.png", is_boss_battle=True, music="orre/cipher_battle",
                 dialogue={"player_won": ["Fein: My disguise... my Togetic... all for nothing!"]})}],
    "done": ["The man in the coat is long gone."]}}


def _col8c(maps):
    if "PYRITE_TOWN" in maps:
        m = maps["PYRITE_TOWN"]
        spots = [s for s, p in _people_at(m).items() if isinstance(p, dict) and p.get("text") == "Rogue Cail"
                 and "orre_beat_cail" in str(p)]
        if spots:
            _set_people(m, {spots[0]: CAIL_POST})
        r = m["rooms"]["house_tower"]
        _set_people(r, {_spot(r, (16, 3)): PYRITE_KID})
    if "SNAGEM_HIDEOUT" in maps:
        fl = maps["SNAGEM_HIDEOUT"]["floors"]
        for k, (text, i, flag) in enumerate(RAID_MISSED):
            f = fl[1] if k < 6 else fl[2]
            _set_people(f, {_spot(f, (3 + 2 * k, 6 + k)): _raid_missed(text, i, flag)})
        for k, (text, i) in enumerate(RAID_GRUNTS):
            f = fl[0] if k < 2 else fl[1]
            _set_people(f, {_spot(f, (4 + 3 * k, 14)): _raid_grunt(text, i)})
        _set_people(fl[1], {_spot(fl[1], (7, 20)): _coloured_peon(PEON_SNAGEM, ["col_cail_post", "col_peon_due"])})
        for k, (text, i, flag, intro) in enumerate(SNAGEM_LATE):
            ev = {"text": text, "action": "EVENT", "condition": ["col_gurks_post", f"not:{flag}"], "event": {"stages": [
                {"flag": f"col_raid_{i}", "lines": [intro], "battle": C(i, dialogue={"player_won": [f"{text.split()[-1]}: Snagged... again."]})}],
                "done": ["..."]}}
            _set_people(fl[2], {_spot(fl[2], (6 + 8 * k, 12)): ev})
        _set_people(fl[2], {_spot(fl[2], (12, 6)): GONZAP_POST})
    if "THE_UNDER" in maps:
        f = maps["THE_UNDER"]["floors"][6]   # (the Junk Shop's 2F: its balcony)
        _set_people(f, {(14, 7): GURKS_POST})
    if "SHADOW_PKMN_LAB" in maps:
        f = maps["SHADOW_PKMN_LAB"]["floors"][3]   # (where Ein was)
        _set_people(f, {_spot(f): _coloured_peon(PEON_LAB, ["col_gurks_post", "col_peon_due"])})
    if "DEEP_COLOSSEUM" in maps:
        f = maps["DEEP_COLOSSEUM"]["floors"][0]
        f["art"] = [row.replace("X", ".") for row in f["art"]]   # (its standing trainers: now the desk's rounds)
        f["trainer_spots"] = []
        _set_people(f, {_spot(f, (13, 12)): DEEP_DESK})
    if "OUTSKIRT_STAND" in maps:
        m = maps["OUTSKIRT_STAND"]
        _set_people(m, {_spot(m, (36, 22)): FEIN})
    if "REALGAM_TOWER" in maps:
        room = maps["REALGAM_TOWER"]["rooms"]["realgam"]
        right = next(((x, y) for y, row in enumerate(room["art"]) for x, c in enumerate(row) if c == ">"), None)
        if right:   # (the Deep Colosseum is reached from The Under's floating platform, as in Colosseum)
            room["barred"] = list(room.get("barred") or []) + [
                {"tiles": [list(right)], "look": "unseen", "until": {"flag_condition": "col_never"},
                 "lines": ["A heavy door with no handle on this side."]}]

# ================================================================== batch 8d: Poke Snacks (BATCH_8D.md)
# XD's snack trays at the three Poke Spots (src/world/poke_snacks.py) and the Gateon herbalist whose Munchlax eats them.
SNACK_TRAY = {"text": "Snack tray", "action": "EVENT", "condition": "xd_spot_oasis", "event": {"snack_tray": True, "lines": []}}
HERBALIST = {"text": "Herbalist", "action": "EVENT", "event": {
    "munchlax_owner": True,
    "lines": ["Herbalist: My Munchlax got out again? And ate all your snacks? Oh dear, oh dear. Here - these are for you."],
    "done": ["Herbalist: I grow the herbs, my Munchlax eats everything else. If it ever raids a snack tray of yours, tell me!"]}}


def _xd8d(maps):
    for key in ("ORRE_POKE_SPOTS", "OASIS_POKE_SPOT", "CAVE_POKE_SPOT"):
        if key in maps:
            f = maps[key]["floors"][0]
            _set_people(f, {_spot(f): SNACK_TRAY})
    if "GATEON_PORT" in maps:
        r = maps["GATEON_PORT"]["rooms"]["house_small"]
        _set_people(r, {_spot(r): HERBALIST})

# ================================================================== Fly in Orre (Jordan 11-21: neither game has it)
# HM Fly lies by the Pyrite Colosseum's steps, so it's found before the first badge; it flies once the Pyrite Badge is
# won (src/world/hms.py USE_BADGE["ORRE"]).
HM_FLY_PYRITE = {"text": "HM Fly", "action": "EVENT", "flag_condition": "not orre_hm_fly", "event": {
    "flag": "orre_hm_fly", "gift_item": {"HM_FLY": 1},
    "lines": ["Someone dropped a disc by the Colosseum's steps. It's HM Fly!",
              "Win the Pyrite Colosseum's badge and your Pokemon can fly you to any town you've been to."]}}


def _orre_fly(maps):
    if "PYRITE_TOWN" in maps:
        m = maps["PYRITE_TOWN"]
        _set_people(m, {_spot(m, (24, 23)): HM_FLY_PYRITE})


# --------------------------------------------------------------------- R2 (11-23): the tournaments, walked
# Jordan 11-23: sign up at the lobby desk, stand on your side of the arena; each round's opponent walks in, you battle, they
# walk off, the next walks in; lose and you're back in the lobby, the tournament starts over; win the last: the award.
# src/world/orre_tournament.py runs it; here are the desk, the referee and the scenes. The lobbies of the Orre Colosseum and
# Phenac Stadium are Pyrite's (fan map 103), recoloured (assets/tiles/orre_ground/103_sand.png, 103_blue.png: made by
# kanto_handoff/orre_map_tools/tint.py).
#   area: (lobby room or None for the place's own map, desk spot, arena room, your spot, the opponent's spot, where they come
#          in from, the lobby picture or None, the Colosseum's name)
TOURNAMENTS = {
    "PYRITE_TOWN": ("gym", (7, 5), "arena", (7, 9), (7, 5), (5, 3), None, "the Pyrite Colosseum"),
    "UNDER_COLOSSEUM": (None, (10, 4), "gym", (7, 9), (7, 5), (5, 3), None, "the Under Colosseum"),
    "PHENAC_CITY": ("gym", (7, 5), "arena", (12, 11), (12, 7), (3, 3), "103_blue", "Phenac Stadium"),
    "ORRE_COLOSSEUM": ("gym", (7, 5), "arena", (13, 15), (13, 11), (13, 1), "103_sand", "the Orre Colosseum"),
    # (Realgam: the tower top is reached by the tower's own way, so its host starts the run where you stand; no desk)
    "REALGAM_TOWER": (None, None, "colosseum", (5, 10), (5, 7), (5, 3), None, "Cipher's Colosseum"),
}
# XD's Realgam Colosseum (R2, Jordan 11-23: the same arena, under XD's name, its own flag): four rounds of four at the disc's
# Lv 47 (Part 2's stage; the disc's Lv 40), open once you reach XD's Snagem Hideout (Mayor Trest's message); rounds at a desk, as XD's Orre Colosseum's.
XD_REALGAM_DESK = {"text": "Realgam Colosseum desk", "action": "EVENT", "condition": "visited_SNAGEM_HIDEOUT", "event": {
    "xd_colosseum": {"rounds": [[T(f"xdrealgam:{r}:{m}", **({"is_boss_battle": True} if m == 4 else {})) for m in range(1, 5)]
                                for r in range(1, 5)],
                     "cleared": "xd_realgam_cleared", "open": "visited_SNAGEM_HIDEOUT", "all_flag": "xd_realgam_all",
                     "name": "the Realgam Colosseum", "money": [3000, 4000, 5000, 6000]},
    "lines": ["Clerk: Welcome to the Realgam Colosseum! Four rounds, four battles each. Every team here is Lv 47."]}}
RECEPTIONIST_SHEET = "orre_npc_15.png"


def _walk_sheet(sprite, cls):
    """A trainer's walking sheet: dungeon_sprites.json's Orre trainers by battle picture, else a look of their class."""
    import json as _j
    import os as _o
    try:
        d = _j.load(open(_o.path.join("assets", "dungeon_sprites.json"), encoding="utf-8-sig"))
    except (OSError, ValueError):
        d = {}
    t = d.get("trainers_ORRE") or {}
    return t.get(sprite) or (d.get("trainers") or {}).get(sprite) or         {"GYM_LEADER": "orre_trainer_cooltrainer_m.png", "CHAMPION": "orre_trainer_ace_trainer.png"}.get(cls) or "orre_trainer_ace_trainer.png"


def _gym_of(area, key="gym"):
    import json as _j
    import os as _o
    try:
        return (_j.load(open(_o.path.join("assets", "orre_area_data.json"), encoding="utf-8"))["STORY_PROGRESSION"].get(area) or {}).get(key) or {}
    except (OSError, ValueError, KeyError):
        return {}


def _is_gym_option(area, text):
    import json as _j
    import os as _o
    try:
        opts = (_j.load(open(_o.path.join("assets", "orre_area_data.json"), encoding="utf-8"))["STORY_PROGRESSION"].get(area) or {}).get("explore_options") or []
    except (OSError, ValueError, KeyError):
        return False
    return next((o for o in opts if o.get("text") == text and str(o.get("action")).upper() == "GYM"), None)


def _tournament(maps):
    for area, (lobby, desk, arena, me, foe, door, pic, name) in TOURNAMENTS.items():
        if area not in maps:
            continue
        m = maps[area]
        lob = m["rooms"][lobby] if lobby else m
        ar = m["rooms"][arena]
        if pic:   # (the lobby's own colour)
            lob["roofs"]["_picture"]["f"] = f"orre_ground/{pic}.png"
            for o in lob.get("overheads") or []:
                if o.get("f", "").startswith("orre_top/103"):
                    o["f"] = f"orre_top/{pic}.png"
        if area == "PHENAC_CITY" and lobby:   # (the lobby's healing machine: Phenac's "Pokemon Center" person is its Center's nurse)
            lob["people"] = [{"text": "Healing machine", "action": "HEAL"} if p == "Pokemon Center" else p for p in lob.get("people") or []]
        if desk:
            _set_people(lob, {desk: {"text": "Receptionist", "action": "EVENT", "event": {
                "world": "orre_tournament",
                "signup": {"arena": arena, "at": list(me),
                           "lines": [f"Receptionist: Welcome to {name}! You're entered. Win every round to take the title.",
                                     "Receptionist: This way to the arena, please. Good luck!"],
                           "champion": [f"Receptionist: Our champion! {name} is yours. Come back any time."]}}}})
        back = [door[0], door[1]]
        scenes = list(ar.get("scenes") or [])
        # (S5, 11-24: Realgam's arena holds Evice's run in Part 1 and the Orre League in Part 2 - src/world/gym_swaps.py - each
        #  with its own walk-ins)
        variants = [(_gym_of(area), [])] if area != "REALGAM_TOWER" else             [(_gym_of(area), ["world:orre_skip:part1"]), (_gym_of(area, "gym_league"), ["world:orre_skip:part2"])]
        for gym, part in variants:
          rounds = list(gym.get("trainers") or []) + ([gym["leader"]] if gym.get("leader") else [])
          league = part == ["world:orre_skip:part2"]
          for k, t in enumerate(rounds):
            last = k == len(rounds) - 1
            who = t.get("name", "Your opponent")
            if league:
                call = [f"Host: The Champion of Orre! {who} takes the field!"] if last else [f"Host: Elite Four battle {k + 1}! {who} takes the field!"]
            else:
                call = [f"Referee: The final! {who} takes the field!"] if last else [f"Referee: Round {k + 1}! {who} takes the field!"]
            scenes.append({"trigger": "enter", "condition": [f"world:orre_tournament:round:{k}"] + part, "call": call,
                           "cast": [{"sheet": _walk_sheet(t.get("sprite"), t.get("class")), "from": back, "to": list(foe),
                                     "face": "d", "stay": True,
                                     "lines": list((t.get("dialogue") or {}).get("intro") or [f"{who}: Let's battle!"])[:1],
                                     "event": {"world": "orre_tournament", "fight": True}}]})
        scenes.append({"trigger": "enter", "condition": ["world:orre_tournament:game"], "cast": [],   # (the Gym's math game before
                       "call": ["Referee: Before the final, a challenge! Win it, and the champion takes the field."],  # the final, 11-23)
                       "event": {"world": "orre_tournament", "fight": True}})
        referee = {"world": "orre_tournament", "referee": True}   # (the Colosseum's host on the arena floor: no menu any more)
        if not desk:   # (no desk: the host signs you up where you stand)
            referee["signup"] = {"arena": arena, "at": list(me), "lines": [f"Host: Welcome to {name}! Take your place. Here they come!"],
                                 "champion": [f"Host: The champion of {name}! Come back once the Gym battles start again."]}
        def _ref(text):   # (the host, shown when the Colosseum's own option was: Phenac's waits for Snattle to go)
            o = _is_gym_option(area, text)
            r = {"text": text, "action": "EVENT", "event": dict(referee)}
            r.update({k: o[k] for k in ("condition", "flag_condition", "color") if o and k in o})
            if text.endswith("Orre League") and r["event"].get("signup"):   # (S5: the League's host, Part 2)
                r["event"]["signup"] = dict(r["event"]["signup"], lines=[
                    "Host: Welcome to the Orre League! Four of Orre's strongest, one after another - then the Champion.",
                    "Host: No rest between battles, and no turning back. Take your place!"],
                    champion=["Host: Our Champion! The Elite Four are always glad of a rematch."])
            return r
        for i, p in enumerate(ar.get("people") or []):
            if isinstance(p, str) and _is_gym_option(area, p):
                ar["people"][i] = _ref(p)
            elif isinstance(p, list):
                ar["people"][i] = [_ref(q) if isinstance(q, str) and _is_gym_option(area, q) else q for q in p]
        lost = {"trigger": "enter", "condition": ["world:orre_tournament:lost"], "cast": [
            {"sheet": RECEPTIONIST_SHEET, "from": back, "to": "player", "leave": "back",
             "lines": ["Receptionist: Bad luck! Your Pokemon have been healed. Sign up again whenever you're ready."]}],
            "event": {"world": "orre_tournament", "reset": True}}
        if lobby and desk:   # (back at the desk; the Under's lobby is its own map, Realgam's is the tower's: you walk out)
            lost["room"] = [lobby, desk[0], desk[1] + 1]
        scenes.append(lost)
        if area == "REALGAM_TOWER":   # (story rework S1, 11-24: Evice ends Part 1 - the five-year time skip, src/world/orre_skip.py)
            scenes.append({"trigger": "enter", "condition": ["world:orre_tournament:won", "world:orre_skip:part1"], "cast": [],
                           "call": ["The roof of Realgam Tower falls silent. Cipher's leader has fallen."],
                           "event": {"world": "orre_skip"}})
            scenes.append({"trigger": "enter", "condition": ["world:orre_tournament:won", "world:orre_skip:part2"], "cast": [],   # (S5)
                           "call": ["Host: Ladies and gentlemen... the new Champion of Orre, {player_name}!", "The whole tower roars!"],
                           "event": {"world": "orre_tournament", "done": True}})
        else:
            scenes.append({"trigger": "enter", "condition": ["world:orre_tournament:won"], "cast": [],
                           "call": [f"Referee: The champion of {name}!", "The crowd roars!"],
                           "event": {"world": "orre_tournament", "done": True}})
        ar["scenes"] = scenes
        if area == "REALGAM_TOWER":
            _set_people(ar, {_free_spot(ar, (2, 5)): XD_REALGAM_DESK})


# S6d (Jordan 11-24): Gym rematches after the League - Misty and Duking wait in their Colosseums' lobbies, Blaine and Erika in
# their garden, for their second teams once a day (src/world/orre_gym.py; the teams are each Leader's "orre_rematch").
REMATCH_SPOTS = [("PHENAC_CITY", "gym", "GYM LEADER MISTY", (10, 7)), ("PYRITE_TOWN", "gym", "GYM LEADER DUKING", (10, 7)),
                 ("AGATE_VILLAGE", "gym_2", "GYM LEADERS BLAINE & ERIKA", None),
                 ("AGATE_VILLAGE", "house_centre", "Move Tutor", None)]   # (R4, 11-24: XD's Agate Move Tutor, his 12 moves as TMs too)


def _rematch_spots(maps):
    for area, room, text, near in REMATCH_SPOTS:
        if area in maps and room in (maps[area].get("rooms") or {}):
            r = maps[area]["rooms"][room]
            _set_people(r, {_free_spot(r, near): text})


def apply(maps):
    if "OUTSKIRT_STAND" in maps:
        _outskirt(maps)
    if "PYRITE_TOWN" in maps:
        _pyrite(maps)
    if "AGATE_VILLAGE" in maps:
        _agate(maps)
    if "THE_UNDER" in maps:
        _under(maps)
    _xd5a(maps)
    _gateon_islands(maps)
    _battle_cds(maps)
    _xd5b(maps)
    _xd6(maps)
    _col7b(maps)
    _xd8a(maps)
    _xd8b(maps)
    _col8c(maps)
    _xd8d(maps)
    _orre_fly(maps)
    if "PHENAC_CITY" in maps:
        _phenac(maps)
        _past_guard(maps["PHENAC_CITY"])
    _tournament(maps)   # (last: after every place has its people)
    _rematch_spots(maps)
    # Story rework L1 (Jordan 11-24): every town battle at Kanto's level caps for its stage (orre_levels.py; the disc
    # levels stay the source, so every build maps them the same way)
    from . import orre_levels as _L
    import json as _j, os as _o
    _sp = _j.load(open(_o.path.join(_L._REPO, "assets", "orre_area_data.json"), encoding="utf-8"))["STORY_PROGRESSION"]
    _L.apply_towns(maps, list(_sp))
