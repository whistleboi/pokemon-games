# Double battles and the no-switch rule (11-18): Luana's Kumquat Gym double battle (Orange 5.7) played through the
# buttons to the badge, the doubles-only moves taking effect, the one-Pokemon fallback, both battle styles drawn,
# and Drake's no-switch six-on-six. Screenshots go to <out>/doubles (or DOUBLES_SHOTS).
import os as _os
from src.states import overworld as ow
from src.states.overworld import common as _common
from src.states.battle import TrainerBattleState, TrainerIntroState
from src.states.battle_double import DoubleBattleState, battle_options
from src.pokemon import moves as movelib
fails = 0
SHOTS = _os.environ.get("DOUBLES_SHOTS") or _os.path.join(S, "doubles")
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


def shot(name):
    g.current_state.draw()
    pygame.image.save(g.screen, _os.path.join(SHOTS, name))


LOG = []


def run(b, frames=3000, until=None):
    """Play frames like the game loop, tapping through text, till b waits for a choice (or `until`)."""
    for _ in range(frames):
        st = g.current_state
        box = getattr(st, "dialogue_box", None)
        if box is not None and box.visible and not box.is_finished:
            if not LOG or LOG[-1] != tuple(box.text_lines):
                LOG.append(tuple(box.text_lines))
            click(box.rect.center)
        st.update()
        if until and until():
            return True
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


def fight(b, move, target=None, right=True):
    """FIGHT -> the move -> (the target) -> the answer, like a player."""
    click(b.action_menu.buttons[0].rect.center)
    assert b.phase == "MOVE_SELECT", b.phase
    btn = next(x for x in b.move_buttons[:-1] if x.text == move.replace("-", " "))
    click(btn.rect.center)
    if b.phase == "TARGET_SELECT":
        names = [x.text for x in b._target_buttons]
        pick = next((x for x in b._target_buttons if target and x.text == target), b._target_buttons[0])
        click(pick.rect.center)
    else:
        names = []
    assert b.phase == "BATTLE", b.phase
    answer(b, right)
    for _ in range(80):   # (the answer's cheer, then the next Pokemon's turn or the turn itself)
        b.update()
        if b.phase != "ANSWER_FEEDBACK":
            break
    return names


story.level_cap_mode = "NONE"
story.enter_region("ORANGE")
prog = g.loader.area_data["STORY_PROGRESSION"]

