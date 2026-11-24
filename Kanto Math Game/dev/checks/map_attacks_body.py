# Attacks on the map (Jordan 11-24, region/systems; src/vfx/map_attacks.py): lunges for physical moves, beams for
# special ones, rings for status moves, each type with the game's own move-animation sprites, sized by the move's power;
# played in OVERWORLD-style battles and the swarm's battle on the map. A real battle played through its answers.
#   bash dev/checks/run.sh map_attacks
exec(open("dev/checks/dungeon_lib.py", encoding="utf-8").read())
from src.vfx import map_attacks as ma
import os as _os
_os.makedirs(_os.path.join(S, "map_attacks"), exist_ok=True)
g.dungeon_routes = True


def to_battle(p, shot_name=None, n=600):
    """The walk over to where the battle stands (if it moves), then the battle; a picture mid-walk."""
    walked = 0
    for _ in range(n):
        if g.current_state is not p:
            return walked
        if p.mode == "OWWALK":
            walked += 1
            if shot_name and walked == 8:
                p.draw()
                pygame.image.save(g.screen, _os.path.join(S, "map_attacks", shot_name))
        p.update()
    return walked


def walk_back(p, n=600):
    for _ in range(n):
        if p.mode != "OWWALK":
            break
        p.update()

print("1) every type has its sprites, from the game's own move-animation sheets")
for typ in ma.SPRITES:
    got = [len(ma.sprites(g.assets.assets_dir, typ, k)) for k in range(3)]
    check(all(got), f"{typ}: beam {got[0]}, hit {got[1]}, bits {got[2]} cells")
check(set(ma.SPRITES) == set(ma.COLORS) and len(ma.SPRITES) == 18, "all 18 types")

print("2) the move decides the look: physical lunge, special beam, status ring; power sets the size")
r1, r2 = pygame.Rect(100, 100, 56, 56), pygame.Rect(220, 100, 56, 56)
mk_atk = lambda name: ma.MapAttack(g, ma.move_for(g, name), lambda: r1, lambda: r2)
tomb, bolt, growl = mk_atk("ROCK-TOMB"), mk_atk("THUNDERBOLT"), mk_atk("GROWL")
check((tomb.kind, tomb.type, bolt.kind, bolt.type, growl.kind) == ("PHYSICAL", "ROCK", "SPECIAL", "ELECTRIC", "STATUS"),
      f"Rock Tomb a Rock lunge, Thunderbolt an Electric beam, Growl a ring ({tomb.kind} {tomb.type}, {bolt.kind} {bolt.type}, {growl.kind})")
check([ma.tier(p) for p in (40, 60, 90, 120)] == [0, 1, 2, 3], "power tiers: up to 40, 75, 100, more")


def peak(atk, who):
    best = 0
    while atk.t < atk.length:
        atk.update()
        dx, dy = atk.offset(who)
        best = max(best, abs(dx) + abs(dy))
    return best


tackle, quake = mk_atk("TACKLE"), mk_atk("EARTHQUAKE")
lean = []
t = mk_atk("TACKLE")
for _ in range(int(t.length * 0.2)):
    t.update()
    lean.append(t.offset("user")[0])
check(min(lean) < 0, f"a lunge winds up first: leans back away from the target ({min(lean)} px)")
rt, rq = peak(mk_atk("TACKLE"), "target"), peak(mk_atk("EARTHQUAKE"), "target")
check(0 < rt < rq, f"the target is knocked back, more by a stronger move (Tackle {rt} px, Earthquake {rq} px)")
check(peak(mk_atk("TACKLE"), "user") > 50, "the attacker dashes over to the target")
check(peak(mk_atk("GROWL"), "target") == 0, "a status move moves no one")
q = mk_atk("THUNDER")
shook = flashed = False
while q.t < q.length:
    q.update()
    shook = shook or q.shake() > 0
    flashed = flashed or q.flashing()
check(shook and flashed and not any(mk_atk("TACKLE").shake() for _ in range(1)), "the strongest shake the screen; the one hit flashes white")
small, big = mk_atk("EMBER"), mk_atk("FLAMETHROWER")
for a in (small, big):
    while not a.hitting():
        a.update()
    a.update()
check(0 < len(small.parts) < len(big.parts), f"a stronger move throws more of its sprites ({len(small.parts)} vs {len(big.parts)})")
surf = pygame.Surface((400, 300), pygame.SRCALPHA)
for name in ("ROCK-TOMB", "THUNDERBOLT", "GROWL", "SWORDS-DANCE"):
    a = mk_atk(name)
    while not a.done:
        a.update()
        a.draw(surf)
