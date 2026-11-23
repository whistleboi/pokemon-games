# Horde battles (Jordan 11-23, Hoenn H3 DECISIONS #16): five wild Pokemon at once against your one, on main for any
# region to use (src/world/hordes.py, src/states/battle_horde.py). Played through the buttons like a player.
#   bash dev/checks/run.sh hordes
import os as _os
import random as _r
from src.world import hordes
from src.states.battle_horde import HordeBattleState
from src.states.battle import TrainerIntroState
fails = 0
SHOTS = _os.path.join(S, "hordes")
_os.makedirs(SHOTS, exist_ok=True)


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def click(pos):
    for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        ev = pygame.event.Event(kind, button=1, pos=pos)
        left = g.ui_manager.unconsumed([ev])
        if left:
            g.current_state.handle_events(left)


LOG = []


def run(b, frames=3000):
    for _ in range(frames):
        st = g.current_state
        box = getattr(st, "dialogue_box", None)
        if box is not None and box.visible and not box.is_finished:
            if not LOG or LOG[-1] != tuple(box.text_lines):
                LOG.append(tuple(box.text_lines))
            click(box.rect.center)
        st.update()
        if st is b and b.phase in ("MENU",) and not b.dialogue_box.visible:
            return True
        if st is not b and not isinstance(st, TrainerIntroState):
            return False
    return False


def lines():
    return [l for t in LOG for l in t]


def mon(pid, level, moves):
    p = mk(pid)
    p.level = level
    p.moves = list(moves)
    p.current_hp = p.get_max_hp()
    return p


def answer(b, right=True):
    idx = b.options.index(b.correct_ans) if right else next(i for i, o in enumerate(b.options) if o != b.correct_ans)
    b.math_ui.on_click(idx)


def pick_move(b, move):
    click(b.action_menu.buttons[0].rect.center)
    btn = next(x for x in b.move_buttons[:-1] if x.text == move.replace("-", " "))
    click(btn.rect.center)


story.level_cap_mode = "NONE"
story.enter_region("HOENN")
story.story_flags["hoenn_version"] = "OMEGA_RUBY"
story.current_area_key = "HOENN_ROUTE_101" if "HOENN_ROUTE_101" in g.loader.area_data["STORY_PROGRESSION"] else story.current_area_key

print("1) the area hook: a horde pool and rate")
area = {"horde_pool_percentages": {"41": 60, "41+41+41+42+42": 40}, "horde_rate": 0.25, "horde_levels": [6, 8]}
check(hordes.rate(g, area) == 0.25 and hordes.rate(g, {}) == 0, "a rate only with a horde pool")
picks = [hordes.pick(g, area, _r.Random(i)) for i in range(40)]
check(all(len(p) == 5 for p in picks) and [41] * 5 in picks and [41, 41, 41, 42, 42] in picks,
      "five each: all one species, or the mixed five as written")
h = hordes.make(g, story.current_area_key, area, _r.Random(3))
check(len(h) == 5 and all(6 <= p.level <= 8 for p in h), f"made at the horde levels ({[p.level for p in h]})")
rolls = sum(hordes.roll(g, area, _r.Random(i)) for i in range(400))
check(60 <= rolls <= 140, f"about a quarter of encounters ({rolls} of 400)")

print("2) five foes, your one")
blast = mon(9, 60, ["SURF", "ICE-BEAM", "PROTECT", "TACKLE"])
story.player_team = [blast, mon(25, 40, ["THUNDERBOLT"])]
foes = [mon(143, 40, ["SPLASH"]) for _ in range(5)]   # (sturdy: they last a few turns)
b = HordeBattleState(g, foes, story.current_area_key)
g.change_state(b)
LOG.clear()
run(b)
check(len([m for m in b.o_slots if m is not None]) == 5 and b.p_slots[0] is blast and b.p_slots[1] is None,
      "five wild Pokemon out, your first Pokemon alone")
check(any("A horde of wild SNORLAX appeared!" in l for l in lines()), f"the opening line ({lines()[:1]})")
g.current_state.draw()
pygame.image.save(g.screen, _os.path.join(SHOTS, "horde.png"))
check(True, "drawn (horde.png)")

print("3) a ball only when one is left")
LOG.clear()
b.throw_from_bag()
run(b)
check(any("more than one wild Pokemon" in l for l in lines()), "five standing: no aiming")

print("4) a single-target move asks which; a spread move hits all five")
pick_move(b, "ICE-BEAM")
_tn = [x.text for x in b._target_buttons if str(x.text).upper() not in ("BACK", "CANCEL")]
check(b.phase == "TARGET_SELECT" and len(_tn) == 5, f"Ice Beam: five to pick from ({_tn})")
b._target_back() if hasattr(b, "_target_back") else None
for _ in range(5):
    if b.phase == "MENU":
        break
    click(b.move_buttons[-1].rect.center) if getattr(b, "move_buttons", None) else None
run(b)
hp0 = [f.current_hp for f in b.o_slots]
xp0 = (blast.level, blast.xp)
LOG.clear()
if b.phase != "MENU":
    b.return_to_menu()
pick_move(b, "SURF")
check(b.phase == "BATTLE", f"Surf asks no target ({b.phase})")
answer(b, True)
run(b)
hit = [f for f, h in zip(b.o_slots, hp0) if f is not None and f.current_hp < h]
gone = [h for f, h in zip(b.o_slots, hp0) if f is None or f.current_hp <= 0]
check(len(hit) + len(gone) == 5, f"all five hit ({len(hit)} hurt, {len(gone)} down)")

print("5) winning: experience for each one down")
weak = [mon(41, 5, ["SPLASH"]) for _ in range(5)]
blast.current_hp = blast.get_max_hp()
b2 = HordeBattleState(g, weak, story.current_area_key)
g.change_state(b2)
run(b2)
xp0 = (blast.level, blast.xp)
LOG.clear()
pick_move(b2, "SURF")
answer(b2, True)
run(b2, frames=6000)
check(all(f is None or f.current_hp <= 0 for f in b2.o_slots), "Surf knocks out all five Zubat")
check((blast.level, blast.xp) > xp0, f"experience gained ({xp0} -> {(blast.level, blast.xp)})")
check(any("defeated" in l for l in lines()), "the wild Pokemon were defeated")
print(f"##### {fails} failures")
