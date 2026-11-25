"""Amity Square in Hearthome City (Pokemon Platinum, 11-24, Sinnoh S8; built by kanto_handoff/sinnoh_map_tools/s_s8_amity.py):
a park you stroll in with a small Pokemon - only some may go in (Platinum's own list, pret/pokeplatinum
res/field/maps/amity_square/scripts.s: sixteen; with the National Pokedex four more). Here the one walking with you is your
lead Pokemon, so the gates' way in opens when your lead is on the list.

Conditions ("world:amity_square:<arg>"): "ok" (your lead may go in)."""

ALLOWED = (25, 35, 54, 417, 425, 427, 440,          # Pikachu, Clefairy, Psyduck, Pachirisu, Drifloon, Buneary, Happiny
           387, 388, 389, 390, 391, 392, 393, 394, 395)   # the three first partners and their evolutions
NATIONAL = (39, 255, 300, 285)                      # Jigglypuff, Torchic, Skitty, Shroomish (once you have the National Pokedex)


def _national(story):
    try:
        from src.states.systems.pokedex import has_national_dex
        return has_national_dex(story)
    except Exception:
        return bool(story.story_flags.get("unlocked_national_dex"))


def allowed(story):
    return ALLOWED + (NATIONAL if _national(story) else ())


def lead(story):
    return next((p for p in story.player_team if p and not getattr(p, "is_egg", False)), None)


def condition(story, arg):
    if arg == "ok":
        p = lead(story)
        return p is not None and int(getattr(p, "id", 0) or 0) in allowed(story)
    return False
