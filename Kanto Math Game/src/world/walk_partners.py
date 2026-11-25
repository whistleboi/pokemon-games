"""Walking partners (Jordan 11-18, Pokemon Platinum's five): someone who walks with you through one place, a step behind
your Pokemon, and battles beside you. While they're with you (as in Platinum):
- a pair of trainers battles you and your partner together (a lone trainer stays one on one: Jordan, "pairs only");
- wild Pokemon come two at a time, you and your partner against both (src/states/battle_wild_double.py);
- after every battle your partner heals your team.
Each has Platinum's one Pokemon at Platinum's level, and stands where Platinum stands them (the map's figure, its own
overworld sheet pt_seven1-5). They leave where Platinum has them leave; going back out the way you came, they wait
where you met them and walk with you again when you come back.

Story flags: "walk_<key>" while walking with you, "walk_<key>_done" once they've said goodbye.
Hooks: dungeon.py (follow: COMPANIONS, wild doubles, leaving, a new floor), route_encounters.py and common.py
(trainer battles: trainer_options), common.py (the figure's event: {"walk_partner": key})."""

PARTNERS = {
    "cheryl": {"name": "Cheryl", "area": "ETERNA_FOREST", "figure": "Cheryl", "sheet": "pt_seven1.png", "sprite": "cheryl.png",
               "team": [113], "levels": [20],   # Chansey
               "join": ["Cheryl: Oh, hello! This forest is so dark, and Team Galactic is about...",
                        "Cheryl: Would you walk with me to the other side? I'll keep your Pokemon healthy on the way!",
                        "Cheryl joined you! She'll heal your team after every battle."],
               "chat": ["Cheryl: My Chansey and I will look after you. Just keep heading north!"],
               "end_exits": ["ETERNA_CITY"], "end_flag": None,   # (our forest opens straight onto Eterna City; Route 205 is where you came in)
               "farewell": ["Cheryl: We made it out! Thank you so much for walking with me.",
                            "Cheryl: Please take this. A Pokemon holding it grows fond of you faster."],
               "gift": {"SOOTHE_BELL": 1},
               "wait": ["Cheryl: Going back? I'll wait right here for you."]},
    "mira": {"name": "Mira", "area": "WAYWARD_CAVE", "figure": "Mira", "sheet": "pt_seven5.png", "sprite": "mira.png",
             "team": [64], "levels": [26],   # Kadabra
             "join": ["Mira: Um... Mira is lost. It's so dark, and Mira doesn't know the way out.",
                      "Mira: Will you take Mira to the exit? Mira's Kadabra will help you battle!",
                      "Mira joined you! She'll heal your team after every battle."],
             "chat": ["Mira: Mira is glad you found her. Kadabra, keep an eye out!"],
             "end_exits": "any", "end_flag": None,
             "farewell": ["Mira: We're out! Thank you! Mira will get stronger, so we can battle one day!"],
             "gift": {}, "wait": []},
    "riley": {"name": "Riley", "area": "IRON_ISLAND", "figure": "Team Up with Riley", "sheet": "pt_seven2.png", "sprite": "riley.png",
              "team": [448], "levels": [41],   # Lucario
              "join": ["Riley: Something's wrong deep in this mine. My Lucario senses it.",
                       "Riley: Let's go together. Lucario and I will battle beside you.",
                       "Riley joined you! He'll heal your team after every battle."],
              "chat": ["Riley: Lucario can sense people's aura. Whoever's down here, we're close."],
              "end_exits": [], "end_flag": "riley_iron_island_cleared",
              "farewell": [], "gift": {},
              "wait": ["Riley: Heading out for now? I'll keep watch here."]},
    "buck": {"name": "Buck", "area": "STARK_MOUNTAIN", "figure": "Buck", "sheet": "pt_seven4.png", "sprite": "buck.png",
             "team": [344], "levels": [63],   # Claydol
             "join": ["Buck: Spacemen, here? Those Galactic types are up to no good again!",
                      "Buck: I'm coming with you. Claydol and I have got your back!",
                      "Buck joined you! He'll heal your team after every battle."],
             "chat": ["Buck: It's hot in here! Good for training, though."],
             "end_exits": [], "end_floor": 3, "end_flag": None,
             "farewell": ["Buck: The air's different up ahead... Galactic's in there, I can feel it. Let's go!"],
             "gift": {}, "wait": ["Buck: Off already? I'll wait here."]},
    "marley": {"name": "Marley", "area": "VICTORY_ROAD_SINNOH", "figure": "Marley", "sheet": "pt_seven3.png", "sprite": "marley.png",
               "team": [59], "levels": [59],   # Arcanine
               "join": ["Marley: ...You. Take me through. I want to go where this road leads.",
                        "Marley joined you! She'll heal your team after every battle."],
               "chat": ["Marley: ...Arcanine is fast. Don't fall behind."],
               "end_exits": ["SINNOH_ROUTE_224"], "end_flag": None,
               "farewell": ["Marley: ...Thanks. You were... all right."],
               "gift": {}, "wait": ["Marley: ...I'll wait."]},
    # (Black 2 / White 2, 11-20: Hugh through the Castelia Sewers. He battles wild Pokemon beside you, not trainers (B2W2),
    # and heals your team after every battle. His team by your starter, as at the Sewers' Plasma battle: the one strong
    # against yours, evolved, and his Pidove. He leaves once Team Plasma is beaten (the scene there: b2_sewer_plasma).)
    "hugh": {"name": "{rival_name}", "area": "CASTELIA_SEWERS", "figure": "{rival_name}", "sheet": "b2_hugh.png", "sprite": "hugh.png",
             "team": [499, 519], "levels": [20, 18], "team_choice": {"495": [499, 519], "498": [502, 519], "501": [496, 519]},
             "join": ["{rival_name}: {player_name}! You've got to get tougher! I can't take them all on by myself...",
                      "{rival_name}: Don't worry, I'll keep our Pokemon healed. Come on, let's find Team Plasma!",
                      "{rival_name} joined you! He'll battle wild Pokemon beside you and heal your team after every battle."],
             "chat": ["{rival_name}: If you don't get strong, you can't protect what matters to you!"],
             "end_exits": [], "end_flag": "b2_sewer_plasma_battled",
             "farewell": [], "gift": {},
             "wait": ["{rival_name}: Stepping out for a minute? I'll wait here. Don't be long!"]},
    # (Black 2 / White 2, 11-24: Bianca through Reversal Mountain's main chamber, from where she meets you to the Undella room;
    # her team at Reversal Mountain is her usual three, by your starter's type as her other battles: Musharna and the starter
    # strong against yours. She heals your team after every battle and battles wild Pokemon beside you.)
    "bianca": {"name": "Bianca", "area": "REVERSAL_MOUNTAIN_INSIDE", "figure": "Bianca", "sheet": "b2_bianca.png", "sprite": "bianca.png",
               "team": [518, 500], "levels": [36, 36], "team_choice": {"495": [518, 500], "498": [518, 503], "501": [518, 497]},
               "join": ["Bianca: Let's go through together! I'll keep our Pokemon healed!",
                        "Bianca joined you! She'll battle wild Pokemon beside you and heal your team after every battle."],
               "chat": ["Bianca: Ooh, it's so warm in here! Do you think Heatran's close?"],
               "end_exits": [], "end_flag": "b2_reversal_bianca_bye",
               "farewell": [], "gift": {},
               "wait": ["Bianca: Taking a break? I'll wait right here!"]},
    # (Platinum's Distortion World, 11-24, s_s5_distortion.py: Cynthia walks with you from 1F; on B2F she tells Giratina's legend
    # and goes on alone - she's met again on B6F and B7F, standing on the map. No wild Pokemon there, so she never battles.)
    "cynthia": {"name": "Cynthia", "area": "DISTORTION_WORLD", "figure": "Cynthia", "sheet": "pt_champion.png", "sprite": "cynthia.png",
                "team": [445], "levels": [61],   # Garchomp
                "join": ["Cynthia: This place... Can you feel it? There are no Pokemon here at all. Time isn't flowing, and space isn't stable.",
                         "Cynthia: A world where the rules are broken... the Distortion World. Let's find Giratina. We need it to stop the distortion at the Spear Pillar.",
                         "Cynthia is walking with you."],
                "chat": ["Cynthia: Stay close. Down is the only way on, I think."],
                "end_exits": [], "end_floor": 2, "end_flag": None,
                "farewell": ["Cynthia: The legend of Giratina is all but forgotten. It told of a world on the other side of ours... this world.",
                             "Cynthia: Why is Giratina here, all alone? ...We don't need to stay together now. Let's each look for the way down."],
                "gift": {}, "wait": ["Cynthia: I'll wait here for you."]},
    # (Unova batch 12a, 11-25: Black 2's Pinwheel Forest after the title - Cheren walks the trail with you while you look for
    #  Team Plasma; the two pairs of trainers there battle you both; he leaves once the second pair is beaten)
    "cheren_pinwheel": {"name": "Cheren", "area": "PINWHEEL_FOREST", "figure": "Cheren", "sheet": "b2_cheren.png", "sprite": "cheren.png",
                        "team": [508, 505, 573], "levels": [67, 65, 65],   # (Black 2's trainer 632: Stoutland, Watchog, Cinccino)
                        "join": ["Cheren: {player_name}! I heard Team Plasma was seen in this forest.",
                                 "Cheren: Will you help me look? Let's go together. I'll keep your team healthy.",
                                 "Cheren joined you! He'll heal your team after every battle."],
                        "chat": ["Cheren: Stay alert. If Team Plasma's here, they won't be easy to spot."],
                        "end_exits": [], "end_flag": "b2_pw_pair_2",
                        "farewell": [], "gift": {},
                        "wait": ["Cheren: Heading back? I'll keep looking around here."]},
}
BY_FIGURE = {(p["area"], p["figure"]): k for k, p in PARTNERS.items()}


