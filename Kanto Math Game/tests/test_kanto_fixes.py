"""Regression tests for the kanto-fixes branch. Plain asserts; run directly."""
import json, random
import _env
from _env import make_game, mk

G = make_game()
AREA = G.loader.area_data
TESTS = []
def test(f): TESTS.append(f); return f

@test
def ned_awards_super_rod():
    raw = open("assets/pokemon_area_data.json").read()
    assert '"{rewards"' not in raw
    def walk(o):
        if isinstance(o, dict):
            if o.get("name") == "Ned" and "team" in o: yield o
            for v in o.values(): yield from walk(v)
        elif isinstance(o, list):
            for v in o: yield from walk(v)
    ned = next(walk(json.loads(raw)))
    assert ned["rewards"].get("SUPER_ROD") == 1

def battle(team, foes):
    from src.states.battle import TrainerBattleState
    G.story_manager.player_team = team
    b = TrainerBattleState(G, foes, trainer_class="HIKER", trainer_name="T", battle_type="event")
    G.change_state(b); return b

@test
def immunities_zero():
    from src.pokemon.mechanics import TypeAdvantage
    c = TypeAdvantage(AREA["TYPE_CHART"])
    for a, d in [("NORMAL","GHOST"),("ELECTRIC","GROUND"),("FIGHTING","GHOST"),("POISON","STEEL"),
                 ("GROUND","FLYING"),("PSYCHIC","DARK"),("GHOST","NORMAL"),("DRAGON","FAIRY")]:
        assert c.get_multiplier(a, [d]) == 0, (a, d)
    b = battle([mk(G, 25, 30)], [mk(G, 74, 30)])
    dmg, lines, _ = b._use_move(b.player_pokemon, b.opponent_pokemon, "THUNDER-SHOCK", "A", "D", 99, 99)
    assert dmg == 0 and "doesn't affect" in lines[-1], lines

@test
def struggle_fallback():
    m = mk(G, 129, 10); m.moves = ["TACKLE"]
    b = battle([m], [mk(G, 92, 10)])
    assert b._battle_moves(m) == ["STRUGGLE"]
    dmg, lines, _ = b._use_move(m, b.opponent_pokemon, "STRUGGLE", "A", "D", 99, 99)
    assert dmg > 0 and b.player_hp < b.player_max_hp

@test
def status_cured_on_blackout_and_full_heal():
    m = mk(G, 25, 20); m.status = "poison"
    b = battle([m], [mk(G, 74, 20)])
    import src.states.battle as B
    try: b.perform_battle_black_out()
    except Exception: pass  # state change side effects; we only check the cure
    assert m.status is None and m.current_hp == m.get_max_hp()
    m.status = "burn"; G.story_manager.player_team = [m]; G.story_manager.inventory["FULL_HEAL"] = 1
    from src.states.systems import BagState
    bag = BagState(G, None)
    bag.on_pokemon_select_full_heal(0)
    assert m.status is None and "FULL_HEAL" not in G.story_manager.inventory
    from src.states.systems import PokeMartState
    G.story_manager.current_area_key = "VIRIDIAN_CITY"
    assert "FULL_HEAL" in PokeMartState(G, None)._shop_items()

@test
def koffing_weezing_wild():
    for k in ("POWER_PLANT", "KANTO_ROUTE_17"):
        pct = AREA[k + "_PERCENTAGES"]
        assert "109" in pct and "110" not in pct and sum(pct.values()) == 100, k
        assert 109 in AREA[k] and 110 not in AREA[k]
    import json as _j
    raw = _j.load(open("assets/pokemon_area_data.json"))
    assert not [k for k, v in raw.items() if k.endswith("PERCENTAGES") and isinstance(v, dict) and "110" in v]
    from src.pokemon import evolution as E
    assert 110 in [t for _, t, _ in E.evolution_options(G, mk(G, 109, 40))]  # Weezing only by evolving
    assert mk(G, 109, 25).types and mk(G, 110, 26).types

