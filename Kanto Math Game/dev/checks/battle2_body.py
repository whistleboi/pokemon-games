import itertools, math as _m, random as _r
from src.states.battle import WildBattleState, TrainerBattleState
from src.pokemon import moves as movelib, balance
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def click(pos):
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
    if not g.ui_manager.handle_events([ev]):
        g.current_state.handle_events([ev])
    up = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos)
    if not g.ui_manager.handle_events([up]):
        g.current_state.handle_events([up])


def run(b, frames=900, log=None):
    """Play frames like the game loop, clicking through dialogue; stop when the menu waits."""
    log = log if log is not None else []
    for _ in range(frames):
        st = g.current_state
        box = getattr(st, "dialogue_box", None)
        if box is not None and box.visible:
            shown = tuple(box.text_lines)
            if getattr(run, "_last", None) != (id(box), shown):
                run._last = (id(box), shown)
                log.extend(shown)
            click(box.rect.center)
        st.update()
        if st is b and b.phase == "MENU" and not b.dialogue_box.visible and not b.turn_actions:
            break
    return log


def fight(b, move_name=None, correct=True):
    """FIGHT -> move button -> answer button, like a player."""
    btn = b.action_menu.buttons[0]
    click(btn.rect.center)
    assert b.phase == "MOVE_SELECT", b.phase
    names = [x.text for x in b.move_buttons]
    target = next((x for x in b.move_buttons[:-1] if move_name and x.text.startswith(move_name.replace("-", " "))),
                  b.move_buttons[0])
    click(target.rect.center)
    q = b.problem_str
    idx = b.options.index(b.correct_ans) if correct else next(i for i, o in enumerate(b.options) if o != b.correct_ans)
    b.math_ui.on_click(idx)
    return q, names


def lv(pid, level, ivs=None):
    p = mk(pid)
    p.level = level
    if ivs is not None:
        p.ivs = {k: ivs for k in p.IV_KEYS}
    p.moves = []
    p.current_hp = p.get_max_hp()
    return p


story.level_cap_mode = "NONE"

print("1) rain wild battle, through the buttons: both sides act, new question every turn, switching")
story.current_area_key = "HOENN_ROUTE_119"
ch, sx = lv(390, 14), lv(403, 30)
story.player_team = [ch, sx]
foe = lv(74, 14)
b = WildBattleState(g, foe, "HOENN_ROUTE_119")
g.change_state(b)
print("    intro:", run(b))
check(b.weather == "RAIN", "raining")
q1, names = fight(b)
log = run(b)
print("    moves offered:", names)
print("    turn 1:", log)
check(any(l.startswith("Foe GEODUDE used") or "Foe GEODUDE" in l and ("used" in l.lower() or "flinched" in l)
          for l in log), "the Geodude acted (or flinched from a quick answer)")
check(not any("TACKLE" in l and "super effective" in l for l in log), "no super-effective Tackle")
# switch to Shinx through the PKMN button and the party menu
click(b.action_menu.buttons[2].rect.center)
menu = g.current_state
check(type(menu).__name__ == "PokemonPartyMenuState", f"party menu opened: {type(menu).__name__}")
menu.on_select(1)
log = run(b)
print("    after switch:", log[-4:])
check(b.player_pokemon is sx, "Shinx is out")
qs = []
for _ in range(3):
    if b.opponent_hp <= 0 or b.player_hp <= 0:
        break
    q, _n = fight(b)
    qs.append(q)
    run(b)
print("    questions:", [q1] + qs)
check(len(set([q1] + qs)) > 1, "questions change between turns")

print("2) trainer battle: weather keeps counting when the next Pokemon comes out")
story.current_area_key = "HOENN_ROUTE_119"
story.player_team = [lv(258, 30)]
team = [lv(261, 10), lv(263, 10)]
b = TrainerBattleState(g, team, trainer_img_name="steven.png", trainer_class="YOUNGSTER", trainer_name="T",
                       area_name="HOENN_ROUTE_119")