check(True, "every kind draws to the end without a hitch")
sd = ma.MapAttack(g, ma.move_for(g, "SWORDS-DANCE"), lambda: r1, lambda: r2, self_target=True)
check(sd.target() is r1, "a move on the user (Swords Dance) plays on the user")

print("3) a real map battle (OVERWORLD style): a right answer plays the move on the map, and the battle waits for it")
from src.states.battle import TrainerBattleState
story.battle_style = "OVERWORLD"
p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
ow = mk(6)
ow.level = 100
ow.moves = ["FLAMETHROWER", "AIR-SLASH"]
ow.heal_full()
story.player_team = [ow]
tr = next((m for f in p.run.floors for m in f.movers if m.kind == "trainer"), None)
p._battle_trainer(tr)
while p.dialogue_box.visible:
    p.dialogue_box.advance()
    p.update()
to_battle(p)
b = g.current_state
check(isinstance(b, TrainerBattleState) and b.overworld is not None, "the trainer battle is on the map")
seen, held, kinds = set(), 0, []
for _k in range(8000):   # (as dungeon's fight(): each turn Flamethrower and the right answer; tap the text on)
    if g.current_state is not b:
        break
    if b.phase == "SWITCH_PROMPT" and b.btn_no.visible and b.btn_no.callback:
        b.btn_no.callback()
    elif b.phase == "MENU" and not b.dialogue_box.visible:
        b.open_move_menu()
        b.choose_move("FLAMETHROWER")
        b.math_ui.on_click(b.options.index(b.correct_ans))
    elif b.dialogue_box.visible:
        b.dialogue_box.is_finished = True
        if b.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
            b.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif not getattr(b, "_move_seq", None):
            _cb = b.dialogue_box.callback
            if _cb:
                b.dialogue_box.callback = None
                _cb()
            else:
                b.dialogue_box.advance()
    b.feedback_timer = 0
    if g.current_state is b:
        atk = b.overworld.atk
        if atk is not None:
            seen.add(id(atk))
            kinds.append((atk.kind, atk.type))
            if getattr(b, "_move_seq", None) and b._move_seq.get("stage") == "move":
                held += 1
        b.update()
        b.draw()
check(len(seen) >= 1 and ("SPECIAL", "FIRE") in kinds, f"Flamethrower played as a Fire beam on the map ({len(seen)} moves, {sorted(set(kinds))[:4]})")
check(held > 10, f"...and the battle waited on it before the HP bar dropped ({held} frames)")
story.battle_style = "TRADITIONAL"

print("4) a map battle at the bottom edge of a map is drawn clear of the battle's text box (Jordan 11-24)")
from src.utils import Utils as _U
story.battle_style = "OVERWORLD"
p = kanto("KANTO_ROUTE_1")
f = p.run.floor
low = max((t for t in ((x, y) for y in range(f.h) for x in range(f.w)) if f.walkable(*t) and not f.occupied(*t)
           and any(f.walkable(t[0] + dx, t[1]) and not f.occupied(t[0] + dx, t[1]) for dx in (-1, 1))), key=lambda t: t[1])
p.run.player = p.partner = p.partner_from = p.anim_from = low
p.run.reveal()
w, _ = beside(p, "wild")
p._meet_wild(w)
p._pick(1)
to_battle(p)
b = g.current_state
for _ in range(400):
    if b.dialogue_box.visible:
        b.dialogue_box.is_finished = True
        if b.dialogue_box.callback and b.phase == "MESSAGE":
            cb, b.dialogue_box.callback = b.dialogue_box.callback, None
            cb()
    b.update()
    if b.phase == "MENU":
        break
b.overworld.attack(b, {"name": "ROCK-TOMB", "side": "player", "user": b.player_pokemon, "target": b.opponent_pokemon})
for _ in range(9):
    b.overworld.attacking()
b.draw()
pygame.image.save(g.screen, _os.path.join(S, "map_attacks", "edge_battle.png"))
box_top = _U.get_full_dialogue_rect(g).top
mine, foe = b.overworld.catch_points()
check(low[1] >= f.h - 3, f"the battle is at the map's foot (row {low[1]} of {f.h})")
check(mine.bottom <= box_top and foe.bottom <= box_top, f"both Pokemon drawn above the text box (bottoms {mine.bottom}, {foe.bottom}; box at {box_top})")
story.battle_style = "TRADITIONAL"