print("1) Luana's battle is a double battle, from her data (5.7: Marowak + Alakazam, Lv 46)")
story.current_area_key = "KUMQUAT_ISLAND"
story.badges = {"ORANGE": ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL"]}
_lu = next(o for o in prog["KUMQUAT_ISLAND"]["explore_options"] if o["text"] == "Luana ")["event"]["battle"]
check(battle_options(_lu) == {"double": True}, f"her event battle says double ({battle_options(_lu)})")
check(battle_options(prog["KUMQUAT_ISLAND"]["gym"]["leader"]) == {"double": True}, "...and so does the Gym's leader record")
blast = mon(9, 60, ["SURF", "ICE-BEAM", "HELPING-HAND", "PROTECT"])
pika = mon(26, 58, ["THUNDERBOLT", "EARTHQUAKE", "FOLLOW-ME", "QUICK-ATTACK"])
story.player_team = [blast, pika, mon(3, 55, ["GIGA-DRAIN"])]
story.story_flags.pop("orange_luana_badge", None)
intro = _common._start_event_battle(g, "KUMQUAT_ISLAND", dict(_lu), "orange_luana_badge")
b = intro.next_state
check(isinstance(b, DoubleBattleState) and b.is_doubles, f"the battle is a DoubleBattleState ({type(b).__name__})")
check([(p.id, p.level) for p in b.o_slots] == [(105, 46), (65, 46)], f"Luana sends both out: {[(p.id, p.level) for p in b.o_slots]}")
check(b.p_slots == [blast, pika], "your first two able Pokemon go out")
g.change_state(intro)
for _ in range(600):
    st = g.current_state
    if st is b:
        break
    if st.dialogue_box.visible and not st.dialogue_box.is_finished:
        LOG.append(tuple(st.dialogue_box.text_lines))
        st.dialogue_box.advance()
    st.update()
    if getattr(st, "phase", "") == "PLAYER_OUT" and getattr(st, "my_box_in", None) == st.BOX_IN:
        shot("01_intro_send_out.png")
check(g.current_state is b, "the intro hands over to the battle")
check(any("sent out MAROWAK and ALAKAZAM" in l for l in lines()), "intro: \"LUANA sent out MAROWAK and ALAKAZAM!\"")
check(any(l.startswith("Go! BLASTOISE and PIKACHU") or l.startswith("Go! BLASTOISE and RAICHU") for l in lines())
      or any("Go! " in l and " and " in l for l in lines()), "intro: \"Go! X and Y!\"")
run(b)
check(b.phase == "MENU" and b.player_pokemon is blast and b._slot_turn == 0, "BLASTOISE picks first")
shot("02_classic_menu_slot1.png")

print("2) one question per Pokemon's action; the target picked; both foes act; Surf hits everyone it reaches")
q1 = b.problem_str
click(b.action_menu.buttons[0].rect.center)
click(next(x for x in b.move_buttons[:-1] if x.text == "ICE BEAM").rect.center)
check(b.phase == "TARGET_SELECT" and [x.text for x in b._target_buttons][:2] == ["MAROWAK", "ALAKAZAM"],
      f"a single-target move asks which one ({[x.text for x in b._target_buttons]})")
shot("03_classic_target_select.png")
click(next(x for x in b._target_buttons if x.text == "ALAKAZAM").rect.center)
check(b.phase == "BATTLE", "...then the math question")
shot("04_classic_question.png")
answer(b)
for _ in range(80):
    b.update()
    if b.phase != "ANSWER_FEEDBACK":
        break
check(b.phase == "MENU" and b.player_pokemon is b.p_slots[1] and b._slot_turn == 1, "then the partner's turn to choose")
check(b.problem_str != q1 or b.options, f"...with its own question ({q1!r} -> {b.problem_str!r})")
shot("05_classic_menu_slot2.png")
names = fight(b, "THUNDERBOLT", "MAROWAK")
check(b.phase == "D_RESOLVE", f"both picked: the turn plays ({b.phase})")
LOG.clear()
mid = []
for _ in range(400):   # (a frame mid-turn for the picture)
    st = g.current_state
    box = st.dialogue_box
    if box.visible and not box.is_finished:
        if not LOG or LOG[-1] != tuple(box.text_lines):
            LOG.append(tuple(box.text_lines))
        if any("used" in l.lower() for l in box.text_lines) and not mid:
            for _w in range(40):
                st.update()
                if box.is_waiting_for_click:
                    break
            mid.append(1)
            shot("06_classic_turn.png")
        click(box.rect.center)
    st.update()
    if b.phase == "MENU" and not b.dialogue_box.visible or g.current_state is not b:
        break
L = lines()
print("    turn 1:", L)
U = [l.upper() for l in L]
check(any("BLASTOISE USED ICE BEAM" in l for l in U), "BLASTOISE's Ice Beam went off")
check(any(("RAICHU USED THUNDERBOLT" in l or "PIKACHU USED THUNDERBOLT" in l) for l in U), "...and its partner's Thunderbolt")
check(any("FOE MAROWAK USED" in l for l in U), "Foe MAROWAK acted")
check(any("FOE ALAKAZAM USED" in l for l in U) or any("FOE ALAKAZAM" in l and "FAINTED" in l for l in U), "Foe ALAKAZAM acted (or went down first)")

print("3) spread moves, Helping Hand, Follow Me: the doubles-only effects take effect")


def fresh_double(team_ids, levels, mine, moves="SPLASH"):
    foes = [mon(pid, lv_, [moves]) for pid, lv_ in zip(team_ids, levels)]
    story.player_team = mine
    bb = TrainerBattleState(g, foes, trainer_sprite=b.trainer_sprite, trainer_class="TWINS", trainer_name="Amy & Liv",
                            area_name="KUMQUAT_ISLAND", options={"double": True})
    g.change_state(bb)
    run(bb)
    return bb


a1, a2 = mon(9, 50, ["SURF", "HELPING-HAND"]), mon(25, 50, ["THUNDERBOLT", "FOLLOW-ME", "EARTHQUAKE"])
bb = fresh_double([143, 143], [60, 60], [a1, a2])   # (two sturdy Snorlax: the battle lasts a few turns)
check(isinstance(bb, DoubleBattleState), "any trainer battle with options {\"double\": true} is a double battle (Twins later)")
hp0 = [f.current_hp for f in bb.o_slots]
LOG.clear()
fight(bb, "SURF")
check(bb.phase == "MENU" and bb._slot_turn == 1, "Surf asks no target (it hits all it reaches)")
fight(bb, "FOLLOW-ME")
run(bb)
L = lines()
print("    spread turn:", L)
hit_both = all(f.current_hp < h for f, h in zip(bb.o_slots, hp0) if f is not None)
check(hit_both, f"Surf hit both foes ({hp0} -> {[f.current_hp for f in bb.o_slots]})")
check(a2.current_hp < a2.get_max_hp(), f"...and your own partner (Surf hits everyone else on the field: {a2.current_hp}/{a2.get_max_hp()})")
check(any("became the center of attention" in l for l in L), "Follow Me works (the center of attention)")
# Helping Hand then Earthquake: the partner gets hit by Earthquake too (Luana's warning)
a1, a2 = mon(9, 50, ["SURF", "HELPING-HAND"]), mon(26, 80, ["THUNDERBOLT", "FOLLOW-ME", "EARTHQUAKE"])
bb = fresh_double([143, 143], [70, 70], [a1, a2])
if True:
    LOG.clear()
    hpa1 = a1.current_hp
    fight(bb, "HELPING-HAND")
    fight(bb, "EARTHQUAKE")
    run(bb)
    L = lines()
    print("    helping hand turn:", L)
    check(any("is ready to help" in l for l in L), "Helping Hand works on the partner (no \"no one to help\")")
    check(not any("no one to help" in l for l in L), "...and doesn't fail")
    check(a1.current_hp < hpa1 or any("BLASTOISE" in l and ("doesn't affect" in l or "protected" in l) for l in L),
          f"Earthquake hits your own partner too ({hpa1} -> {a1.current_hp})")
check(bb.spread_mult([1, 2]) == 0.75 and bb.spread_mult([1]) == 1.0, "spread moves: 0.75x on more than one target")

print("3b) switching by choice, an item, and a fainted Pokemon replaced from the party (at the end of the turn)")
k1, k2, k3 = mon(129, 5, ["SPLASH"]), mon(9, 60, ["SURF", "PROTECT"]), mon(3, 60, ["GIGA-DRAIN"])
bb = fresh_double([143, 143], [90, 90], [k1, k2, k3], moves="BODY-SLAM")
click(bb.action_menu.buttons[2].rect.center)   # POKEMON
check(type(g.current_state).__name__ == "PokemonPartyMenuState", "POKEMON opens the party list")
g.current_state.on_select(1)
check(type(g.current_state).__name__ == "PokemonPartyMenuState" and not bb._plans, "...BLASTOISE, already out, can't be picked")
g.current_state.on_select(2)
check(g.current_state is bb and bb._slot_turn == 1 and bb._plans[id(k1)]["kind"] == "switch", "VENUSAUR picked for MAGIKARP's spot; BLASTOISE's turn")
bb.on_item_used()   # (as the Bag does after an item)
check(bb.phase == "D_RESOLVE" and bb._plans[id(k2)]["kind"] == "item", "an item takes BLASTOISE's action; the turn plays")
LOG.clear()
run(bb, until=lambda: type(g.current_state).__name__ == "PokemonPartyMenuState")
L = lines()
print("    switch turn:", L)
check(bb.p_slots[0] is k3 and any("Come back, MAGIKARP" in l for l in L) and any("Go! VENUSAUR" in l for l in L),
      "the switch goes first: Come back, MAGIKARP! Go! VENUSAUR!")
for _t in range(6):   # (BLASTOISE takes Body Slams till it faints: then you pick who replaces it)
    if type(g.current_state).__name__ == "PokemonPartyMenuState" or bb.phase != "MENU":
        break
    fight(bb, "GIGA-DRAIN") if bb._slot_turn == 0 else None
    if bb.phase == "MENU":
        fight(bb, "SURF")
    run(bb, until=lambda: type(g.current_state).__name__ == "PokemonPartyMenuState")
pm = g.current_state
if type(pm).__name__ == "PokemonPartyMenuState":
    check(pm.context == "forced_switch" and bb.phase == "D_PICK", "a fainted Pokemon of yours: the party list to replace it")
    gone = [i for i, p in enumerate(story.player_team) if p.current_hp > 0 and not bb._has(bb.p_slots, p)]
    pm.on_select(gone[0])
    run(bb)
    check(bb._has(bb.p_slots, story.player_team[gone[0]]) and bb.phase in ("MENU", "OUTRO"), f"...it comes in ({bb.phase})")
else:
    check(bb.phase == "OUTRO" or not any(p.current_hp <= 0 for p in bb.p_slots if p),
          f"(no replacement needed: {bb.phase})")

print("4) only one Pokemon able to battle: you battle with one (the games' rule)")
solo = mon(9, 70, ["SURF", "ICE-BEAM"])
story.player_team = [solo, mon(25, 30, ["TACKLE"])]
story.player_team[1].current_hp = 0
foes = [mon(19, 20, ["TACKLE"]), mon(19, 20, ["TACKLE"])]
b1 = TrainerBattleState(g, foes, trainer_class="TWINS", trainer_name="Amy & Liv", area_name="KUMQUAT_ISLAND",
                        options={"double": True})
g.change_state(b1)
run(b1)
check(b1.p_slots[0] is solo and b1.p_slots[1] is None, "one slot on your side, two foes")
for _ in range(10):
    if b1.phase != "MENU":
        break
    fight(b1, "SURF")
    run(b1)
check(b1.player_won or b1.phase in ("VICTORY_TEXT", "REWARD_TEXT"), f"...and it plays to the win ({b1.phase})")

print("5) Luana's double battle to the end: the Jade Star Badge")
blast.heal_full(); pika.heal_full()
story.player_team = [mon(9, 70, ["SURF", "ICE-BEAM"]), mon(26, 70, ["THUNDERBOLT", "EARTHQUAKE"]), mon(3, 65, ["GIGA-DRAIN"])]
story.badges = {"ORANGE": ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL"]}
story.story_flags.pop("orange_luana_badge", None)
intro = _common._start_event_battle(g, "KUMQUAT_ISLAND", dict(_lu), "orange_luana_badge")
b = intro.next_state
g.change_state(b)
run(b)
turns = 0
while g.current_state is b and b.phase == "MENU" and turns < 30:
    turns += 1
    fight(b, "SURF" if b._slot_turn == 0 else "THUNDERBOLT")
    run(b, until=lambda: b.phase in ("VICTORY_TEXT", "OUTRO"))
check(b.player_won, f"won in {turns} turns")
for _ in range(400):
    st = g.current_state
    if st is not b:
        break
    if b.phase in ("VICTORY_TEXT", "REWARD_TEXT"):
        b.dialogue_box.is_finished = True
        b.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=b.dialogue_box.rect.center)])
    st.update()
