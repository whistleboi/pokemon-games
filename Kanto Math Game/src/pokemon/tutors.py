"""Move tutors and the TMs (Jordan, 11-19): "For any tutors, including previous regions, if their tutor moves are
available as TMs, have the tutors sell the TMs. If the tutor TMs are/were in the shops, remove them from the shop so
they are only available from the tutor."

A tutor is any event with a "tutor" ({"move"} or {"choices": [moves]}) in a region's area data or on its maps
(assets/town_maps.json: map people, rooms, floors). tutor_tms(game, region): the TMs whose moves a tutor in that
region teaches - that region's shops don't sell them (src/states/systems/mart.py), the tutor does (common.py's tutor
event offers "Buy the TM"). Other regions' shops are not affected (a region without that tutor still sells the TM)."""


def _norm(move):
    return str(move or "").upper().replace("_", "-").replace(" ", "-")


def _tutor_moves(obj, out):
    if isinstance(obj, dict):
        tu = obj.get("tutor")
        if isinstance(tu, dict):
            for m in [tu.get("move")] + list(tu.get("choices") or []):
                if m:
                    out.add(_norm(m))
        for v in obj.values():
            _tutor_moves(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _tutor_moves(v, out)


def moves_by_region(game):
    """{region: {move}} every tutor's moves, from the area data and the walked maps."""
    cache = game.__dict__.setdefault("_tutor_cache", {})
    if "by_region" in cache:
        return cache["by_region"]
    prog = (getattr(game.loader, "area_data", {}) or {}).get("STORY_PROGRESSION", {}) or {}
    try:
        from src.states.overworld.walk_town import custom
        maps = custom(game) or {}
    except Exception:
        maps = {}
    out = {}
    for key, area in prog.items():
        if not isinstance(area, dict):
            continue
        region = str(area.get("region") or "KANTO").upper()   # (Kanto's areas carry no region: the game's default, story.area_region)
        got = set()
        _tutor_moves(area, got)
        _tutor_moves(maps.get(key) or {}, got)
        if got:
            out.setdefault(region, set()).update(got)
    cache["by_region"] = out
    return out


def tms_for_moves(game, moves):
    """The TM keys teaching these moves (moves our TMs don't have: left out)."""
    from src.pokemon import tms
    by_move = {_norm(d.get("move")): k for k, d in tms.table(game).items()}
    return sorted({by_move[_norm(m)] for m in moves if _norm(m) in by_move})


def tutor_tms(game, region=None):
    """The TMs a tutor in this region (default: where you are) sells instead of the shops."""
    region = str(region or game.story_manager.get_current_region() or "").upper()
    cache = game.__dict__.setdefault("_tutor_cache", {})
    k = ("tms", region)
    if k not in cache:
        cache[k] = set(tms_for_moves(game, moves_by_region(game).get(region, ())))
    return cache[k]


def tutor_event_tms(game, ev):
    """The TMs of this tutor event's moves."""
    tu = (ev or {}).get("tutor") or {}
    return tms_for_moves(game, [tu.get("move")] + list(tu.get("choices") or []))
