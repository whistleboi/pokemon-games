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
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())   # (Kanto is walked: legacy menu clear, Step 5, 11-24)
story.enter_region("KANTO")

print("1) Saffron")
story.story_flags.update({"tower_ghost_defeated": True, "fuji_rescued": True}); story.story_flags.pop("silph_co_cleared", None)
city = walk_town(  # (Silph's door: open once Fuji is home, as the map's grunt and the travel option say)
    "SAFFRON_CITY", "KANTO_ROUTE_5")
check("SILPH_CITY" in walk_exits(city), "Saffron's map has Silph Co.'s door")
walk_out(city, "SILPH_CITY")
check(story.current_area_key == "SILPH_CITY", f"walk in: Silph Co. ({story.current_area_key})")

print("2) Game Corner grunts")
city = walk_town("CELADON_CITY", "KANTO_ROUTE_7"); g.states["city"] = city
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
story.inventory.update({"SUPER_ROD": 1})
seen = []
ps = walk_route("KANTO_ROUTE_6", "VERMILLION_CITY")
for _ in range(900):   # (not every cast bites: as many tries as the menu's 400 bites)
    g.change_state(ps); ps.mode = "MAP"
    st = walk_fish(ps)   # (cast from the bank, as a player would: the FISH key beside water)
    if hasattr(st, "opponent_pokemon"):
        seen.append((st.opponent_pokemon.id, st.opponent_pokemon.level))
bad = [s for s in seen if s[0] in (148, 149) and s[1] < 30 or s[0] in (119, 99, 91, 121, 130) and s[1] < 20 or s[1] < 15]
check(seen and not bad, f"{len(seen)} Super Rod bites, all Lv 15+ and no under-level evolved fish: {bad[:5]}")
# (Dratini: not in Route 6's water since its FireRed table (Poliwag, Psyduck, Slowpoke, Gyarados); the Safari Zone's, 11-24)
sz = walk_route("SAFARI_ZONE", "FUCHSIA_CITY")
drat = []
for _ in range(300):
    g.change_state(sz); sz.mode = "MAP"
    st = walk_fish(sz)
    if hasattr(st, "opponent_pokemon"):
        drat.append(st.opponent_pokemon.id)
    if 147 in drat:
        break
check(147 in drat, f"Dratini can still bite (the Safari Zone, {len(drat)} bites)")
story.inventory.pop("SUPER_ROD"); story.inventory.pop("OLD_ROD", None); story.inventory["GOOD_ROD"] = 1
ps = walk_route("KANTO_ROUTE_10", "KANTO_ROUTE_9")
check(ps._check_route_condition("can_fish", 0), "Good Rod counts as a rod")
st = walk_fish(ps)
check(hasattr(st, "opponent_pokemon") and st.opponent_pokemon.level >= 10, "Good Rod bite on Route 10")

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
story.story_flags.pop("fuji_rescued", None)
city = walk_town("LAVENDER_TOWN", "KANTO_ROUTE_10")
w = walk_meet(city, "Talk to Mr. Fuji")
check(not story.inventory.get("POKE_FLUTE") and (w is None or any("Tower" in l for l in w)),
      f"Fuji's not home till you rescue him from the tower's top (as in the games) ({w})")
story.story_flags["fuji_rescued"] = True
city = walk_town("LAVENDER_TOWN", "KANTO_ROUTE_10")
w = walk_meet(city, "Talk to Mr. Fuji")
check(story.inventory.get("POKE_FLUTE") == 1 and any("Marowak" in l for l in w or []), f"walk into his house: Fuji tells his story and gives the flute ({(w or [])[:1]})")

print("6) evolve after a gym win")
walk_town("PEWTER_CITY", "KANTO_ROUTE_2")
ch = mk(4); ch.level = 16; ch.evo_due = True; ch.current_hp = ch.get_max_hp(); story.player_team = [ch]
b = TrainerBattleState(g, [mk(74)], trainer_class="GYM_LEADER", trainer_name="Brock", area_name="PEWTER_CITY", battle_type="gym", badge_reward="BOULDER")
g.change_state(b); b.player_won = True
b.exit_battle()
st = g.current_state
check(isinstance(st, EvolutionState) and isinstance(st.return_state, ow.GymLobbyState), f"evolves right after the badge ({type(st).__name__})")
check("BOULDER" in story.badges.get("KANTO", []), "badge still awarded")
print("7) evolve after a town trainer battle")
story.current_area_key = "ETERNA_CITY"
ch = mk(4); ch.level = 16; ch.evo_due = True; story.player_team = [ch]
b = TrainerBattleState(g, [mk(396)], trainer_class="PKMN_TRAINER", trainer_name="Barry", area_name="ETERNA_CITY", battle_type="event")
g.change_state(b); b.player_won = True; b.exit_battle()
check(isinstance(g.current_state, EvolutionState) and isinstance(g.current_state.return_state, ow.CityState), type(g.current_state).__name__)
print("FAILURES:", fails)