check(story.story_flags.get("orange_luana_badge") and "JADE_STAR" in story.badges.get("ORANGE", []),
      f"Jade Star Badge won ({story.badges.get('ORANGE')})")

print("6) the OVERWORLD style draws a double battle on the map")
story.battle_style = "OVERWORLD"
g.dungeon_routes = True
from src.states.overworld.dungeon import DungeonState
from src.states.overworld.overworld_battle import OverworldView
from src.states.overworld import PlayState
story.current_area_key, story.last_area_key = "KANTO_ROUTE_1", "PALLET_TOWN"   # (a grassy land route)
g.walk_town_pos = None
g.walk_town_room = None
dst = PlayState(g)
g.states["play"] = dst
g.change_state(dst)
for _ in range(5):
    g.current_state.update()
dst = g.current_state
ok_ow = hasattr(dst, "run") and getattr(dst.run, "floor", None) is not None
check(ok_ow, f"a walked route to battle on ({type(dst).__name__})")
if ok_ow:
    import types
    f = dst.run.floor
    sx, sy = dst.run.player
    open_spot = min(((x, y) for y in range(2, f.h - 4) for x in range(7, f.w - 3)
                     if all(f.walkable(x - i, y + j) and not f.occupied(x - i, y + j) for i in range(7) for j in range(3))),
                    key=lambda t: abs(t[0] - sx) + abs(t[1] - sy), default=None)
    check(open_spot is not None, f"an open stretch of the route for the line-up ({open_spot})")
    px, py = open_spot or dst.run.player
    dst.run.player = (px, py)
    mover = types.SimpleNamespace(kind="trainer", x=px - 5, y=py, facing=(1, 0), payload=(0, {}))
    a1, a2 = mon(9, 50, ["SURF", "ICE-BEAM"]), mon(25, 50, ["THUNDERBOLT", "QUICK-ATTACK"])
    story.player_team = [a1, a2]
    bo = TrainerBattleState(g, [mon(19, 45, ["TACKLE"]), mon(41, 45, ["TACKLE"])], trainer_class="TWINS",
                            trainer_name="Amy & Liv", area_name="KANTO_ROUTE_1", options={"double": True})
    bo.overworld = OverworldView(dst, mover)
    g.change_state(bo)
    run(bo)
    shot("07_overworld_menu.png")
    fight(bo, "ICE-BEAM", "ZUBAT")
    for _ in range(60):
        box = bo.dialogue_box
        if box.visible and not box.is_finished and not any("used" in l.lower() for l in box.text_lines):
            click(box.rect.center)
        bo.update()
    fight(bo, "THUNDERBOLT") if bo.phase == "MENU" else None
    seen = False
    for _ in range(300):
        box = bo.dialogue_box
        if box.visible and not box.is_finished:
            if any("used" in l.lower() for l in box.text_lines) and not seen and bo._move_seq:
                for _w in range(40):
                    bo.update()
                    if box.is_waiting_for_click:
                        break
                seen = True
                shot("08_overworld_turn.png")
            click(box.rect.center)
        bo.update()
        if bo.phase == "MENU" and not box.visible:
            break
    rects = bo.overworld._double_rects(bo)
    rs = [r for r, _m, _p in rects.values()]
    check(len(rs) == 4 and len({(r.x, r.y) for r in rs}) == 4, f"four Pokemon on four tiles ({[(r.x, r.y) for r in rs]})")
    check(bo.phase in ("MENU", "VICTORY_TEXT", "REWARD_TEXT", "D_RESOLVE") and bo.turn_count >= 1, f"the battle plays on the map ({bo.phase}, turn {bo.turn_count})")
