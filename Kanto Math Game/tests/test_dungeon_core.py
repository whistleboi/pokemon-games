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
            want = (["BACK"] if i == 0 else [core.STAIRS_UP]) + (["A", "B"] if i == run.n_floors - 1 else [core.STAIRS])
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



@test
def ponds_never_cut_a_way():
    """Ponds (for fishing) and every style, building and sea too: everything still reachable."""
    water = 0
    for seed in range(200):
        style = ("field", "forest", "cave", "building", "sea")[seed % 5]
        run = core.Run({"floors": 1, "style": style, "size": [40, 26], "wild": [3, 5], "ponds": 3},
                       random.Random(seed), entrance="BACK", forwards=["A"], make_wild=lambda r: "wild",
                       figures=[(0, "boss")])
        f = run.floor
        reach = core.distances(f, f.start)
        water += sum(row.count(core.WATER) for row in f.tiles)
        for t in list(f.exits) + [(m.x, m.y) for m in f.movers]:
            assert t in reach, (seed, style, t)
        assert all(not f.walkable(x, y) for y in range(f.h) for x in range(f.w) if f.tiles[y][x] == core.WATER)
    assert water > 300, water  # (small corner ponds: somewhere to fish)


@test
def stairs_go_both_ways():
    """Down the stairs and back up: the same floor as you left it, beside its stairs."""
    run = make_run(5, floors=3)
    first = run.floor
    run.player = (0, 0)
    run.descend()
    assert run.index == 1 and core.STAIRS_UP in run.floor.exits.values()
    up = next(t for t, v in run.floor.exits.items() if v == core.STAIRS_UP)
    assert run.floor.room_at(*up) is run.floor.room_at(*run.player)  # in the room you arrive in
    run.ascend()
    assert run.index == 0 and run.floor is first
    down = next(t for t, v in first.exits.items() if v == core.STAIRS)
    assert abs(run.player[0] - down[0]) + abs(run.player[1] - down[1]) == 1
    run.descend()
    run.descend()
    assert run.index == 2 and len(run.floors) == 3


@test
def figures_stand_still_and_can_be_bumped():
    run = core.Run({"floors": 2, "size": [40, 26], "wild": [0, 0]}, random.Random(3), entrance="BACK",
                   forwards=["A"], figures=[(1, "zapdos"), (0, "nerd")])
    figs = [m for m in run.floor.movers if m.kind == "figure"]
    assert [m.payload for m in figs] == ["nerd"]
    spot = (figs[0].x, figs[0].y)
    for _ in range(30):
        run.wait()
    assert (figs[0].x, figs[0].y) == spot
    run.descend()
    assert [m.payload for m in run.floor.movers if m.kind == "figure"] == ["zapdos"]
    run.drop_figure("zapdos")
    assert not [m for m in run.floor.movers if m.kind == "figure"]
    run.add_figure(1, "ghost")
    assert [m.payload for m in run.floor.movers if m.kind == "figure"] == ["ghost"]


@test
def ways_out_and_trainers_on_their_floors():
    """A building: its ways out on given floors, a trainer on its own floor."""
    run = core.Run({"floors": 3, "size": [40, 26], "wild": [0, 0]}, random.Random(9),
                   exits_by_floor={0: ("TOWN", []), 2: (None, ["ROOF"])},
                   trainers=[(0, {"floor": 2}), (1, {})], floor_of=lambda t: t.get("floor"), start_floor=0)
    assert sorted(run.floor.exits.values()) == sorted(["TOWN", core.STAIRS])
    run.descend()
    assert sorted(run.floor.exits.values()) == sorted([core.STAIRS_UP, core.STAIRS])
    run.descend()
    assert sorted(run.floor.exits.values()) == sorted([core.STAIRS_UP, "ROOF"])
    assert any(m.kind == "trainer" and m.payload[0] == 0 for m in run.floor.movers)

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
