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


from src.states.overworld import CityState
from collections import Counter
story.level_cap_mode = "NONE"


def play_eterna(team, correct=True, label=""):
    story.current_area_key = "HEARTHOME_CITY"  # Barry's first city battle (BDSP; Eterna's was removed)
    story.player_team = team
    story.story_flags.pop("defeated_rival_hearthome", None)
    story.story_flags["has_coal_badge"] = True
    story.badges["SINNOH"] = ["COAL", "FOREST"]
    g.change_state(CityState(g))
    intro = g.current_state
    phases = Counter(); stuck = 0; last = None; questions = 0
    for frame in range(9000):
        st = g.current_state
        if isinstance(st, TrainerBattleState):
            b = st
            phases[b.phase] += 1
            key = (b.phase, tuple(b.dialogue_box.text_lines), b.dialogue_box.visible)
            stuck = stuck + 1 if key == last else 0
            last = key
            if stuck > 600:
                return f"STUCK in {b.phase} visible={b.dialogue_box.visible} lines={b.dialogue_box.text_lines} sprite={b.player_pokemon and b.player_pokemon.display_name}"
            if b.phase == "SWITCH_PROMPT" and b.dialogue_box.is_finished:
                click(b.btn_no.rect.center)  # "Change PKMN?" -> keep going
            if b.phase == "MENU" and not b.dialogue_box.visible and not b.turn_actions:
                try:
                    fight(b, correct=correct); questions += 1
                except AssertionError as e:
                    return f"FIGHT failed in phase {b.phase}"
                continue
        elif not hasattr(st, "dialogue_box") and frame > 50 and not isinstance(st, type(intro)):
            break
        box = getattr(st, "dialogue_box", None)
        if box is not None and box.visible:
            click(box.rect.center)
        for e in list(g.ui_manager.elements):
            if getattr(e, "visible", False) and hasattr(e, "advance") and e is not box:
                click(e.rect.center)
        st.update()
        if isinstance(st, CityState) and frame > 50 and not isinstance(g.current_state, TrainerBattleState):
            break
    return f"ok ({type(g.current_state).__name__}, {questions} questions, won={story.story_flags.get('defeated_rival_hearthome')})"


for starter in (390, 387, 393):
    for setup in ("solo", "fainted lead", "two"):
        a = lv(starter + 1, 26)
        team = [a]
        if setup == "fainted lead":
            f = lv(396, 20); f.current_hp = 0; team = [f, a]
        if setup == "two":
            team = [lv(396, 14), a]
        story.user_rival_starter_raw = None
        for correct in (True, False):
            r = play_eterna(team, correct)
            check(r.startswith("ok"), f"#{starter+1} {setup} correct={correct}: {r}")
            for p in team: p.heal_full()
print("##### ", fails, "failures")