story.battle_style = "CLASSIC"
g.dungeon_routes = False

print("7) the HUD: four boxes, none overlapping, all on screen (1280x720)")
story.player_team = [mon(9, 50, ["SURF"]), mon(25, 50, ["THUNDERBOLT"])]
bh = TrainerBattleState(g, [mon(105, 46, ["TACKLE"]), mon(65, 46, ["TACKLE"])], trainer_class="GYM_LEADER",
                        trainer_name="Luana", area_name="KUMQUAT_ISLAND", options={"double": True})
g.change_state(bh)
run(bh)
boxes = [bh._box_rect(s, k) for s in ("opponent", "player") for k in (0, 1)]
screen_r = pygame.Rect(0, 0, 1280, 720)
check(all(screen_r.contains(r) for r in boxes), f"on screen: {boxes}")
check(not any(boxes[i].colliderect(boxes[j]) for i in range(4) for j in range(i + 1, 4)), "no two boxes overlap")
text_top = 720 - int(720 * 0.25)
check(all(r.bottom <= text_top for r in boxes), "all above the text box")
def _ink(m):
    img, r = bh._sprite_at(m)
    return img.get_bounding_rect().move(r.topleft)
sprites = [_ink(m) for m in bh.p_slots + bh.o_slots]
check(not any(r.colliderect(s) for r in boxes[:2] for s in sprites[2:]), "the foes' boxes clear of the foes")
check(not any(r.colliderect(s) for r in boxes[2:] for s in sprites[2:]), "your boxes clear of the foes")
check(not sprites[2].colliderect(sprites[3]) and not sprites[0].colliderect(sprites[1]), "the two on each side stand apart")

