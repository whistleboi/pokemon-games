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
             "farewell": ["Buck: Whatever's in there is too much for me. I'll wait here. Go on!"],
             "gift": {}, "wait": ["Buck: Off already? I'll wait here."]},
    "marley": {"name": "Marley", "area": "VICTORY_ROAD_SINNOH", "figure": "Marley", "sheet": "pt_seven3.png", "sprite": "marley.png",
               "team": [59], "levels": [59],   # Arcanine
               "join": ["Marley: ...You. Take me through. I want to go where this road leads.",
                        "Marley joined you! She'll heal your team after every battle."],
               "chat": ["Marley: ...Arcanine is fast. Don't fall behind."],
               "end_exits": ["SINNOH_ROUTE_224"], "end_flag": None,
               "farewell": ["Marley: ...Thanks. You were... all right."],
               "gift": {}, "wait": ["Marley: ...I'll wait."]},
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
    return {"name": p["name"], "class": "PKMN_TRAINER", "sprite": p["sprite"], "team": list(p["team"]), "levels": list(p["levels"])}


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
    if out.get("double") and not out.get("partner") and not out.get("second_trainer"):
        out["partner"] = battle_partner(key)
    return out
