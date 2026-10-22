from src.states import overworld as ow
from src.states.systems import GameCornerState, EvolutionState
from src.states.battle import TrainerBattleState, TrainerIntroState
from src.world import levels
fails = 0
def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m); fails += 0 if c else 1
prog = g.loader.area_data["STORY_PROGRESSION"]
g.data.save = lambda *a, **k: None

print("1) Saffron")
story.current_area_key = "SAFFRON_CITY"
story.story_flags.update({"tower_ghost_defeated": True}); story.story_flags.pop("silph_co_cleared", None)
city = ow.CityState(g); g.change_state(city)
opt = next(o for o in prog["SAFFRON_CITY"]["explore_options"] if o["text"] == "Confront Team Rocket")
cb = city._get_callback_for_option(opt)
check(cb is not None, "button has an action")
cb()
check(isinstance(g.current_state, ow.AreaTransitionState) and g.current_state.next_area_key == "SILPH_CITY", "it heads into Silph Co.")

print("2) Game Corner grunts")
story.current_area_key = "CELADON_CITY"
city = ow.CityState(g); g.states["city"] = city
spreads = []
for prog_i in range(4):
    gc = GameCornerState(g, city); gc.rocket_progress = prog_i
    gc.next_rocket_battle()
    b = g.current_state.next_state if isinstance(g.current_state, TrainerIntroState) else g.current_state
    lv = [p.level for p in b.opponent_team]
    spreads.append(lv)
check(all(max(l) - min(l) <= 3 for l in spreads), f"levels fit together: {spreads}")
check(spreads[-1][-1] > spreads[0][-1], "later grunts are tougher")

print("3) fishing")
story.current_area_key = "VERMILLION_CITY" if "VERMILLION_CITY" in prog else "KANTO_ROUTE_6"
story.current_area_key = "KANTO_ROUTE_6"
story.inventory.update({"SUPER_ROD": 1})
seen = []
for _ in range(400):
    ps = ow.PlayState(g); g.change_state(ps)
    ps.action_fish()
    st = g.current_state
    if hasattr(st, "opponent_pokemon"):
        seen.append((st.opponent_pokemon.id, st.opponent_pokemon.level))
bad = [s for s in seen if s[0] in (148, 149) and s[1] < 30 or s[0] in (119, 99, 91, 121, 130) and s[1] < 20 or s[1] < 15]
check(seen and not bad, f"{len(seen)} Super Rod bites, all Lv 15+ and no under-level evolved fish: {bad[:5]}")
check(any(s[0] == 147 for s in seen), "Dratini can still bite")
story.inventory.pop("SUPER_ROD"); story.inventory.pop("OLD_ROD", None); story.inventory["GOOD_ROD"] = 1
story.current_area_key = "KANTO_ROUTE_10"
ps = ow.PlayState(g); g.change_state(ps)
check(ps._check_route_condition("can_fish", 0), "Good Rod counts as a rod")
ps.action_fish()
check(hasattr(g.current_state, "opponent_pokemon") and g.current_state.opponent_pokemon.level >= 10, "Good Rod bite on Route 10")

print("4) Erika / Lorelei")
er = prog["CELADON_CITY"]["gym"]["leader"]["team"]
check(er[-1] == 45 and 43 not in er, f"Erika: {er}")
names = [t.get("name") for t in prog["INDIGO_PLATEAU"]["gym"]["trainers"]]
check("Lorelei" in names, f"E4: {names}")

print("5) Mr. Fuji")
story.inventory.pop("POKE_FLUTE", None)
story.story_flags["tower_ghost_defeated"] = True
story.sync_key_items() if hasattr(story, "sync_key_items") else None
import inspect
syncs = [n for n, f in inspect.getmembers(story, inspect.ismethod) if "sync" in n.lower()]
for n in syncs:
    try: getattr(story, n)()
    except TypeError: pass
check(story.inventory.get("POKE_FLUTE", 0) == 0, f"no flute before Fuji (ran {syncs})")
story.current_area_key = "LAVENDER_TOWN"
city = ow.CityState(g); g.change_state(city); city.visit_mr_fuji()
check(story.inventory.get("POKE_FLUTE") == 1 and any("Marowak" in l for l in city.npc_dialogue.text_lines), "Fuji tells his story and gives the flute")

print("6) evolve after a gym win")
story.current_area_key = "PEWTER_CITY"
ch = mk(4); ch.level = 16; ch.current_hp = ch.get_max_hp(); story.player_team = [ch]
b = TrainerBattleState(g, [mk(74)], trainer_class="GYM_LEADER", trainer_name="Brock", area_name="PEWTER_CITY", battle_type="gym", badge_reward="BOULDER")
g.change_state(b); b.player_won = True
b.exit_battle()
st = g.current_state
check(isinstance(st, EvolutionState) and isinstance(st.return_state, ow.GymLobbyState), f"evolves right after the badge ({type(st).__name__})")
check("BOULDER" in story.badges.get("KANTO", []), "badge still awarded")
print("7) evolve after a town trainer battle")
story.current_area_key = "ETERNA_CITY"
ch = mk(4); ch.level = 16; story.player_team = [ch]
b = TrainerBattleState(g, [mk(396)], trainer_class="PKMN_TRAINER", trainer_name="Barry", area_name="ETERNA_CITY", battle_type="event")
g.change_state(b); b.player_won = True; b.exit_battle()
check(isinstance(g.current_state, EvolutionState) and isinstance(g.current_state.return_state, ow.CityState), type(g.current_state).__name__)
print("FAILURES:", fails)
