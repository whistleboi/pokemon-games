
# Orre's pilot (11-20, kanto_handoff/orre_check/PILOT.md): Colosseum's opening through leaving Phenac, and the Shadow
# Pokemon rules it needs (src/world/shadow.py, src/states/battle_shadow.py). Run: bash dev/checks/run_par.sh orre_pilot
from src.states.battle import TrainerBattleState
from src.world import shadow
from src.pokemon import catching

fails = []


def check(c, m):
    print(("ok   " if c else "FAIL ") + m)
    if not c:
        fails.append(m)


prog = g.loader.area_data["STORY_PROGRESSION"]
story.current_area_key = "PHENAC_CITY"
story.inventory = {"POKE_BALL": 5, shadow.SNAG_MACHINE: 1}
story.story_flags = {}
MAKUHITA = 9406


def team_of(ids, lv=30):
    t = [mk(i) for i in ids]
    for p in t:
        p.level = lv
        p.current_hp = p.get_max_hp()
    return t


def run_snag(b, frames=900):
    """Throw a ball now (as the Bag does) and play the snag through. The lines it showed."""
    story.selected_ball = "POKE_BALL"
    b.throw_from_bag()
    seen = []
    for _ in range(frames):
        if b.dialogue_box.visible:
            for line in b.dialogue_box.text_lines:
                if line not in seen:
                    seen.append(line)
            b.dialogue_box.is_finished = True
        if b.phase == "MESSAGE" and b.dialogue_box.callback:
            cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
            break
        b.update()
    return seen


print("1) The Shadow data from the discs")
sd = g.loader.area_data.get("SHADOW_DATA") or {}
check(len(sd) >= 130, f"{len(sd)} Shadow forms with disc data")
check(sd.get(str(MAKUHITA), {}).get("heart") == 3000 and sd[str(MAKUHITA)].get("catch_rate") == 255,
      f"Makuhita: Colosseum's gauge 3000, snag rate 255 ({sd.get(str(MAKUHITA))})")
check(catching.catch_rate(g, mk(MAKUHITA)) == 255, "the snag uses the disc's rate")

print("2) Snagging in a single battle")
story.player_team = team_of([196])
foe = team_of([355, MAKUHITA])   # Duskull, Shadow Makuhita
b = TrainerBattleState(g, foe, trainer_class="CIPHER_PEON", trainer_name="Trudly", victory_flag="t_single")
g.change_state(b)
b.phase = "MENU"
lines = run_snag(b)
check(any("blocked" in ln for ln in lines) and story.inventory["POKE_BALL"] == 5, f"a ball at an ordinary Pokemon is blocked, not lost: {lines[:2]}")
b.opponent_pokemon = foe[1]; b.current_opponent_idx = 1
real = catching.throw
catching.throw = lambda *a, **k: (True, 3, False)
lines = run_snag(b)
catching.throw = real
got = [p for p in story.player_team if p.id == MAKUHITA]
check(any("snagged" in ln for ln in lines) and got, f"Shadow Makuhita snagged into the party: {lines}")
check(got and got[0].shadow and got[0].moves[0] == shadow.SHADOW_RUSH and got[0].shadow["max"] == 3000,
      f"its gauge is full and it knows Shadow Rush ({got and got[0].moves})")
check(story.story_flags.get("snagged_shadow_makuhita"), "the pool's flag is set (snagged_shadow_makuhita)")
check(story.inventory["POKE_BALL"] == 4 and all(m.id != MAKUHITA for m in b.opponent_team), "the ball is used; it left Trudly's team")

print("3) Snagging in a double battle (Colosseum's battles are doubles)")
story.player_team = team_of([196, 197])
story.story_flags = {}
foe = team_of([355, MAKUHITA, 167])   # Duskull, Shadow Makuhita, Spinarak
b = TrainerBattleState(g, foe, trainer_class="CIPHER_PEON", trainer_name="Trudly", options={"double": True})
check(type(b).__name__ == "DoubleBattleState", "a double battle")
g.change_state(b)
b._begin_input()
catching.throw = lambda *a, **k: (True, 3, False)
lines = run_snag(b)
catching.throw = real
check(any("snagged" in ln for ln in lines) and any(p.id == MAKUHITA for p in story.player_team), f"snagged in a double: {lines}")
check(all(m is None or m.id != MAKUHITA for m in b.o_slots), "it left the field")