@test
def cross_gen_evolution_gating():
    from src.pokemon import evolution as E
    s = G.story_manager; saved = (s.starting_region, set(s.visited_region_set), dict(s.story_flags))
    tids = lambda pid: [t for _, t, _ in E.evolution_options(G, mk(G, pid, 50))]
    try:
        s.starting_region, s.visited_region_set, s.story_flags = "KANTO", {"KANTO"}, {}
        assert tids(137) == [] and tids(113) == [] and tids(42) == [] and 134 in tids(133)
        s.enter_region("JOHTO")
        assert 233 in tids(137) and 242 in tids(113) and 474 not in tids(233)
        s.starting_region, s.visited_region_set, s.story_flags = "SINNOH", {"SINNOH"}, {}
        assert 233 in tids(137) and 474 in tids(233) and 466 in tids(125) and 700 not in tids(133)
        s.visited_region_set = {"UNOVA"}
        data = s.serialize() if hasattr(s, "serialize") else None
        assert data is None or "SINNOH" in data["visited_regions"] and "UNOVA" in data["visited_regions"]
    finally:
        s.starting_region, s.visited_region_set, s.story_flags = saved

@test
def sleep_never_zero_turns():
    import collections
    b = battle([mk(G, 25, 20)], [mk(G, 19, 20)]); c = collections.Counter()
    for _ in range(3000):
        m = mk(G, 19, 10); b._inflict("sleep", m, "x"); t = 0
        while b._status_stops(m, "x")[0]: t += 1
        c[t] += 1
    assert c[0] == 0 and set(c) == {1, 2, 3}, c

@test
def status_move_immunities_and_toxic():
    from src.pokemon import moves as M
    b = battle([mk(G, 25, 20)], [mk(G, 74, 20)])
    tw = M.info(G, "THUNDER-WAVE"); sp = M.info(G, "SLEEP-POWDER"); tx = M.info(G, "TOXIC")
    assert not b._status_move_works(tw, mk(G, 74, 20))          # Geodude (Ground)
    assert b._status_move_works(tw, mk(G, 19, 20))
    assert not b._status_move_works(sp, mk(G, 1, 20))           # Bulbasaur (Grass)
    assert b._status_move_works(sp, mk(G, 19, 20))
    foe = b.opponent_pokemon; foe.types = ["NORMAL"]; foe.status = None
    _, lines, _ = b._use_move(b.player_pokemon, foe, "TOXIC", "A", "D", 99, 99)
    if foe.status:  # Toxic can miss
        assert foe.status == "toxic" and "badly" in lines[-1]
        hp0 = b.opponent_hp; b._status_chip(); d1 = hp0 - b.opponent_hp
        hp1 = b.opponent_hp; b._status_chip(); d2 = hp1 - b.opponent_hp
        assert d2 > d1 > 0, (d1, d2)

@test
def multihit_drain_recoil_highcrit():
    import collections
    from src.pokemon import balance
    b = battle([mk(G, 32, 30)], [mk(G, 143, 60)])  # Nidoran vs high-HP Snorlax
    att, de = b.player_pokemon, b.opponent_pokemon
    c = collections.Counter(b._hit_count({"min_hits": 2, "max_hits": 5}) for _ in range(4000))
    assert set(c) == {2, 3, 4, 5} and c[2] > c[5] * 1.8
    _, lines, _ = b._use_move(att, de, "DOUBLE-KICK", "A", "D", 999, 999)
    assert "missed" in lines[-1] or any("Hit 2 times" in l for l in lines), lines
    b.player_hp = att.current_hp = att.get_max_hp() // 2
    hp = b.player_hp
    _, lines, _ = b._use_move(att, de, "GIGA-DRAIN", "A", "D", 999, 999)
    assert "missed" in lines[-1] or b.player_hp > hp
    hp = b.player_hp
    _, lines, _ = b._use_move(att, de, "TAKE-DOWN", "A", "D", 999, 999)
    assert "missed" in lines[-1] or b.player_hp < hp
    n = 60000
    crit = sum(balance.damage(50, 70, 100, 100, crit_stage=1)[1] for _ in range(n)) / n
    assert abs(crit - 1 / 8) < 0.01, crit

