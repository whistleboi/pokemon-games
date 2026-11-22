"""Colosseum after the title (Orre batch 8c, Colosseum walkthrough part 9; Jordan 11-21, DECISIONS.md "Batch 8c calls").

- The coloured Cipher peons: the Johto starters' second stages (Bayleef, Quilava, Croconaw) you haven't snagged yet come
  back with Verde, Rosso or Bluno - in the Snagem Hideout raid, then in the Shadow Pokemon Lab where Ein was (after Gurks).
  Whichever is still missed, in that order.
- Cipher Peon Fein, the master of disguise: at the Outskirt Stand once every other Colosseum Shadow Pokemon is snagged.
- Colosseum's missed Shadows wait in the Snagem raid (Colosseum's way); Miror B.'s radar keeps only XD's (miror_radar.miss).

    peon(game)        -> "bayleef" / "quilava" / "croconaw" still missed, or None
    fein_due(game)    -> Fein is waiting"""

PEONS = (("bayleef", "snagged_shadow_bayleef", "Cipher Peon Verde"), ("quilava", "snagged_shadow_quilava", "Cipher Peon Rosso"),
         ("croconaw", "snagged_shadow_croconaw", "Cipher Peon Bluno"))
FEIN_FLAG = "snagged_shadow_togetic"


def peon(game):
    flags = game.story_manager.story_flags
    return next((k for k, f, _n in PEONS if not flags.get(f)), None)


def peon_name(key):
    return next((n for k, _f, n in PEONS if k == key), "Cipher Peon")


def _col_pool(game):
    prog = game.loader.area_data.get("STORY_PROGRESSION", {})
    sd = game.loader.area_data.get("SHADOW_DATA") or {}
    return [s for a in prog.values() if isinstance(a, dict) for s in a.get("shadow_pool") or []
            if (sd.get(str(s.get("id"))) or {}).get("game") == "col"]


def fein_due(game):
    flags = game.story_manager.story_flags
    if not flags.get("beat_orre_champion") or flags.get(FEIN_FLAG) or flags.get("col_fein"):
        return False
    return all(flags.get(s.get("flag")) for s in _col_pool(game) if s.get("flag") != FEIN_FLAG)


def second_chance(game, battle):
    """A battle with "if_snagged": {"flag", "battle"}: once that Shadow is snagged, the other team (no Shadow) instead."""
    alt = (battle or {}).get("if_snagged")
    if alt and game.story_manager.story_flags.get(alt.get("flag")):
        b = dict(alt["battle"])
        for k in ("dialogue", "intro", "is_boss_battle", "rewards", "music"):
            if k in battle and k not in b:
                b[k] = battle[k]
        return b
    return battle