print("4) The Heart Gauge, Hyper Mode, CALL, purifying")
mon = next(p for p in story.player_team if p.id == MAKUHITA)
check(shadow.bars(mon) == 5 and len(mon.moves) == 1, "five bars, its own moves hidden")
for _ in range(10):
    shadow.after_battle(g, story.player_team, [mon])
check(shadow.bars(mon) < 5 and len(mon.moves) > 1, f"battles open it and its moves come back ({shadow.bars(mon)} bars, {mon.moves})")
mon.shadow["hyper"] = True
lines = shadow.call(g, mon)
check(not mon.shadow["hyper"] and any("senses" in ln for ln in lines), "CALL brings it out of Hyper Mode")
check(story.purify_shadow() == [], "not purified while its heart is closed")
shadow.open_heart(g, mon, 1.0)
check(shadow.is_open(mon) and story.purify_shadow() == ["MAKUHITA"], "purified once open")
p = next(p for p in story.player_team if p.id == 296)
check(shadow.SHADOW_RUSH not in p.moves and not getattr(p, "shadow", None), f"its own moves back ({p.moves})")
rec = story._pokemon_record(mk(MAKUHITA))
m2 = shadow.make_shadow(g, mk(MAKUHITA))
r2 = story._pokemon_record(m2)
check(rec.get("shadow") is None and r2["shadow"]["max"] == 3000, "the gauge is saved with the Pokemon")

print("4a) A Shadow Pokemon evolves and stays Shadow, its Heart Gauge kept (Jordan's rule, 11-20)")
from src.states.systems.evolution_scene import EvolutionState
from src.pokemon import evolution as _evo
bay = shadow.make_shadow(g, mk(9348))
bay.level = 40
bay.evo_due = True   # (it just levelled up)
shadow.open_heart(g, bay, 0.3)
before = dict(bay.shadow)
story.player_team = [bay]
check("MEGANIUM_SHADOW" in _evo.ready_evolutions(g, bay), f"Shadow Bayleef can evolve as a Shadow ({_evo.ready_evolutions(g, bay)})")
es = EvolutionState(g, bay, 154, 0, next_form="shadow")
es.evolve_yes()
for _ in range(400):
    es.update()
    if es.evolved_pokemon_obj is not None:
        break
new = es.evolved_pokemon_obj
check(new is not None and shadow.is_shadow(g, new) and getattr(new, "shadow", None) == before,
      f"it became Shadow Meganium with the same gauge ({new and new.name}, id {new and new.id}, form {new and new.form}, {getattr(new, 'shadow', None)} vs {before})")
shadow.open_heart(g, new, 1.0)
story.player_team = [new]
check(story.is_shadow(new) and story.purify_shadow() == ["MEGANIUM"], "an evolved Shadow is purified at the Relic Stone once its heart opens")

print("4b) Every move the story's trainers use is one the game knows (the disc spells some the old way: VICEGRIP)")
import json as _json
_known = _json.load(open("assets/moves.json", encoding="utf-8"))
_tm = _json.load(open("assets/town_maps.json", encoding="utf-8"))
_bad = set()


def _walk(o):
    if isinstance(o, dict):
        for mv in sum((o.get("team_moves") or []), []) if isinstance(o.get("team_moves"), list) else []:
            if mv not in _known:
                _bad.add(mv)
        for v in o.values():
            _walk(v)
    elif isinstance(o, list):
        for v in o:
            _walk(v)


for _k in ("OUTSKIRT_STAND", "PHENAC_CITY"):
    _walk(_tm[_k])
check(not _bad, f"all known ({sorted(_bad)})")

print("5) The pilot played: a new Orre game from the partners to leaving Phenac")
from src.states.overworld import CityState as _CS
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.menus import StarterSelectionState
from src.world import rui as _rui
g.dungeon_routes = True
g.walk_towns = True
said = []