@test
def two_turn_recharge_fixed_flinch():
    from src.pokemon import moves as M
    b = battle([mk(G, 1, 30)], [mk(G, 143, 60)])
    att, de = b.player_pokemon, b.opponent_pokemon
    b.weather = None
    d1, l1, _ = b._use_move(att, de, "SOLAR-BEAM", "A", "D", 999, 999)
    assert d1 == 0 and "sunlight" in l1[-1] and b._forced_move(att) == "SOLAR-BEAM"
    d2, l2, _ = b._use_move(att, de, "SOLAR-BEAM", "A", "D", 999, 999)
    assert d2 > 0 and b._forced_move(att) is None
    random.seed(3)
    while True:
        dmg, _, _ = b._use_move(att, de, "HYPER-BEAM", "A", "D", 999, 999)
        if dmg: break
    stopped, lines = b._status_stops(att, "A")
    assert stopped and "recharge" in lines[0] and not b._status_stops(att, "A")[0]
    assert b._use_move(att, de, "SEISMIC-TOSS", "A", "D", 999, 999)[0] == 30
    assert b._use_move(att, de, "DRAGON-RAGE", "A", "D", 999, 999)[0] == 40
    assert b._use_move(att, de, "SUPER-FANG", "A", "D", 999, 100)[0] in (0, 50)
    assert b._use_move(att, mk(G, 92, 30), "SEISMIC-TOSS", "A", "D", 99, 99)[0] == 0  # Ghost
    assert M.usable(M.info(G, "SONIC-BOOM")) and M.usable(M.info(G, "NIGHT-SHADE"))
    b._acts_second = id(de); b._flinched = set(); n = 0
    for _ in range(200):
        b._flinched.clear(); b._use_move(att, de, "HEADBUTT", "A", "D", 9999, 9999); n += id(de) in b._flinched
    assert 30 < n < 90, n
    b._flinched = {id(de)}; assert b._status_stops(de, "D")[0] and not b._status_stops(de, "D")[0]

@test
def kanto_dex_is_1_to_151():
    from src.states.systems import _dex_ids
    s = G.story_manager; saved = (s.starting_region, dict(s.story_flags))
    try:
        s.starting_region, s.story_flags = "KANTO", {"unlocked_kanto_badges": True}
        ids = _dex_ids(s, {}, [169, 25, 2001])
        assert ids == list(range(1, 152)), (len(ids), ids[150:])
        s.starting_region, s.story_flags = "JOHTO", {"unlocked_johto_badges": True}
        j = _dex_ids(s, {}, [])
        assert j[:100] == list(range(152, 252)) and 461 in j  # Johto keeps its dex_extra
    finally:
        s.starting_region, s.story_flags = saved

@test
def indigo_path_route23_victory_road():
    SP = AREA["STORY_PROGRESSION"]
    ex = lambda a: {o["target"]: o.get("condition") for o in SP[a]["route_menu"] if o.get("action") == "EXIT"}
    assert "KANTO_ROUTE_23" in ex("KANTO_ROUTE_22") and "VICTORY_ROAD" in ex("KANTO_ROUTE_23")
    assert "has_8_kanto_badges" in ex("VICTORY_ROAD")["INDIGO_PLATEAU"]

@test
def league_flags_only_on_win():
    from src.states.battle import TrainerBattleState
    G.story_manager.player_team = [mk(G, 6, 60)]; G.story_manager.current_area_key = "INDIGO_PLATEAU"
    G.story_manager.story_flags.pop("beat_elite_four", None)
    b = TrainerBattleState(G, [mk(G, 149, 60)], trainer_class="ELITE_FOUR", trainer_name="Lance",
                           battle_type="gym", is_boss_battle=True, area_name="INDIGO_PLATEAU",
                           victory_flag="beat_elite_four")
    G.change_state(b); b.player_won = False
    b.exit_battle(lost=True)
    assert not G.story_manager.story_flags.get("beat_elite_four")
    src = open("src/states/overworld.py").read()
    assert 'victory_flag=None if self.area_key == "INDIGO_PLATEAU"' not in src

@test
def fossil_revival_runs_once():
    from src.states.systems import FossilRevivalState
    st = G.story_manager; st.player_team = [mk(G, 25, 20)]; st.inventory["OLD_AMBER"] = 1
    prev = type("P", (), {"show_message": lambda self, m: None, "start": lambda self: None, "enter": lambda self: None})()
    saved_save = G.data.save; G.data.save = lambda: None
    try:
        f = FossilRevivalState(G, "OLD_AMBER", 142, prev)
        for _ in range(600):
            if G.current_state is prev: break
            f.update()
    finally:
        G.data.save = saved_save
    assert sum(p.id == 142 for p in st.player_team) == 1 and "OLD_AMBER" not in st.inventory