print("5) side by side first: a battle moves to open ground when they can't stand side by side where they met;")
print("   up and down only when there's no room, with two tiles between; everyone back after (Jordan 11-24)")
story.battle_style = "OVERWORLD"


def open_spot(p, w=4, h=10):
    f = p.run.floor
    f.movers[:] = [m for m in f.movers if m.kind != "wild"]
    for y in range(h, f.h - h):
        for x in range(w, f.w - w):
            if all(f.walkable(x + dx, y + dy) and not f.occupied(x + dx, y + dy) for dx in range(-w, w + 1) for dy in range(-2, 3)):
                return x, y
    return None


def rock(p, t):
    m = core.Mover("figure", t[0], t[1], {"text": "ROCK"})
    p.run.floor.movers.append(m)
    return m


def battle_at(p, foe_at, me_at, shot_name=None):
    f = p.run.floor
    f.movers[:] = [m for m in f.movers if m.kind != "wild"]
    w = core.Mover("wild", foe_at[0], foe_at[1], p._make_wild(_rnd.Random(1)))
    f.movers.append(w)
    p.run.player = p.anim_from = p.partner = p.partner_from = me_at
    p.run.reveal()
    p._meet_wild(w)
    p._pick(1)
    p.walked = to_battle(p, shot_name)
    return g.current_state, w


for _try in ("KANTO_ROUTE_1", "KANTO_ROUTE_22", "KANTO_ROUTE_2"):
    p = kanto(_try)
    c = open_spot(p)
    if c:
        break
check(c is not None, f"an open stretch to test on ({_try} {c})")
x, y = c
rocks = [rock(p, (x + dx, y + dy)) for dx in (-2, -1, 1, 2) for dy in (0, 1)]   # (boxed in left and right where they meet)
b, w = battle_at(p, (x, y), (x, y + 1), "walking_over.png")
ov = b.overworld
check(ov.spot[1] == ov.mine[1] and abs(ov.spot[0] - ov.mine[0]) == 3,
      f"boxed in sideways where they met: the battle stands side by side nearby, two tiles between (foe {ov.spot}, yours {ov.mine})")
check((w.x, w.y) != (x, y) and getattr(p, "_ow_home", None) and p.walked > 6, f"...everyone walked over to open ground ({p.walked} frames)")
b.overworld.attack(b, {"name": "THUNDERBOLT", "side": "player", "user": b.player_pokemon, "target": b.opponent_pokemon})
for _ in range(12):
    ov.attacking()
b.draw()
pygame.image.save(g.screen, _os.path.join(S, "map_attacks", "moved_side_by_side.png"))
p._back_from_battle()
check(p.mode == "OWWALK", "after the battle: you walk back")
walk_back(p)
check(tuple(p.run.player) == (x, y + 1) and not getattr(p, "_ow_home", None) and p.mode == "MAP", f"...back where you met ({p.run.player}, {p.mode})")
for m in rocks:
    p.run.floor.movers.remove(m)
g.change_state(p)
p = kanto(_try)
b, w = battle_at(p, (x, y), (x + 1, y))
ov = b.overworld
check(ov.spot[1] == ov.mine[1] and abs(ov.spot[0] - ov.mine[0]) == 3 and (w.x, w.y) == (x, y),
      f"room where they met: side by side right there, two tiles between (foe {ov.spot}, yours {ov.mine}, walked {p.walked})")
p._back_from_battle()
walk_back(p)
check(p.mode == "MAP", "...and on with the walk after")
g.change_state(p)

p = kanto(_try)
f = p.run.floor
f.movers[:] = [m for m in f.movers if m.kind != "wild"]
walls = [rock(p, (x + dx, y + dy)) for dy in range(-8, 9) for dx in (-1, 1)] + [rock(p, (x, y - 9)), rock(p, (x, y + 9))]   # (a closed corridor one tile wide)
b, w = battle_at(p, (x, y), (x, y + 1))
ov = b.overworld
check(ov.spot[0] == ov.mine[0] and abs(ov.spot[1] - ov.mine[1]) == 3,
      f"no room side by side anywhere near: up and down, two tiles between the Pokemon (foe {ov.spot}, yours {ov.mine})")
b.draw()
pygame.image.save(g.screen, _os.path.join(S, "map_attacks", "vertical_gap.png"))
p._back_from_battle()
walk_back(p)
check(tuple(p.run.player) == (x, y + 1) and (w not in f.movers or (w.x, w.y) == (x, y)), "...and back where you met after")
for m in walls:
    f.movers.remove(m)
story.battle_style = "TRADITIONAL"

print(f"##### {fails} failures")