def frames(n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def _note(st):
    box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
    if box is not None and getattr(box, "visible", True):
        for line in getattr(box, "text_lines", []) or []:
            if not said or said[-1] != line:
                said.append(line)


def _fight(b, n=8000):
    """Win the battle with right answers; a Shadow Pokemon is snagged as soon as it's out (the ball always holds)."""
    tried = set()
    for _k in range(n):
        if g.current_state is not b:
            return
        foe = b._snag_target() if hasattr(b, "_snag_target") else None
        if b.phase == "SWITCH_PROMPT" and b.btn_no.visible and b.btn_no.callback:
            b.btn_no.callback()
        elif b.phase == "MENU" and not b.dialogue_box.visible and foe is not None and id(foe) not in tried \
                and story.inventory.get(catching.POKE, 0) > 0:
            tried.add(id(foe))
            story.selected_ball = catching.POKE
            real = catching.throw
            catching.throw = lambda *a, **k: (True, 3, False)
            b.throw_from_bag()
            catching.throw = real
        elif b.phase == "TARGET_SELECT" and getattr(b, "_target_buttons", None):
            b._target_buttons[0].callback()   # (a double battle: the first foe)
        elif b.phase in ("MENU", "BATTLE") and not b.dialogue_box.visible and b.math_ui and b.math_ui.visible:
            b.math_ui.on_click(b.options.index(b.correct_ans))
        elif b.phase == "MENU" and not b.dialogue_box.visible:
            b.open_move_menu()
            b.choose_move(b.move_buttons[0].text.replace(" ", "-"))
        elif b.dialogue_box.visible:
            _note(b)
            b.dialogue_box.is_finished = True
            if b.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
                b.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            elif b.dialogue_box.callback:
                cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
        b.feedback_timer = 0
        b.update(); b.draw()


def play(n=3000):
    quiet = 0
    for _ in range(n):
        st = g.current_state
        if hasattr(st, "math_ui") and hasattr(st, "phase"):
            _fight(st); quiet = 0
        elif getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))]); quiet = 0
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st); st.dialogue_box.advance(); quiet = 0
        elif getattr(getattr(st, "scenes", None), "playing", None):
            quiet = 0   # (a scene's cast still walking)
        else:
            quiet += 1
            if quiet > 40:
                return
        st.update(); st.draw()


def town(area, came):
    g.walk_town_pos = g.walk_town_exit = g.walk_town_room = None
    story.current_area_key, story.last_area_key = area, came
    t = _CS(g); g.change_state(t); frames(2); play()
    return g.current_state


def meet(st, text):
    said.clear()
    st = g.current_state if isinstance(g.current_state, _WTS) else st
    spot = next((s for s, o in st._people().items() if o.get("text") == text), None)
    if spot is None:
        for room in (st.town_map.get("rooms") or {}):
            st._go(room, ""); frames(2)
            spot = next((s for s, o in st._people().items() if o.get("text") == text), None)
            if spot is not None:
                break
    if spot is None:
        return None
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        b = (spot[0] + dx, spot[1] + dy)
        if st._open(b) and b not in st.exits:
            st.player = st.anim_from = b; st.anim = 0; st.walk_goal = None
            st.step(-dx, -dy)
            break
    else:
        return None
    play()
    return list(said)


story.story_flags = {}
F = story.story_flags
story.inventory = {}
story.player_team = []
story.current_area_key = "OUTSKIRT_STAND"
ss = StarterSelectionState(g, starter_ids=[196, 197], region="ORRE")
g.change_state(ss)
ss.load_starters(); ss.selected_idx = 0; ss.complete_selection()
ss.dialogue_box.callback()
frames(3)
lv = {p.id: p.level for p in story.player_team}
check(lv == {196: 25, 197: 26}, f"Espeon Lv 25 and Umbreon Lv 26, as Colosseum gives them ({lv})")
check(story.inventory.get("SNAG_MACHINE") and F.get("orre_opening_seen"), "the Snag Machine from the opening")
check(story.inventory.get(catching.POKE, 0) == 0, "no Poke Balls yet (Orre's Marts have none)")
mv = {p.id: p.moves for p in story.player_team}
check(mv.get(196) == ["CONFUSION", "RETURN", "REFLECT", "HELPING-HAND"] and mv.get(197, [None])[0] == "BITE", f"their moves from the disc ({mv})")
for p in story.player_team:   # (the story's flow is under test here, not how hard its battles are)
    p.level = 45
    p.heal_full()