@test
def visit_bill_with_empty_pc_slots():
    from src.states.overworld import CityState
    st = G.story_manager; st.current_area_key = "CERULEAN_CITY"
    st.player_team = [mk(G, 25, 20)] * 6; st.pc_pokemon = [None] * 300; st.pc_pokemon[5] = mk(G, 143, 30)
    saved_save = G.data.save; G.data.save = lambda: None
    try:
        c = CityState(G); c.visit_bill()   # crashed: AttributeError 'NoneType' has no attribute 'id'
    finally:
        G.data.save = saved_save
    assert len(st.pc_pokemon) == 300

@test
def guaranteed_old_rod_and_route10_fish():
    from src.states.overworld import CityState
    st = G.story_manager; st.current_area_key = "VERMILLION_CITY"; st.inventory.pop("OLD_ROD", None)
    st.story_flags.pop("got_old_rod_guru", None)
    c = CityState(G); c.visit_fishing_guru()
    assert st.inventory.get("OLD_ROD") == 1 and st.story_flags["got_old_rod_guru"]
    acts = [o.get("action") for o in AREA["STORY_PROGRESSION"]["KANTO_ROUTE_10"]["route_menu"]]
    assert "FISH" in acts

@test
def early_area_gates():
    from src.states.overworld import CityState, PlayState
    st = G.story_manager; st.story_flags = {}; st.inventory = {}
    st.current_area_key = "CELADON_CITY"; c = CityState(G)
    opt = [o for o in AREA["STORY_PROGRESSION"]["CELADON_CITY"]["travel_options"] if o["target_area"] == "KANTO_ROUTE_16"][0]
    assert not c._check_menu_condition(opt["condition"])
    st.story_flags["KANTO_ROUTE_11_boss_defeated"] = True
    assert c._check_menu_condition(opt["condition"])
    st.current_area_key = "KANTO_ROUTE_10"; p = PlayState(G); p.rounds_completed = 99
    pp = [o for o in AREA["STORY_PROGRESSION"]["KANTO_ROUTE_10"]["route_menu"] if o.get("target") == "POWER_PLANT"][0]
    assert not p._check_route_condition(pp["condition"], False, pp)
    st.inventory["SURF_BOARD"] = 1
    assert p._check_route_condition(pp["condition"], False, pp)

@test
def kanto_mart_stock():
    from src.states.systems import PokeMartState
    st = G.story_manager
    def items(area):
        st.current_area_key = area; return PokeMartState(G, None)._shop_items()
    v = items("VIRIDIAN_CITY")
    assert "RARE_CANDY" not in v and "REVIVE" not in v and "POTION" in v and "FULL_HEAL" in v
    c = items("CELADON_CITY")
    assert {"POTION", "POKE_BALLS", "FULL_HEAL", "REVIVE"} <= set(c) and "FIRE_STONE" in c
    assert "REVIVE" in items("LAVENDER_TOWN") and "RARE_CANDY" in items("INDIGO_PLATEAU")
    j = items("GOLDENROD_CITY"); assert "RARE_CANDY" in j  # other regions unchanged

@test
def late_area_levels():
    from src.world import levels
    lv = lambda a: levels.area_level(G, a)
    assert lv("VICTORY_ROAD") >= 42 and lv("KANTO_ROUTE_23") >= 40 and lv("CERULEAN_CAVE") >= 55
    assert 34 <= lv("SEAFOAM_ISLANDS") <= 43 and lv("POWER_PLANT") >= 30

def _lobby(area, progress):
    from src.states.overworld import GymLobbyState
    st = G.story_manager; st.current_area_key = area; st.player_team = [mk(G, 6, 50)]
    st.story_flags[f"gym_progress_{area}"] = progress
    G.transitioning = False
    lb = GymLobbyState(G, None); G.change_state(lb); return lb

def _solve(pz, wrong_first=False):
    if wrong_first:
        pz.answer([i for i, o in enumerate(pz.options) if not o[1]][0])
    while not pz.finished:
        pz.answer([i for i, o in enumerate(pz.options) if o[1]][0])
    for _ in range(100):
        pz.update()

