"""XD's Poke Snacks at the three Poke Spots (Orre batch 8d; Jordan 11-21: "XD's way, all of it", steps for time).

- Each spot has a tray of up to 10 Poke Snacks (the "SNACK TRAY" there: put snacks in, take them back). No snacks, no
  wild Pokemon at the spot.
- Away from a stocked spot, a visitor comes after ARRIVE steps (walked anywhere else): a wild Pokemon from the spot's own
  table (rarer ones less often), Munchlax 10% of the time (the Gateon herbalist's: it gobbles the whole tray; tell him and
  he gives 10 snacks and a herb), Bonsly 30% once the S.S. Libra is done (until you have one). The Spot Monitor (the P*DA)
  beeps: slow for a common one, fast for a rare one.
- While it's there it eats a snack every EAT steps; the last one gone, it leaves. On the spot's map it is the only wild
  Pokemon (src/states/overworld/dungeon.py _make_wild); battled, caught or run from, it's gone (the snacks left stay).
- Snacks: Duking leaves 10 at your first tray; the herbalist after Munchlax; Orre trainers now and then after a win.

    trays(story) -> {spot: {"tray", "visitor", "steps"}}
    walked(game, steps) -> lines (the Spot Monitor's alerts)
    visitor_mon(game, spot) -> a wild Pokemon for the spot's map, or None"""
import random

SPOTS = {"ORRE_POKE_SPOTS": "the Rock Poke Spot", "OASIS_POKE_SPOT": "the Oasis Poke Spot", "CAVE_POKE_SPOT": "the Cave Poke Spot"}
KEY = "poke_snacks"
ITEM = "POKE_SNACK"
TRAY_MAX = 10
ARRIVE = 120
EAT = 50
MUNCHLAX, BONSLY = 446, 438
MUNCHLAX_CHANCE, BONSLY_CHANCE = 0.10, 0.30
TRAINER_CHANCE = 0.35   # (an Orre trainer beaten gives a snack about one time in three)


def trays(story):
    t = story.story_flags.get(KEY)
    if not isinstance(t, dict):
        t = {}
        story.story_flags[KEY] = t
    for s in SPOTS:
        t.setdefault(s, {"tray": 0, "visitor": None, "steps": 0})
    return t


def _pool(game, spot):
    area = game.loader.area_data.get("STORY_PROGRESSION", {}).get(spot) or {}
    table = game.loader.area_data.get(area.get("wild_pool_percentages") or "") or {}
    return [(int(k), int(v)) for k, v in table.items()]


def _choose(game, spot, rng):
    story = game.story_manager
    if rng.random() < MUNCHLAX_CHANCE:
        return {"id": MUNCHLAX, "kind": "munchlax", "rare": True}
    if (story.story_flags.get("xd_bonsly_home") and not story.catch_counts.get(str(BONSLY))
            and rng.random() < BONSLY_CHANCE):
        return {"id": BONSLY, "kind": "bonsly", "rare": True}
    pool = _pool(game, spot)
    if not pool:
        return None
    tot = sum(w for _i, w in pool)
    r = rng.random() * tot
    for pid, w in pool:
        r -= w
        if r <= 0:
            return {"id": pid, "kind": "wild", "rare": w <= 10}
    return {"id": pool[0][0], "kind": "wild", "rare": False}


def beeps(v):
    return "Beep-beep-beep-beep!" if v and v.get("rare") else "Beep... beep... beep..."


def walked(game, steps=1, rng=None):
    story = game.story_manager
    if story.get_current_region() != "ORRE":
        return []
    rng = rng or random
    lines = []
    here = story.current_area_key
    for spot, t in trays(story).items():
        if spot == here or t["tray"] <= 0:
            continue
        t["steps"] += steps
        if not t["visitor"]:
            if t["steps"] >= ARRIVE:
                t["steps"] = 0
                t["visitor"] = _choose(game, spot, rng)
                if t["visitor"]:
                    lines.append(f"Spot Monitor: {beeps(t['visitor'])} Something is eating the snacks at {SPOTS[spot]}!")
            continue
        while t["steps"] >= EAT and t["tray"] > 0:
            t["steps"] -= EAT
            t["tray"] -= 1
        if t["tray"] <= 0:
            t["visitor"], t["steps"] = None, 0
            lines.append(f"Spot Monitor: the snacks at {SPOTS[spot]} are all gone. Whatever was eating them has left.")
    return lines


