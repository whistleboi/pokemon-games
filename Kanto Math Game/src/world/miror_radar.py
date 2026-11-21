"""Miror B.'s radar (Jordan 11-20, Orre batch 5b: "XD's way").

Once you hold the MIROR_RADAR (Miror B. drops it at the Cave Poke Spot), every Shadow Pokemon you beat without snagging it
goes to Miror B.: it leaves its own place's Snag list and joins his team. Each day he dances at one of the three Poke
Spots; the radar (used from the Bag) says which. Battle him there (the route option "WANDERER MIROR B.", condition
"miror_b_here") and snag them back. Before the radar, a missed Shadow stays at its place, as before.

    has(story)                  -> the radar's in your Bag
    miss(game, mon)             -> a Shadow beaten unsnagged (src/states/battle_shadow.py, on a win)
    missed(game)                -> [[flag, form id, level], ...] still with him
    where(game)                 -> the Poke Spot he's at today, or None
    is_with_him(game, flag)     -> a shadow_pool entry he holds (it leaves that place's Snag list)
    battle_info(game)           -> his battle (Ludicolo and the missed Shadows), for a story event
    radar_lines(game)           -> what the radar shows"""
import datetime

SPOTS = ("ORRE_POKE_SPOTS", "OASIS_POKE_SPOT", "CAVE_POKE_SPOT")
SPOT_NAMES = {"ORRE_POKE_SPOTS": "the Rock Poke Spot", "OASIS_POKE_SPOT": "the Oasis Poke Spot", "CAVE_POKE_SPOT": "the Cave Poke Spot"}
LUDICOLO = 272
KEY = "miror_b_missed"


def has(story):
    return story.inventory.get("MIROR_RADAR", 0) > 0


def missed(game):
    flags = game.story_manager.story_flags
    held = [m for m in (flags.get(KEY) or []) if not flags.get(m[0])]
    flags[KEY] = held
    return held


def is_with_him(game, flag):
    return has(game.story_manager) and any(m[0] == flag for m in missed(game))


def miss(game, mon):
    story = game.story_manager
    if not has(story):
        return
    from src.world import shadow
    flag = shadow.snag_flag(game, mon)
    if not flag or story.story_flags.get(flag):
        return
    held = missed(game)
    if not any(m[0] == flag for m in held):
        held.append([flag, int(mon.id), int(getattr(mon, "level", 50) or 50)])
        story.story_flags[KEY] = held


def where(game):
    if not has(game.story_manager) or not missed(game):
        return None
    return SPOTS[datetime.date.today().toordinal() % len(SPOTS)]


def radar_lines(game):
    if not missed(game):
        return ["The Miror B. Radar is quiet. Miror B. has none of your missed Shadow Pokemon."]
    spot = where(game)
    n = len(missed(game))
    return ["The Miror B. Radar is beeping!",
            f"Miror B. is grooving at {SPOT_NAMES[spot]} today, with {n} Shadow Pokemon you didn't snag."]


def battle_info(game):
    held = missed(game)[:4]
    top = max((m[2] for m in held), default=40)
    team = [LUDICOLO, LUDICOLO] + [m[1] for m in held]
    levels = [max(1, top - 2), max(1, top - 2)] + [m[2] for m in held]
    return {"name": "Wanderer Miror B.", "class": "WANDERER", "sprite": "orre_trainer_miror_b.png", "team": team, "levels": levels,
            "double": True, "music": "orre/miror_b_battle", "rewards": {"balls": 0},
            "_intro_lines": ["Miror B.: Ooh, you found me! These lonely Shadow Pokemon found a new rhythm with me!",
                             "Miror B.: You want them back? Then dance for them!"],
            "dialogue": {"player_won": ["Miror B.: Aww! You stepped all over my groove! I'm out of here!"]}}