@test
def gym_puzzles_math():
    from src.states.gym_puzzles import GymPuzzleState, make_step
    st = G.story_manager
    for area, kind in (("VERMILLION_CITY", "surge"), ("FUCHSIA_CITY", "koga"), ("SAFFRON_CITY", "sabrina")):
        st.story_flags.pop(f"gym_puzzle_{area}", None)
        n = len(AREA["STORY_PROGRESSION"][area]["gym"].get("trainers", []))
        lb = _lobby(area, n); lb.challenge_gym()
        pz = G.current_state
        assert isinstance(pz, GymPuzzleState) and pz.kind == kind, (area, type(pz))
        pz.draw()
        _solve(pz, wrong_first=True)
        assert st.story_flags[f"gym_puzzle_{area}"] and type(G.current_state).__name__ == "GymLobbyState"
        G.current_state.challenge_gym()
        assert type(G.current_state).__name__ == "TrainerIntroState", type(G.current_state)
    for _ in range(200):  # every step has exactly one right answer, and it is right
        for kind in ("surge", "koga", "sabrina", "quiz"):
            p, pic, opts = make_step(kind, 0)
            assert sum(o[1] for o in opts) == 1
    # Blaine: right answer skips the trainer, wrong answer starts the battle
    for k in [k for k in st.story_flags if k.startswith("gym_quiz_")]: st.story_flags.pop(k)
    lb = _lobby("CINNABAR_ISLAND", 0); lb.challenge_gym(); _solve(G.current_state)
    assert st.story_flags["gym_progress_CINNABAR_ISLAND"] == 1
    lb = G.current_state; lb.challenge_gym(); qz = G.current_state
    qz.answer([i for i, o in enumerate(qz.options) if not o[1]][0])
    for _ in range(100): qz.update()
    assert type(G.current_state).__name__ == "TrainerIntroState"

@test
def semi_invulnerable_fly_dig_dive():
    b = battle([mk(G, 18, 40)], [mk(G, 51, 40)])   # Pidgeot vs Dugtrio
    me, foe = b.player_pokemon, b.opponent_pokemon
    b.turn_count = 5; b._semi = {}; b._charging = {}
    b._use_move(me, foe, "FLY", "A", "D", 999, 999)          # Pidgeot flies up
    _, lines, _ = b._use_move(foe, me, "SLASH", "D", "A", 999, 999)
    assert "avoided" in lines[-1]
    random.seed(1); d_gust = [b._use_move(foe, me, "GUST", "D", "A", 9999, 9999)[0] for _ in range(40)]
    b._semi = {}; random.seed(1); d_norm = [b._use_move(foe, me, "GUST", "D", "A", 9999, 9999)[0] for _ in range(40)]
    assert sum(d_gust) > 1.8 * sum(d_norm)
    b._semi = {id(me): ("FLY", 5)}; b.turn_count = 6
    assert "avoided" in b._use_move(foe, me, "TACKLE", "D", "A", 999, 999)[1][-1]
    b.turn_count = 7   # charge kept through wrong answers, but the cover ends
    assert "avoided" not in b._use_move(foe, me, "TACKLE", "D", "A", 999, 999)[1][-1]
    b.turn_count = 5; b._semi = {}; b._charging = {}
    b._use_move(foe, me, "DIG", "D", "A", 999, 999)          # Dugtrio digs
    assert "avoided" in b._use_move(me, foe, "WING-ATTACK", "A", "D", 999, 999)[1][-1]
    assert b._use_move(me, foe, "EARTHQUAKE", "A", "D", 999, 999)[0] > 0
    b._charging[id(foe)] = "DIG"
    dmg, _, _ = b._use_move(foe, me, "DIG", "D", "A", 999, 999)   # strikes: cover gone
    assert id(foe) not in b._semi
    b._semi = {id(foe): ("DIVE", 5)}
    assert b._use_move(me, foe, "SURF", "A", "D", 999, 999)[0] > 0

def _fresh_story(start):
    from src.world.story import StoryManager
    st = StoryManager(); st.game = G; st.starting_region = start
    G.story_manager = st; return st