def walking(story, key):
    f = story.story_flags
    p = PARTNERS[key]
    return bool(f.get(f"walk_{key}") and not f.get(f"walk_{key}_done") and not (p.get("end_flag") and f.get(p["end_flag"])))


def active(story, area=None):
    """The partner walking with you here, or None."""
    area = area or story.current_area_key
    for key, p in PARTNERS.items():
        if p["area"] == area and walking(story, key):
            return key
    return None


def figure(key):
    return PARTNERS[key]["figure"]


def battle_partner(key):
    """Their side of a tag battle (battle_double.py's "partner")."""
    p = PARTNERS[key]
    out = {"name": p["name"], "class": "PKMN_TRAINER", "sprite": p["sprite"], "team": list(p["team"]), "levels": list(p["levels"])}
    if p.get("team_choice"):   # (a team by your starter: Hugh's)
        out["team_choice"] = dict(p["team_choice"])
    return out


def join(story, key):
    """They walk with you now. Returns their lines."""
    p = PARTNERS[key]
    if story.story_flags.get(f"walk_{key}_done"):
        return list(p.get("chat") or [])
    first = not story.story_flags.get(f"walk_{key}_met")
    story.story_flags[f"walk_{key}"] = True
    story.story_flags[f"walk_{key}_met"] = True
    return list(p["join"]) if first else [f"{p['name']} is walking with you again."]