print("8) singles stay singles")
story.player_team = [mon(9, 50, ["SURF"]), mon(25, 50, ["THUNDERBOLT"])]
bs = TrainerBattleState(g, [mon(19, 20, ["TACKLE"])], trainer_class="YOUNGSTER", area_name="KUMQUAT_ISLAND")
check(type(bs) is TrainerBattleState and not bs.is_doubles and not bs.no_switch, "no options: an ordinary single battle")

print("9) Drake's six-on-six: no switching by choice; a fainted Pokemon is still replaced")
story.badges["ORANGE"] = ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL", "JADE_STAR"]
story.current_area_key = "PUMMELO_ISLAND"
story.story_flags["gym_progress_PUMMELO_ISLAND"] = 0
story.story_flags["orange_drake_met"] = True
weak = mon(129, 5, ["SPLASH"])
story.player_team = [weak, mon(9, 70, ["SURF"])]
g.transitioning = False
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
lobby.challenge_gym()
st = g.current_state
bd = st.next_state if isinstance(st, TrainerIntroState) else st
check(isinstance(bd, TrainerBattleState) and bd.no_switch and not bd.is_doubles, f"Drake's battle has the no-switch rule ({getattr(bd, 'no_switch', None)!r})")
g.change_state(bd)
run(bd)
click(bd.action_menu.buttons[2].rect.center) if len(bd.action_menu.buttons) > 2 else bd.open_party_menu()
if g.current_state is not bd:
    check(False, f"POKEMON opened the party list ({type(g.current_state).__name__})")
    g.change_state(bd)
else:
    check(bd.phase == "MESSAGE" and "Drake's rule" in " ".join(bd.dialogue_box.text_lines),
          f"POKEMON: the rule is shown, no party list ({bd.dialogue_box.text_lines})")
    for _w in range(60):
        bd.dialogue_box.update()
        if bd.dialogue_box.is_waiting_for_click:
            break
    shot("09_no_switch_message.png")
run(bd)
check(bd.player_pokemon is weak and bd.phase == "MENU", "...and you're back at the menu with the same Pokemon")
for _ in range(8):   # (the Magikarp goes down: the replacement is still asked for)
    if g.current_state is not bd or bd.phase != "MENU":
        break
    names = fight(bd, "SPLASH")
    for _f in range(1500):
        stc = g.current_state
        if stc is not bd:
            break
        box = bd.dialogue_box
        if box.visible and not box.is_finished:
            click(box.rect.center)
        bd.update()
        if bd.phase == "MENU" and not box.visible:
            break
    if g.current_state is not bd:
        break
check(type(g.current_state).__name__ == "PokemonPartyMenuState" and g.current_state.context == "forced_switch",
      f"a fainted Pokemon is still replaced (the party list: {type(g.current_state).__name__})")
if type(g.current_state).__name__ == "PokemonPartyMenuState":
    g.current_state.on_select(1)
    run(bd)
    check(bd.player_pokemon is story.player_team[1] and bd.phase == "MENU", f"...BLASTOISE comes in ({bd.player_pokemon.display_name}, {bd.phase})")

# ---- the games' own pairs (11-18): FireRed / LeafGreen's double-battle trainers (the trainer table's double flag),
# Kanto and Sevii: Twins, Young / Cool Couples, Sis and Bro, Crush Kin
print("10) FireRed's pairs are double battles")
import json as _json
_pairs = {"pokemon_area_data.json": ["Eli & Anne", "Ray & Tyra", "Gia & Jes", "Kiri & Jan", "Ron & Mya", "Lea & Jed", "Lia & Luc", "Lil & Ian"],
          "sevii_area_data.json": ["Mik & Kia", "Joy & Meg", "Ava & Geb", "Miu & Mia", "Eve & Jon", "Lex & Nya"]}
