"""The route dungeon rules (src/dungeon/core.py), no pygame needed. Plain asserts; run directly."""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from src.dungeon import core  # noqa: E402

TESTS = []


def test(f):
    TESTS.append(f)
    return f


def make_run(seed, floors=2, style="field"):
    loot = {"per_floor": [2, 4], "items": {"POTION": 3, "POKE_BALLS": 1}}
    return core.Run({"floors": floors, "style": style, "size": [40, 26], "wild": [3, 5]}, random.Random(seed),
                    entrance="BACK", forwards=["A", "B"], make_wild=lambda r: "wild",
                    trainers=[(0, "t0"), (1, "t1")], loot_for=lambda r: core.roll_loot(r, loot), tm_spots=["S1"])


@test
def every_floor_can_be_crossed():
    """Every exit, item, TM spot and mover can be reached from the start, on every style and floor."""
    for seed in range(300):
        run = make_run(seed, floors=1 + seed % 3, style=("field", "forest", "cave")[seed % 3])
        for i in range(run.n_floors):
            f = run.floor
            reach = core.distances(f, f.start)
            for t in list(f.exits) + list(f.items) + list(f.tm_spots) + [(m.x, m.y) for m in f.movers]:
                assert t in reach, (seed, i, t)
            want = (["BACK"] if i == 0 else []) + (["A", "B"] if i == run.n_floors - 1 else [core.STAIRS])
            assert sorted(f.exits.values()) == sorted(want), (seed, i, f.exits)
            if i < run.n_floors - 1:
                run.descend()


@test
def nothing_walks_through_walls():
    for seed in range(60):
        run = make_run(seed)
        rng = random.Random(seed)
        for _ in range(400):
            events = run.step(*rng.choice(core.DIRS))
            f = run.floor
            assert f.walkable(*run.player)
            for m in f.movers:
                assert f.walkable(m.x, m.y) and (m.x, m.y) != run.player
            if any(e[0] in ("exit", "stairs") for e in events):
                break
            for e in events:
                if e[0] in ("bump", "ambush") and e[1].kind == "wild":
                    run.remove(e[1])


@test
def wild_pokemon_chase_and_jump_in():
    run = make_run(1, floors=1)
    f = run.floor
    f.movers[:] = []
    px, py = run.player
    spot = next((px + k * dx, py + k * dy) for dx, dy in core.DIRS for k in (3,)
                if all(f.walkable(px + j * dx, py + j * dy) for j in range(1, 4)))
    m = core.Mover("wild", spot[0], spot[1], "w")
    f.movers.append(m)
    events = []
    for _ in range(4):
        events += run.wait()
    assert any(e[0] == "ambush" and e[1] is m for e in events), events


@test
def trainers_see_ahead():
    run = make_run(2, floors=1)
    f = run.floor
    f.movers[:] = []
    for y in range(f.h):
        for x in range(f.w - 4):
            if all(f.walkable(x + k, y) for k in range(5)):
                t = core.Mover("trainer", x, y, (0, "t"), facing=(1, 0))
                f.movers.append(t)
                run.player = (x + 3, y)
                assert any(e[0] == "spotted" for e in run.others_act())
                run.player = (x + 6, y)
                assert not any(e[0] == "spotted" for e in run.others_act())
                return
    raise AssertionError("no straight path found")


@test
def tm_spots_pick_once_per_save():
    table = {f"TM{i:02d}": {"tier": i // 12} for i in range(100)}
    a = core.pick_tm(42, "R2", table, set(), 0)
    assert a == core.pick_tm(42, "R2", table, set(), 0)
    assert table[a]["tier"] <= 1
    assert core.pick_tm(42, "R2", table, {a}, 0) != a
    assert core.pick_tm(42, "R2", table, set(table), 8) is None


@test
def loot_follows_its_weights():
    rng = random.Random(3)
    items = [i for _ in range(2000) for i in core.roll_loot(rng, {"per_floor": [1, 1], "items": {"A": 9, "B": 1}})]
    assert 0.85 < items.count("A") / len(items) < 0.95


@test
def walking_to_a_tapped_tile():
    run = make_run(4, floors=1)
    f = run.floor
    f.movers[:] = []
    goal = next(xy for xy, t in f.exits.items() if t == "A")
    for _ in range(500):
        step = run.walk_toward(goal)
        if step is None:
            break
        events = run.step(*step)
        if any(e[0] == "exit" for e in events):
            break
    assert run.player == goal


if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t()
            print("OK  ", t.__name__)
        except Exception as e:
            fails += 1
            print("FAIL", t.__name__, repr(e))
    print(f"{len(TESTS) - fails}/{len(TESTS)} passed")
    raise SystemExit(1 if fails else 0)
