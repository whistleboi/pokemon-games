"""Shadow farming at Orre's Poke Spots (Jordan 11-24, questions/ORRE.md 13a): from Part 2 a Cipher straggler hangs about each
Poke Spot with a Shadow Pokemon you've snagged before - snag it again, any number of times. Each spot its own pool:

    the Rock Poke Spot    Colosseum's Shadows
    the Oasis Poke Spot   XD's early ones (the HQ Lab to the Snagem raid)
    the Cave Poke Spot    XD's late ones (the Orre Colosseum, the Key Lair, Citadark)

A region hook: the straggler's option runs {"world": "orre_farm"}, shown on "world:orre_farm:here" (Part 2, and one of the
spot's Shadows snagged already). Each place's own SNAG AGAIN farms that place's Shadows too (route_actions)."""
import random

SPOTS = {"ORRE_POKE_SPOTS": "rock", "OASIS_POKE_SPOT": "oasis", "CAVE_POKE_SPOT": "cave"}
LATE = {"ORRE_COLOSSEUM", "XD_CIPHER_KEY_LAIR", "XD_CITADARK_ISLE"}   # (XD's last stretch: the Cave Poke Spot's pool)
NAME = "Cipher Straggler"


def pool(game, spot):
    """The Shadows ({"id", "name", "flag"}) of one spot's pool, from every place's shadow_pool and the Shadows' own game."""
    data = game.loader.area_data
    sd = data.get("SHADOW_DATA") or {}
    out, seen = [], set()
    for area, a in (data.get("STORY_PROGRESSION") or {}).items():
        if not isinstance(a, dict) or str(a.get("region") or "").upper() != "ORRE":
            continue
        for e in a.get("shadow_pool") or []:
            if e["flag"] in seen:
                continue
            g = (sd.get(str(e["id"])) or {}).get("game")
            kind = "rock" if g == "col" else "cave" if area in LATE else "oasis" if g == "xd" else None
            if kind == spot:
                seen.add(e["flag"])
                out.append(e)
    return out


def _snagged(game, spot):
    flags = game.story_manager.story_flags
    return [e for e in pool(game, spot) if flags.get(e["flag"])]


def condition(story, arg):
    if arg != "here" or not story.story_flags.get("orre_part2"):
        return False
    spot = SPOTS.get(story.current_area_key)
    return bool(spot and _snagged(story.game, spot))


def event(state, ev, lines, show):
    from src.world import levels
    from src.states.overworld.common import _start_event_battle
    game = state.game
    story = game.story_manager
    spot = SPOTS.get(story.current_area_key)
    have = _snagged(game, spot) if spot else []
    if not have:
        return show(["Nobody's about."])
    e = random.choice(have)
    base = int(((game.loader.area_data.get("SHADOW_DATA") or {}).get(str(e["id"])) or {}).get("level") or 20)
    lv = max(base, int(levels.story_ace(story)) - 3)   # (the Shadow's own level, or near your next Leader's if that's higher)
    info = {"name": NAME, "class": "CIPHER_PEON", "sprite": "orre_cipher_peon.png", "team": [e["id"]], "levels": [lv],
            "rewards": {"balls": 3}, "music": "orre/cipher_battle",
            "_intro_lines": [f"{NAME}: Cipher's gone, but I kept a few. Want this {e['name']}? Come and take it!"],
            "dialogue": {"player_won": [f"{NAME}: Fine, fine... I'll find another one."],
                         "player_lost": [f"{NAME}: Ha! Come back when you can snag."]}}
    game.change_state(_start_event_battle(game, story.current_area_key, info, None))