_found = {}
for _f, _names in _pairs.items():
    _d = _json.load(open(os.path.join("assets", _f), encoding="utf-8"))
    for _a in _d["STORY_PROGRESSION"].values():
        for _t in (_a.get("trainer_pool") or []) if isinstance(_a, dict) else []:
            if isinstance(_t, dict) and _t.get("name") in _names:
                _found[_t["name"]] = _t
check(len(_found) == 14 and all(battle_options(t).get("double") for t in _found.values()),
      f"all 14 pairs are in the data, each marked double ({len(_found)}: {[n for n, t in _found.items() if not battle_options(t).get('double')]})")
# (and every other region's: Twins, couples, Sis and Bro, Double Team... and Tate & Liza fight as a pair in their games;
#  Orange's Jessie & James are one trainer in 5.7)
import glob as _glob
_single = []
for _f in _glob.glob(os.path.join("assets", "*_area_data.json")):
    def _walk(o):
        if isinstance(o, dict):
            if "class" in o and "team" in o and isinstance(o.get("name"), str) and "&" in o["name"] and o["name"] != "Jessie & James":
                if not battle_options(o).get("double"):
                    _single.append((os.path.basename(_f), o["name"]))
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)
    _walk(_json.load(open(_f, encoding="utf-8")))
check(not _single, f"every region's pairs are double battles (not yet: {_single})")
_tl = _json.load(open(os.path.join("assets", "hoenn_area_data.json"), encoding="utf-8"))["STORY_PROGRESSION"]["MOSSDEEP_CITY"]["gym"]["leader"]
story.player_team = [mon(9, 50, ["SURF"]), mon(26, 50, ["THUNDERBOLT"])]
_b = TrainerBattleState(g, [mon(p_, l_, ["TACKLE"]) for p_, l_ in zip(_tl["team"], _tl["levels"])], trainer_class=_tl["class"],
                        trainer_name=_tl["name"], options=battle_options(_tl))
check(isinstance(_b, DoubleBattleState) and [p_.id for p_ in _b.o_slots] == [337, 338],
      f"Tate & Liza: a double battle, Lunatone and Solrock together ({type(_b).__name__})")
_t = _found.get("Eli & Anne")
if _t:
    story.player_team = [mon(9, 40, ["SURF"]), mon(26, 40, ["THUNDERBOLT"])]
    _team = [mon(pid, lv, ["TACKLE"]) for pid, lv in zip(_t["team"], _t["levels"])]
    _b = TrainerBattleState(g, _team, trainer_class=_t["class"], trainer_name=_t["name"], options=battle_options(_t))
    check(isinstance(_b, DoubleBattleState) and len(_b.o_slots) == 2, f"Twins Eli & Anne: a double battle, both their Pokemon out ({type(_b).__name__})")


# ---- tag battles (11-18): a partner's Pokemon in your second slot, run by the AI; two trainers on the other side
print("11) a tag battle: your partner beside you, two trainers against you")
story.enter_region("HOENN")
story.current_area_key = "MOSSDEEP_CITY"
_tag = {"name": "Maxie", "class": "MAGMA_LEADER", "sprite": "maxie.png", "team": [229, 323], "levels": [30, 30],
        "rewards": {"balls": 2},
        "battle_options": {"double": True,
                           "partner": {"name": "Steven", "class": "CHAMPION", "sprite": "steven.png", "team": [376, 306], "levels": [80, 80]},
                           "second_trainer": {"name": "Tabitha", "class": "MAGMA_ADMIN", "sprite": "tabitha.png", "team": [324, 262],
                                              "levels": [28, 28], "rewards": {"balls": 3}}}}
_me1, _me2 = mon(260, 90, ["SPLASH"]), mon(26, 90, ["SPLASH"])   # (you splash: Steven does the fighting)
story.player_team = [_me1, _me2]
LOG.clear()
intro = _common._start_event_battle(g, "MOSSDEEP_CITY", dict(_tag), "test_tag_battle")
b = intro.next_state
check(isinstance(b, DoubleBattleState) and b.partner_name == "Steven" and b.foe2_name == "Tabitha",
      f"a double battle with a partner and a second trainer ({type(b).__name__}, {b.partner_name}, {b.foe2_name})")
check(b.p_slots[0] is _me1 and b.is_partner(b.p_slots[1]) and b.p_slots[1].id == 376,
      f"your SWAMPERT and Steven's METAGROSS ({[p.id for p in b.p_slots]})")
check([p.id for p in b.o_slots] == [229, 324] and len(b.opponent_team) == 4,
      f"Maxie's HOUNDOOM and Tabitha's TORKOAL, each its own trainer's ({[p.id for p in b.o_slots]})")