t = town("OUTSKIRT_STAND", "ORRE_DESERT")
check(F.get("orre_os_shady"), "arriving: the two men leave the diner with the sack")
check(not any(o.get("text") == "CHALLENGE WILLIE" for o in t._people().values()), "Willie isn't outside any more")
said_w = meet(t, "Rider Willie") or []
check(F.get("orre_beat_willie"), f"Rider Willie beaten in the diner ({said_w[:2]})")
check(any("TV" in ln for ln in said_w), "the TV news on the hideout plays first")

t = town("PHENAC_CITY", "OUTSKIRT_STAND")
check(F.get("orre_phenac_folly"), "Phenac: Folly walks up and battles at once")
meet(t, "A big sack")
check(F.get("orre_rui_joined"), "Rui comes out of the sack and joins you")
check(_rui.active(story) and shadow.aura_visible(g), "Rui walks with you; Shadow Pokemon's auras show now")
t = town("PHENAC_CITY", "OUTSKIRT_STAND")
meet(t, "Mayor Es Cade")
check(F.get("orre_met_mayor"), "the Mayor heard about the Shadow Pokemon")
t = town("PHENAC_CITY", "OUTSKIRT_STAND")
meet(t, "Team Snagem Wakin")
check(F.get("orre_wakin"), "Team Snagem's Wakin beaten")
t = town("OUTSKIRT_STAND", "PHENAC_CITY")
meet(t, "Diner")
check(F.get("orre_got_balls") and story.inventory.get(catching.POKE) == 5, f"the bartender's 5 Poke Balls ({story.inventory.get(catching.POKE)})")
t = town("PHENAC_CITY", "OUTSKIRT_STAND")
check(F.get("orre_raid_told"), "back in Phenac: trouble at the Mayor's")
for who, flag in (("Miror B.", "orre_raid_mirorb"), ("Miror B. Peon Folly", "orre_raid_folly"), ("Miror B. Peon Trudly", "orre_raid_trudly")):
    meet(g.current_state, who)
    check(F.get(flag), f"{who}: done ({flag})")
mine = [p for p in list(story.player_team) + list(story.pc_pokemon or []) if p]
check(F.get("snagged_shadow_makuhita") and any(p.id == MAKUHITA for p in mine), "Trudly's Shadow Makuhita snagged: the first Shadow Pokemon")
t = town("PHENAC_CITY", "OUTSKIRT_STAND")
guards = [o.get("text") for o in t._people().values() if "Mystery Troop" in str(o.get("text"))]
check(len(guards) == 3, f"three guards at Phenac's ways out ({guards})")
meet(t, "Mystery Troop Verde")
check(F.get("got_snag_machine") and F.get("snagged_shadow_bayleef"), "a guard beaten, his Shadow Bayleef snagged; Phenac opens")
t = town("PHENAC_CITY", "OUTSKIRT_STAND")
check(not [o for o in t._people().values() if "Mystery Troop" in str(o.get("text"))], "the other two guards are gone")

t = town("PHENAC_CITY", "OUTSKIRT_STAND")
sp = story.inventory.get("SUPER_POTION", 0)
meet(t, "Super Potion ball")
check(story.inventory.get("SUPER_POTION", 0) == sp + 3 and F.get("orre_phenac_superpotion"), "3 Super Potions by the bike, once")
t = town("PHENAC_CITY", "OUTSKIRT_STAND")
said_m = meet(t, "Girl") or []
check(any("nobody sells them" in ln for ln in said_m), f"the Mart: Orre's shops sell no Poke Balls ({said_m[:1]})")

print("6) An older save already past Phenac sees none of it again")
story.story_flags = {"got_snag_machine": True, "orre_beat_willie": True}
t = town("PHENAC_CITY", "OUTSKIRT_STAND")
left = [o.get("text") for o in t._people().values() if o.get("text") in ("Shady Guy Folly", "A big sack", "Team Snagem Wakin", "Mystery Troop Verde")]
check(not left and not story.story_flags.get("orre_phenac_folly"), f"no Folly fight, no sack, no guards ({left})")
check(_rui.active(story), "Rui walks with them too")

print("##### orre_pilot:", len(fails), "failures")
for f in fails:
    print("  -", f)
