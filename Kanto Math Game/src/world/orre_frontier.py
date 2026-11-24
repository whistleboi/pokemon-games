"""Orre's Battle Frontier (the fan game Pokemon Orre 2.1.1's, after Orre's League - story rework S6c, Jordan 11-24): its Battle
Tower's three endless streaks run through src/world/frontier.py ("otower", "otower2", "olc"). This region hook adds the
tower's two people the shared Frontier has no part for:
    {"world": "orre_frontier", "lc_shop": true}   the Little Cup seller: a Lv 5 Pokemon from the Little Cup's pool for BP
    {"world": "orre_frontier", "records": true}   the record boards: each streak's best
    {"world": "orre_frontier", "bp_shop": key}   a BP counter or the tutor's TMs (battle_points.SHOPS; BP_SHOP can't stand on a map)"""
import random

LC_PRICE = 3        # BP for a Little Cup Pokemon (the fan game's seller charges BP too)
LC_STOCK = 8        # how many the seller has on offer (a fresh pick each visit)


def condition(story, arg):
    return False


def event(state, ev, lines, show):
    game = state.game
    if ev.get("records"):
        from src.world import frontier
        return show([f"{frontier.NAMES[f]}: best streak {frontier.best(game, f)}, now {frontier.wins(game, f)}."
                     for f in ("otower", "otower2", "olc")])
    if ev.get("lc_shop"):
        return _lc_shop(state, show)
    if ev.get("bp_shop"):
        from src.states.game_corner import BPShopState
        return game.change_state(BPShopState(game, state, ev["bp_shop"]))
    if lines:
        show(lines)


def _lc_shop(state, show):
    from src.world import frontier, battle_points as bpl, story_events
    from src.states.systems.pick_list import PickListState
    game = state.game
    story = game.story_manager
    have = bpl.bp(story)
    if have < LC_PRICE:
        return show([f"Seller: Little Cup Pokemon, {LC_PRICE} BP each! ...You have {have} BP. Win some in the tower first!"])
    offer = random.sample(frontier.lc_pool(game), LC_STOCK)
    rows = []
    for pid in offer:
        raw = game.loader.fetch_specific(pid) or {}
        rows.append((f"{str(raw.get('name', pid)).title()} - {LC_PRICE} BP", pid))

    def chose(pid):
        game.change_state(state)
        if pid is None:
            return show(["Seller: Come again!"])
        if bpl.bp(story) < LC_PRICE:
            return show(["Seller: Not enough BP!"])
        bpl.add_bp(story, -LC_PRICE)
        said = story_events.gift_pokemon(game, pid, 5)
        show([said, f"You have {bpl.bp(story)} BP left."])
    game.change_state(PickListState(game, state, f"LITTLE CUP - {have} BP", rows, chose))