check(b.side_of(b.p_slots[1]) == "player" and b.rewards.get("balls") == 5, f"the partner's on your side; both trainers pay ({b.rewards})")
g.change_state(intro)
for _ in range(400):   # (a picture of the challenge: both trainers, you and your partner)
    intro.update()
    if intro.phase == "CHALLENGE" and intro.t > 40:
        break
shot("tag_intro.png")
for _ in range(2000):   # (the send-out: a ball onto each foe's spot; a picture as the second one lands)
    if intro.dialogue_box.visible and not intro.dialogue_box.is_finished:
        LOG.append(tuple(intro.dialogue_box.text_lines))
        click(intro.dialogue_box.rect.center)
    intro.update()
    _sm = intro.__dict__.get("_summons", {}).get("opponent") or []
    if len(_sm) == 2 and _sm[1].phase == 1:
        shot("tag_sendout.png")
        break
check(len(intro.__dict__.get("_summons", {}).get("opponent") or []) == 2, "the send-out: a ball thrown onto each foe's spot")
run(b, 4000)
check(len(intro.__dict__.get("_summons", {}).get("player") or []) == 2, "...and onto each of your side's (yours and Steven's)")
_said = lines()
check(any("challenged by MAXIE AND TABITHA" in l for l in _said), f"\"You are challenged by Maxie and Tabitha!\" ({[l for l in _said if 'challenged' in l]})")
check(any(l == "TABITHA sent out TORKOAL!" for l in _said) and any(l == "STEVEN sent out METAGROSS!" for l in _said),
      f"each trainer sends out its own, Steven his ({[l for l in _said if 'sent out' in l]})")
shot("tag_intro_done.png")
check(g.current_state is b and b.phase == "MENU" and b._slot_turn == 0, f"you choose for your own Pokemon only ({b.phase}, slot {b._slot_turn})")
_turns = 0
_all = []
for _ in range(60):
    if g.current_state is not b and b.phase == "D_PICK" and hasattr(g.current_state, "on_select"):
        g.current_state.on_select(next(i for i, p in enumerate(story.player_team) if p.current_hp > 0))   # (yours fainted: send the next)
        run(b, 3000, until=lambda: g.current_state is b and b.phase == "MENU" and not b.dialogue_box.visible)
        continue
    if g.current_state is not b or b.phase != "MENU":
        break
    LOG.clear()
    fight(b, "SPLASH")
    _turns += 1
    run(b, 3000, until=lambda: g.current_state is b and b.phase == "MENU" and not b.dialogue_box.visible)
    _all += lines()
    if not any(p is not None and p.current_hp > 0 for p in b.opponent_team):
        break
check(not any(p.current_hp > 0 for p in b.opponent_team) and _me1.current_hp >= 0,
      f"you only splashed: Steven's Pokemon picked their own moves and beat all four ({_turns} turns; left {[p.current_hp for p in b.opponent_team]}; mine {[p.current_hp for p in b.p_slots if p]}; stopped in {type(g.current_state).__name__} {b.phase})")
check(_me1.xp > 0 and not any("METAGROSS gained" in l or "SKARMORY gained" in l for l in _all), f"your Pokemon earn XP, Steven's don't ({_me1.xp})")
check(not any(p.current_hp > 0 for p in b.opponent_team),
      f"the battle plays to the end ({_turns} turns; foes left {[p.current_hp for p in b.opponent_team]})")
check(story.player_team == [_me1, _me2], "Steven's Pokemon never join your party")

print("12) the Mossdeep Space Center: Steven beside you against the leader and an admin (Emerald's multi battle)")
_boss = next(t for t in g.loader.area_data["STORY_PROGRESSION"]["HOENN_SPACE_CENTER"]["trainer_pool"]
             if t.get("victory_flag") == "space_center_cleared")
for _ver, _want, _mons in (("OMEGA_RUBY", "MAGMA ADMIN TABITHA", [323, 262, 42]), ("ALPHA_SAPPHIRE", "AQUA ADMIN MATT", [319, 262, 42])):
    story.story_flags["hoenn_version"] = _ver
    intro = _common._start_event_battle(g, "HOENN_SPACE_CENTER", dict(_boss), "space_center_cleared")
    b = intro.next_state
    _second = [p.id for p in b.foe_teams[1]] if b.foe_teams else []
    check(isinstance(b, DoubleBattleState) and b.partner_name == "Steven" and [p.id for p in b.partner_team] == [375, 227, 306]
          and str(b.foe2_name).upper() == _want and _second == _mons,
          f"{_ver}: Steven's Metang, Skarmory, Aggron beside you; {b.trainer_name} and {b.foe2_name} ({_second}) against you")