def visitor_mon(game, spot):
    """The spot's map: its visitor (once), else nobody."""
    v = trays(game.story_manager)[spot].get("visitor")
    if not v or v.get("kind") == "munchlax":
        return None
    from src.pokemon.data import Pokemon
    from src.world import levels
    raw = game.loader._fetch_raw(id_pool=[int(v["id"])], area_data=game.loader.area_data.get("STORY_PROGRESSION", {}).get(spot) or {})
    if not raw or raw.get("id", 0) == 0:
        return None
    p = Pokemon(raw, game.assets, size_mult=3.125)
    levels.set_wild(game, p, spot)
    p.snack_visitor = spot
    return p


def visitor_gone(game, spot):
    t = trays(game.story_manager).get(spot)
    if t:
        t["visitor"], t["steps"] = None, 0


def tray_lines(game, spot):
    t = trays(game.story_manager)[spot]
    v = t["visitor"]
    who = "Nothing's eating." if not v else ("A Munchlax is gobbling the snacks!" if v["kind"] == "munchlax"
                                             else "Something's at the tray! Look around the spot.")
    return [f"The snack tray: {t['tray']} of {TRAY_MAX} Poke Snacks. {who}"]


def tray_event(state, ev, lines, show):
    """The SNACK TRAY at a spot: Duking's starter bag; Munchlax caught red-handed; put snacks in or take them back."""
    from src.states.systems.pick_list import PickListState
    from src.states.overworld.common import _say_then
    game = state.game
    story = game.story_manager
    spot = story.current_area_key
    t = trays(story)[spot]
    said = list(lines or [])
    if not story.story_flags.get("snacks_from_duking"):
        story.story_flags["snacks_from_duking"] = True
        story.add_item(ITEM, 10)
        said.append("A note on the tray: \"Leave some Poke Snacks here and see who comes to eat! Here's 10 to start. - Duking\"")
    v = t["visitor"]
    if v and v.get("kind") == "munchlax":
        t["tray"], t["visitor"], t["steps"] = 0, None, 0
        story.story_flags["munchlax_ate"] = True
        show(said + ["A Munchlax is gobbling up every last snack! It has a tag on its collar: \"Gateon Port herb shop\".",
                     "It waddles off, full. Maybe its owner in Gateon should hear about this..."])
        return
    have = story.inventory.get(ITEM, 0)
    rows = []
    if t["tray"] < TRAY_MAX and have:
        rows.append(("PUT IN SNACKS", "put"))
    if t["tray"]:
        rows.append(("TAKE THEM BACK", "take"))

    def picked(what):
        if what == "put":
            n = min(TRAY_MAX - t["tray"], story.inventory.get(ITEM, 0))
            t["tray"] += n
            story.inventory[ITEM] -= n
            show([f"You put {n} Poke Snack{'s' if n != 1 else ''} on the tray. Now walk somewhere else and wait for the Spot Monitor."])
        elif what == "take":
            story.add_item(ITEM, t["tray"])
            show([f"You took back {t['tray']} Poke Snacks."])
            t["tray"], t["visitor"], t["steps"] = 0, None, 0
        else:
            show(["You leave the tray as it is."])

    said += tray_lines(game, spot) + [f"You have {have} Poke Snacks."]
    if not rows:
        show(said + (["You have no Poke Snacks to put in."] if not have else []))
        return
    _say_then(state, said, lambda: game.change_state(PickListState(game, state, "THE SNACK TRAY", rows, picked)))


def trainer_reward(game, rng=None):
    """An Orre trainer beaten: sometimes a snack (lines)."""
    story = game.story_manager
    if story.get_current_region() != "ORRE" or not story.story_flags.get("snacks_from_duking"):
        return []
    if (rng or random).random() < TRAINER_CHANCE:
        story.add_item(ITEM, 1)
        return ["You got a Poke Snack!"]
    return []