def _goodbye(story, key):
    p = PARTNERS[key]
    story.story_flags[f"walk_{key}_done"] = True
    story.story_flags.pop(f"walk_{key}", None)
    lines = list(p.get("farewell") or [])
    from src.world import hms
    for item, n in (p.get("gift") or {}).items():
        story.add_item(item, n) if hasattr(story, "add_item") else story.inventory.__setitem__(item, story.inventory.get(item, 0) + n)
        lines.append(f"You received the {hms.item_name(item)}!")
    lines.append(f"{p['name']} left.")
    return lines


def on_leave(story, area, target):
    """Leaving the place: where Platinum has them leave, they say goodbye (and give their gift); back out the way you
    came, they wait where you met them. Returns lines to say first, or []."""
    key = active(story, area)
    if key is None:
        return []
    p = PARTNERS[key]
    ends = p.get("end_exits")
    if ends == "any" or target in (ends or ()):
        return _goodbye(story, key)
    story.story_flags.pop(f"walk_{key}", None)
    return list(p.get("wait") or [])


def on_floor(story, area, index):
    """A new floor: Buck stops at the door of Heatran's chamber. Returns lines, or []."""
    key = active(story, area)
    if key is None:
        return []
    end = PARTNERS[key].get("end_floor")
    if end is not None and index == end:
        return _goodbye(story, key)
    return []


def trainer_options(story, opts):
    """A trainer battle's options while a partner walks with you: a pair battles you both; every battle, they heal you."""
    key = active(story)
    if key is None:
        return opts
    out = dict(opts or {})
    out["heal_after"] = True
    if out.get("double") and not out.get("partner"):   # (a pair of two trainers too: Black 2's tag battles, 11-25)
        out["partner"] = battle_partner(key)
    return out