story.story_flags["hoenn_version"] = "OMEGA_RUBY"
print("14) Intimidate in a double battle lowers both foes' Attack")
story.enter_region("ORANGE")
_gy = mon(130, 50, ["SPLASH"])
bb = fresh_double([19, 20], [30, 30], [mon(26, 50, ["SPLASH"]), mon(25, 50, ["SPLASH"]), _gy])
bb.vol(_gy)["ability"] = "INTIMIDATE"
bb._switch_in("player", 0, _gy, called_back=True)
check([bb.stages(f)["ATTACK"] for f in bb.o_slots] == [-1, -1], f"GYARADOS's Intimidate: both foes' Attack -1 ({[bb.stages(f)['ATTACK'] for f in bb.o_slots]})")
check(bb.stages(bb.p_slots[1])["ATTACK"] == 0, "...and not its partner's")

print("15) Wide Guard and Mat Block guard your side for one turn")
_wg, _mate = mon(68, 50, ["WIDE-GUARD", "SPLASH"]), mon(143, 60, ["SPLASH"])
bb = fresh_double([55, 55], [40, 40], [_wg, _mate], moves="SURF")
_hp0 = (_wg.current_hp, _mate.current_hp)
fight(bb, "WIDE-GUARD"); fight(bb, "SPLASH")
run(bb, 3000, until=lambda: g.current_state is bb and bb.phase == "MENU" and not bb.dialogue_box.visible)
check((_wg.current_hp, _mate.current_hp) == _hp0, f"Wide Guard: both foes' Surf hits nobody ({_hp0} -> {(_wg.current_hp, _mate.current_hp)})")
fight(bb, "SPLASH"); fight(bb, "SPLASH")
run(bb, 3000, until=lambda: g.current_state is bb and bb.phase == "MENU" and not bb.dialogue_box.visible)
check(_wg.current_hp < _hp0[0] or _mate.current_hp < _hp0[1], f"...and next turn it's gone: Surf hits ({(_wg.current_hp, _mate.current_hp)})")
_mb, _mate = mon(106, 50, ["MAT-BLOCK", "SPLASH"]), mon(143, 60, ["SPLASH"])
bb = fresh_double([66, 66], [40, 40], [_mb, _mate], moves="TACKLE")
_hp0 = (_mb.current_hp, _mate.current_hp)
fight(bb, "MAT-BLOCK"); fight(bb, "SPLASH")
run(bb, 3000, until=lambda: g.current_state is bb and bb.phase == "MENU" and not bb.dialogue_box.visible)
check((_mb.current_hp, _mate.current_hp) == _hp0, f"Mat Block on the first turn: both Tackles blocked ({(_mb.current_hp, _mate.current_hp)})")

print("16) Pursuit: switching out a Pokemon a foe's Pursuit is aimed at, it's hit first, at double power")
_ala, _steel, _bench = mon(65, 60, ["SPLASH"]), mon(208, 60, ["SPLASH"]), mon(143, 60, ["SPLASH"])
bb = fresh_double([198, 198], [15, 15], [_ala, _steel, _bench], moves="PURSUIT")
_hp_a = _ala.current_hp
LOG.clear()
bb.open_party_menu()
g.current_state.on_select(2)                      # (ALAKAZAM out, SNORLAX in)
fight(bb, "SPLASH")                               # (STEELIX splashes)
run(bb, 3000, until=lambda: g.current_state is bb and bb.phase == "MENU" and not bb.dialogue_box.visible)
_said = lines()
_go = next((i for i, l in enumerate(_said) if l == "Go! SNORLAX!"), None)
_hit = next((i for i, l in enumerate(_said) if "PURSUIT" in l.upper()), None)
check(_ala.current_hp < _hp_a and _hit is not None and (_go is None or _hit < _go) and bb.p_slots[0] is not _ala,
      f"ALAKAZAM is hit by Pursuit before it goes ({_hp_a} -> {_ala.current_hp}); then SNORLAX comes in ({[l for l in _said if 'Pursuit' in l or 'PURSUIT' in l or 'Go!' in l][:4]})")

print("13) the Rocket HQ (HeartGold / SoulSilver): you and Lance against Ariana and a Grunt")
story.enter_region("JOHTO")
_ari = next(t for t in g.loader.area_data["STORY_PROGRESSION"]["ROCKET_HQ"]["trainer_pool"] if t.get("victory_flag") == "rocket_hq_cleared")
b = _common._start_event_battle(g, "ROCKET_HQ", dict(_ari), "rocket_hq_cleared").next_state
check(isinstance(b, DoubleBattleState) and [p.id for p in b.partner_team] == [149] and [p.id for p in b.foe_teams[0]] == [24, 44, 198]
      and [p.id for p in b.foe_teams[1]] == [96, 88],
      f"Lance's Dragonite beside you; Ariana's Arbok, Gloom, Murkrow and the Grunt's Drowzee, Grimer ({b.partner_name}, {b.foe2_name})")

print(f"##### {fails} failures")