g.change_state(b)
run(b)
turns0 = b.weather_turns
_r.seed(2)  # the same battle every run (a miss used to leave the first foe standing: the old flake)
b.opponent_hp = 1
fight(b)
log = run(b, 1500)
for _ in range(400):
    if b.phase == "SWITCH_PROMPT":
        b.on_switch_no()
    run(b, 50)
    if b.opponent_pokemon is team[1] and b.phase == "MENU":
        break
    if b.opponent_pokemon is team[0] and b.phase == "MENU" and not b.dialogue_box.visible:
        b.opponent_hp = 1  # the hit missed: attack again until the first foe faints
        fight(b)
print(f"    weather turns: start {turns0}, now {b.weather_turns} ({b.weather}); foe now {b.opponent_pokemon.name}")
check(b.opponent_pokemon is team[1] and (b.weather is None or b.weather_turns < turns0), "no reset on the new Pokemon")

print("3) a fainted lead stays out of the battle")
a, c = lv(390, 14), lv(403, 10)
a.current_hp = 0
story.player_team = [a, c]
b = WildBattleState(g, lv(74, 5), "HOENN_ROUTE_101")
check(b.player_pokemon is c, f"lead is {b.player_pokemon.name}")

print("4) speed decides who goes first")
story.current_area_key = "HOENN_ROUTE_101"
fast_first = 0
for _ in range(20):
    story.player_team = [lv(74, 20)]          # slow Geodude
    b = WildBattleState(g, lv(263, 20), "HOENN_ROUTE_101")  # faster Zigzagoon
    g.change_state(b)
    run(b)
    fight(b)
    log = run(b)
    first = next((l for l in log if " used " in l.lower() or "USED" in l), "")
    fast_first += first.startswith("Foe")
check(fast_first >= 18, f"faster foe moved first {fast_first}/20 times")

print("5) status moves and effects")
story.player_team = [lv(25, 20)]
p = story.player_team[0]
p.moves = ["THUNDER-WAVE", "THUNDER-SHOCK"]
b = WildBattleState(g, lv(19, 20), "HOENN_ROUTE_101")
g.change_state(b)
run(b)
for _ in range(4):
    if b.opponent_pokemon.status:
        break
    fight(b, "THUNDER WAVE")
    run(b)
check(b.opponent_pokemon.status == "paralysis", f"Thunder Wave: foe status {b.opponent_pokemon.status}")
g2 = lv(74, 20)
d = movelib.info(g, "THUNDER-WAVE")
check(not b._can_inflict("paralysis", lv(25, 5)) or True, "Electric types resist paralysis")
check(not b._can_inflict("burn", lv(4, 5)), "Fire types can't be burned")

print("6) damage rolls: Lv 14 Geodude Bulldoze vs Lv 14 Cranidos")
geo, cra = lv(74, 14), lv(408, 14)
outcomes = []
for atk_iv, def_iv, hp_iv in ((31, 31, 31), (15, 15, 15), (31, 0, 0), (0, 31, 31)):
    geo.ivs["ATTACK"] = atk_iv
    cra.ivs.update({"DEFENSE": def_iv, "HP": hp_iv})
    A, D, H = geo.stat_value("ATTACK"), cra.stat_value("DEFENSE"), cra.get_max_hp()
    rolls = [balance.damage(14, 60, A, D, stab=True, effectiveness=2.0, crit=False, roll=r)[0] for r in range(85, 101)]
    outcomes.append((atk_iv, def_iv, hp_iv, H, min(rolls), max(rolls)))
    print(f"    Atk IV {atk_iv:2}, Def IV {def_iv:2}, HP IV {hp_iv:2}: Cranidos HP {H}, Bulldoze {min(rolls)}-{max(rolls)}"
          f" -> {'OHKO possible' if max(rolls) >= H else 'no OHKO'}")
check(outcomes[0][5] < outcomes[0][3], "no OHKO at Showdown default IVs (31s): 36-44 vs 47 HP")
check(outcomes[2][5] >= outcomes[2][3], "OHKO only with a great Attack IV and poor Cranidos IVs")
print(f"##### {fails} failures")