@test
def rival_per_region_fresh_and_multi_region():
    old = G.story_manager
    try:
        canon = {"KANTO": "BLUE", "JOHTO": "SILVER", "HOENN": "MAY", "SINNOH": "BARRY", "UNOVA": "CHEREN",
                 "KALOS": "SERENA", "ALOLA": "HAU", "GALAR": "HOP", "PALDEA": "NEMONA"}
        G.player_character = "red"
        for region, name in canon.items():           # fresh start in each region
            st = _fresh_story(region)
            assert st.assign_region_rival(region)["name"] == name, region
        # Kanto start, the player picked Silver as their rival and named him GARY
        st = _fresh_story("KANTO"); st.record_region_rival("KANTO", "GARY", "silver")
        st.rival_starter_raw = {"id": 4}; st.note_rival_starter("KANTO")
        seen = []
        for region in ["JOHTO", "HOENN", "SINNOH", "UNOVA", "KALOS", "ALOLA", "GALAR", "PALDEA"]:
            r = st.assign_region_rival(region)
            st.rival_starter_raw = {"id": 999}; st.note_rival_starter(region)
            seen.append((r["name"], r["character"]))
        assert st.region_rivals["JOHTO"]["name"] != "SILVER"        # Silver already used in Kanto
        keys = [st.region_rivals[r]["character"] for r in st.region_rivals]
        names = [st.region_rivals[r]["name"] for r in st.region_rivals]
        assert len(set(keys)) == len(keys) == 9 and len(set(names)) == 9 and "red" not in keys, seen
        assert st.rival_starter_id("KANTO") == 4                     # Kanto rival keeps a Kanto team
        st.current_area_key = "PALLET_TOWN"; st.sync_rival()
        assert G.rival_name == "GARY" and G.rival_character == "silver"
        data = st.serialize(); st2 = _fresh_story("KANTO"); st2.region_rivals = {}
        st2.region_rivals = {k.upper(): dict(v) for k, v in data["region_rivals"].items()}
        assert st2.region_rivals == st.region_rivals
    finally:
        G.story_manager = old

@test
def champion_stays_kanto_rival_after_moving():
    """The Champion is the Kanto rival with a Kanto-starter team even after the player moved on."""
    from src.states.overworld import GymLobbyState
    old = G.story_manager
    try:
        st = _fresh_story("KANTO"); st.player_team = [mk(G, 6, 70)]
        st.record_region_rival("KANTO", "GARY", "blue"); st.rival_starter_raw = {"id": 7}
        st.note_rival_starter("KANTO")
        st.assign_region_rival("JOHTO"); st.rival_starter_raw = {"id": 155}; st.note_rival_starter("JOHTO")
        G.rival_name, G.rival_character = "SILVER", "silver"      # as if the player is in Johto now
        st.current_area_key = "INDIGO_PLATEAU"; st.story_flags["gym_progress_INDIGO_PLATEAU"] = 4
        G.transitioning = False
        lb = GymLobbyState(G, None); G.change_state(lb); lb.challenge_gym()
        battle = G.current_state.battle_state if hasattr(G.current_state, "battle_state") else None
        b = battle or getattr(G.current_state, "next_state", None)
        names = [p.id for p in b.opponent_team]
        assert b.trainer_name == "GARY", getattr(b, "trainer_name", None)
        assert 9 in names, names                          # Blastoise line (rival took Squirtle)
        assert st.region_rivals["JOHTO"]["name"] == "SILVER"
    finally:
        G.story_manager = old

@test
def indigo_rematch_levels():
    from src.states.overworld import GymLobbyState
    old = G.story_manager
    try:
        def run(beaten, idx):
            st = _fresh_story("KANTO"); st.player_team = [mk(G, 6, 70)]
            st.record_region_rival("KANTO", "GARY", "blue"); st.rival_starter_raw = {"id": 1}
            st.note_rival_starter("KANTO"); st.current_area_key = "INDIGO_PLATEAU"
            st.story_flags["beat_champion"] = beaten
            st.story_flags["gym_progress_INDIGO_PLATEAU"] = idx
            G.transitioning = False
            lb = GymLobbyState(G, None); G.change_state(lb); lb.challenge_gym()
            b = G.current_state.next_state
            return [p.id for p in b.opponent_team], [p.level for p in b.opponent_team]
        first_e4, rem_e4 = run(False, 0), run(True, 0)
        assert max(first_e4[1]) < 64 and rem_e4 == ([87, 91, 221, 124, 131], [64, 63, 63, 66, 66]), (first_e4, rem_e4)
        first_ch, rem_ch = run(False, 4), run(True, 4)
        assert first_ch == ([18, 65, 112, 130, 59, 3], [59, 57, 59, 59, 61, 63]), first_ch
        assert rem_ch[1] == [72, 73, 72, 73, 73, 75] and rem_ch[0][-1] == 3 and 248 in rem_ch[0], rem_ch
        for i in (1, 2, 3):
            assert min(run(True, i)[1]) >= 64
    finally:
        G.story_manager = old

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try: t(); print("OK  ", t.__name__)
        except Exception as e: fails += 1; print("FAIL", t.__name__, repr(e))
    print(f"{len(TESTS)-fails}/{len(TESTS)} passed"); raise SystemExit(1 if fails else 0)
