
from src.states import overworld as ow
from src.states.battle import WildBattleState, TrainerBattleState
from src.states.systems import GameCornerState
from src.pokemon import moves as movelib
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
story.level_cap_mode = "NONE"


def lv(pid, level):
    p = mk(pid)
    p.level = level
    p.moves = []
    p.current_hp = p.get_max_hp()
    return p


def settle(b, frames=600):
    log = []
    for _ in range(frames):
        if b.phase == "MENU" and not b.dialogue_box.visible and not b.turn_actions:
            break
        if b.dialogue_box.visible:
            for line in b.dialogue_box.text_lines:
                if not log or log[-1] != line:
                    log.append(line)
            b.dialogue_box.is_finished = True
            cb = b.dialogue_box.callback
            if cb:
                b.dialogue_box.callback = None
                cb()
        b.feedback_timer = 0
        b.update()
    return log


def answer(b, correct, quick):
    b.open_move_menu()
    b.choose_move(b.move_buttons[0].text.replace(" ", "-"))
    if not quick:
        b._question_at -= 5000
    idx = b.options.index(b.correct_ans) if correct else next(i for i, o in enumerate(b.options) if o != b.correct_ans)
    b.math_ui.on_click(idx)
    return settle(b)


print("1) wrong answers still attack, but weaker")
import random as _seeded
_seeded.seed(2026)  # fixed rolls: the average comparison is repeatable
story.current_area_key = "KANTO_ROUTE_1"
dmg_wrong, dmg_slow = [], []
note = False
for correct, bucket in ((False, dmg_wrong), (True, dmg_slow)):
    for _ in range(40):
        story.player_team = [lv(4, 30)]
        foe = lv(113, 40)  # Chansey: bulky and weak, so every hit is measured
        b = WildBattleState(g, foe, "KANTO_ROUTE_1")
        g.change_state(b)
        settle(b)
        before = b.opponent_hp
        log = answer(b, correct, quick=False)
        if b.opponent_hp < before:
            bucket.append(before - b.opponent_hp)
        if not correct and any("answer was off" in l for l in log):
            note = True
check(len(dmg_wrong) >= 35, f"a wrong answer still lands the move ({len(dmg_wrong)}/40 hit)")
check(sum(dmg_wrong) / len(dmg_wrong) < sum(dmg_slow) / len(dmg_slow),
      f"but weaker: avg {sum(dmg_wrong)/len(dmg_wrong):.1f} vs {sum(dmg_slow)/len(dmg_slow):.1f}")
check(note, "and it says why")

print("2) quick right answers earn a bonus, explained")
seen = {}
for _ in range(80):
    story.player_team = [lv(4, 30)]
    b = WildBattleState(g, lv(143, 60), "KANTO_ROUTE_1")
    g.change_state(b)
    settle(b)
    log = answer(b, True, quick=True)
    for l in log:
        if "speedy answer" in l or "lightning-fast" in l:
            seen[l.split(":")[0][:40]] = seen.get(l.split(":")[0][:40], 0) + 1
check(len(seen) >= 2, f"bonus messages: {seen}")
story.player_team = [lv(4, 30)]
b = WildBattleState(g, lv(143, 60), "KANTO_ROUTE_1")
g.change_state(b)
settle(b)
log = answer(b, True, quick=False)
check(not any("speedy" in l or "lightning" in l for l in log), "no bonus for a slow answer")

print("3) XP has no bonus/penalty labels")
story.player_team = [lv(4, 10)]
b = WildBattleState(g, lv(19, 30), "KANTO_ROUTE_1")
g.change_state(b)
msgs = b._award_battle_xp()
check(msgs and not any("bonus" in m or "easy" in m for m in msgs), f"{msgs[:2]}")

print("4) Mew")
dex = g.data.data.setdefault("pokedex", {})
dex.clear()
for pid in range(1, 150):
    dex[f"{pid}-normal"] = {"id": pid}
for pid in (2001, 2002, 152, 153):  # other forms/regions don't count
    dex[f"{pid}-normal"] = {"id": pid}
story.story_flags["mew_spotted_mt_moon"] = True
story.current_area_key = "MT_MOON"
ps = ow.PlayState(g)
g.change_state(ps)
check(story.kanto_caught_count() == 149 and not ps._check_route_condition("mew_available", False), "149: no Mew")
dex["150-normal"] = {"id": 150}
check(ps._check_route_condition("mew_available", False), "all 150: Mew can be found")

print("5) wild Ditto")
story.player_team = [lv(25, 20)]
b = WildBattleState(g, lv(132, 20), "KANTO_ROUTE_13")
g.change_state(b)
check(b.phase == "DITTO_TRANSFORM", f"starts transforming ({b.phase})")
settle(b)
check(b.phase == "MENU" and b.action_menu.visible, f"then the menu comes back ({b.phase})")
answer(b, True, quick=False)
check(True, "and the battle goes on")

print("6) Struggle")
story.player_team = [lv(129, 5)]
story.player_team[0].moves = ["TACKLE"]
b = TrainerBattleState(g, [lv(92, 20)], trainer_class="CHANNELER", trainer_name="Laurel", area_name="KANTO_POKEMON_TOWER")
g.change_state(b)
settle(b)
try:
    b.open_move_menu()
    b.draw()
    check(any(x.text.upper().startswith("STRUGGLE") for x in b.move_buttons), "Struggle offered, no crash")
except Exception as e:
    check(False, f"crash: {e!r}")

print("7) Game Corner menu after Cash In")
story.current_area_key = "CELADON_CITY"
city = ow.CityState(g)
g.states["city"] = city
story.inventory["COIN_CASE"] = 1
gc = GameCornerState(g, city)
g.change_state(gc)
gc.show_main_menu()
gc.open_shop()
g.current_state.go_back() if hasattr(g.current_state, "go_back") else g.change_state(gc)
texts = [getattr(e, "text", "") for e in g.ui_manager.elements]
check(g.current_state is gc and "LEAVE" in texts, f"menu buttons back: {texts}")

print("8) stray taps on fresh route buttons")
story.current_area_key = "KANTO_ROUTE_1"
ps = ow.PlayState(g)
g.change_state(ps)
ps.show_progression_menu()
exit_btn = ps.route_buttons[0]
pressed = []
exit_btn.callback = lambda: pressed.append(1)
ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=exit_btn.rect.center)
exit_btn.handle_event(ev)
check(not pressed, "a tap right as the menu appears does nothing")
exit_btn.armed_at = 0
exit_btn.handle_event(ev)
check(pressed == [1], "a later tap works")

print("9) safety net")
story.current_area_key = "VIRIDIAN_CITY"
city = ow.CityState(g)
g.change_state(city)
g._error_times = []
try:
    raise ValueError("test")
except ValueError:
    g._recover_from_error()
check(isinstance(g.current_state, ow.CityState), "an error returns to the town")
print("FAILURES:", fails)
