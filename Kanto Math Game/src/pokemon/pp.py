# [REF-0085: PP]
"""PP, like the games: every move has Power Points (assets/moves.json "pp"); using a move spends one
(two against a foe with Pressure). A move at 0 PP can't be picked; with no PP left in any move, the
Pokemon uses Struggle. Pokemon Centers (and every full heal: Pokemon.heal_full) restore all PP.

Each Pokemon keeps
  mon.pp       {move: PP left}   (a move missing from it has full PP)
  mon.pp_ups   {move: PP Ups used, 0-3}   (each adds a fifth of the base PP: PP Up one, PP Max all three)

Items: Ether (10 PP, one move), Max Ether (all, one move), Elixir (10 PP, every move), Max Elixir
(all, every move), Leppa Berry (10 PP, one move; held, it restores a move that runs out), PP Up, PP Max."""

MAX_UPS = 3
DEFAULT_PP = 10
PP_ITEMS = {
    "ETHER": {"restore": 10, "all": False, "price": 1200, "text": "Restores 10 PP to one of a Pokemon's moves."},
    "MAX_ETHER": {"restore": "full", "all": False, "price": 2000, "text": "Fully restores the PP of one of a Pokemon's moves."},
    "ELIXIR": {"restore": 10, "all": True, "price": 3000, "text": "Restores 10 PP to each of a Pokemon's moves."},
    "MAX_ELIXIR": {"restore": "full", "all": True, "price": 4500, "text": "Fully restores the PP of all of a Pokemon's moves."},
    "LEPPA_BERRY": {"restore": 10, "all": False, "berry": True, "text": "A Berry. Restores 10 PP to one move. Held, it's eaten when a move runs out of PP."},
    "PP_UP": {"ups": 1, "price": 9800, "text": "Raises the most PP of one of a Pokemon's moves a little, for good."},
    "PP_MAX": {"ups": MAX_UPS, "price": 9800, "text": "Raises the most PP of one of a Pokemon's moves as high as it goes, for good."},
}


def base_pp(game, move):
    from src.pokemon import moves as movelib
    if move == movelib.STRUGGLE:
        return 0
    return int(movelib.table(game).get(move, {}).get("pp") or DEFAULT_PP)


def ups(mon, move):
    return int((getattr(mon, "pp_ups", None) or {}).get(move, 0))


def max_pp(game, mon, move):
    """Base PP, plus a fifth of it for each PP Up (PP Max: three). A move copied by Transform: 5 at most
    (mon._pp_cap, set for the battle by battle_moves.mv_copied_pp)."""
    cap = getattr(mon, "_pp_cap", None)
    if cap and move in cap:
        return cap[move]
    b = base_pp(game, move)
    return b + b * ups(mon, move) // 5


def left(game, mon, move):
    pp = getattr(mon, "pp", None) or {}
    top = max_pp(game, mon, move)
    return max(0, min(top, int(pp.get(move, top))))


def _store(mon):
    if not isinstance(getattr(mon, "pp", None), dict):
        mon.pp = {}
    return mon.pp


def spend(game, mon, move, n=1):
    """Use n PP (never below 0). Returns the PP left."""
    from src.pokemon import moves as movelib
    if move == movelib.STRUGGLE or not move:
        return 0
    now = max(0, left(game, mon, move) - n)
    _store(mon)[move] = now
    return now


def restore(game, mon, move, amount="full"):
    """Give back PP to one move. Returns how much it got back."""
    have, top = left(game, mon, move), max_pp(game, mon, move)
    new = top if amount == "full" else min(top, have + int(amount))
    if new >= top:
        _store(mon).pop(move, None)
    else:
        _store(mon)[move] = new
    return new - have


def restore_all(mon):
    """Full PP for every move (Pokemon Center)."""
    mon.pp = {}


def forget(mon, move):
    """A move it no longer knows: if relearned, it comes back with full PP (PP Ups stay with the move slot in
    the games; here they stay with the move)."""
    _store(mon).pop(move, None)


def usable_moves(game, mon, moves):
    """The moves with PP left."""
    return [m for m in moves if left(game, mon, m) > 0]


def can_restore(game, mon, move):
    return left(game, mon, move) < max_pp(game, mon, move)


def can_raise(game, mon, move):
    return base_pp(game, move) >= 5 and ups(mon, move) < MAX_UPS


def raise_pp(game, mon, move, n=1):
    """PP Up (n=1) / PP Max (n=3). Returns True if the move's PP went up (the extra PP comes filled in)."""
    if not can_raise(game, mon, move):
        return False
    had_full = not can_restore(game, mon, move)
    before = max_pp(game, mon, move)
    if not isinstance(getattr(mon, "pp_ups", None), dict):
        mon.pp_ups = {}
    mon.pp_ups[move] = min(MAX_UPS, ups(mon, move) + n)
    if not had_full:
        _store(mon)[move] = left(game, mon, move) + (max_pp(game, mon, move) - before)
    return True


def use_item(game, mon, item, move=None):
    """An Ether / Elixir / Leppa Berry / PP Up / PP Max on a Pokemon (move: for the one-move ones).
    Returns (used, lines)."""
    from src.pokemon import moves as movelib
    data = PP_ITEMS[item]
    name = mon.display_name
    known = list(movelib.ensure_moves(game, mon))
    label = lambda m: m.replace("-", " ").title()
    if "ups" in data:
        if move is None or not can_raise(game, mon, move):
            return False, ["It won't have any effect."]
        raise_pp(game, mon, move, data["ups"])
        return True, [f"{label(move)}'s PP rose! (Now {max_pp(game, mon, move)}.)"]
    targets = known if data["all"] else [move] if move else []
    got = {m: restore(game, mon, m, data["restore"]) for m in targets if can_restore(game, mon, m)}
    if not got:
        return False, ["It won't have any effect."]
    if data["all"]:
        return True, [f"{name}'s PP was restored."]
    return True, [f"{label(move)}'s PP was restored by {got[move]}."]
