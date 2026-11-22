"""XD after Greevil (Orre batch 8b, XD part 8): Miror B.'s last Shadow Pokemon and Greevil's rematch.

- Miror B. and Shadow Dragonite: once every other XD Shadow Pokemon is snagged (the disc's 83 less this one), Miror B.
  waits at the top of Gateon Port's lighthouse with the Dragonite he took from the Key Lair. Snag it and his radar breaks
  (src/world/miror_radar.py has()); beat him without snagging it and, like any missed Shadow, it goes on with him to the
  Poke Spots.
- Greevil's rematch (Citadark Dome 2F): his six Shadow Pokemon, each one you've already snagged replaced by its stand-in
  (the disc's second team, Story 201: Rhydon -> Manectric, Moltres -> Swellow, ...). His Shadows never go to Miror B.

    last_due(game)               -> Miror B.'s last battle is waiting
    greevil_battle(game, ev)     -> the rematch's battle (ev: {"shadows": battle, "stand_ins": battle})"""

LAST_FLAG = "snagged_shadow_dragonite"
LAST_ID = 9347
GREEVIL_FLAGS = ("snagged_shadow_rhydon", "snagged_shadow_moltres", "snagged_shadow_exeggutor", "snagged_shadow_tauros",
                 "snagged_shadow_articuno", "snagged_shadow_zapdos")


def _xd_pool(game):
    prog = game.loader.area_data.get("STORY_PROGRESSION", {})
    sd = game.loader.area_data.get("SHADOW_DATA") or {}
    return [s for a in prog.values() if isinstance(a, dict) for s in a.get("shadow_pool") or []
            if (sd.get(str(s.get("id"))) or {}).get("game") == "xd"]


def left(game):
    """XD's Shadow Pokemon not snagged yet, Miror B.'s last one aside."""
    flags = game.story_manager.story_flags
    return [s for s in _xd_pool(game) if s.get("flag") != LAST_FLAG and not flags.get(s.get("flag"))]


def last_due(game):
    flags = game.story_manager.story_flags
    return bool(flags.get("xd_greevil_beaten")) and not flags.get(LAST_FLAG) and not flags.get("xd_miror_last") and not left(game)


def greevil_battle(game, ev):
    flags = game.story_manager.story_flags
    sh, st = ev["shadows"], ev["stand_ins"]
    keep = [not flags.get(f) for f in GREEVIL_FLAGS]
    b = dict(sh)
    for k in ("team", "levels", "team_moves", "team_items"):
        if k in sh or k in st:
            a, c = list(sh.get(k) or [None] * 6), list(st.get(k) or [None] * 6)
            b[k] = [a[i] if keep[i] else c[i] for i in range(6)]
    if not any(b.get("team_items") or []):
        b.pop("team_items", None)
    return b
