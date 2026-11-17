
# PP and items that work like the games (11-16): bash dev/checks/run.sh items_pp
import random
from src.pokemon import pp as pplib, items as itemlib, catching, moves as movelib, breeding
from src.pokemon.contest import scarf_condition
from src.states.systems import BagState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None


def fresh(area="HOENN_ROUTE_101", me=25, foe=19, moves=None):
    """A wild battle where your Pokemon outlasts a weak foe with lots of HP (every turn gets played)."""
    b = battle(area, me, foe)
    p = b.player_pokemon
    if moves:
        p.moves = list(moves)
    p.level = 50
    b.player_hp = b.player_max_hp = p.current_hp = p.get_max_hp()
    b.opponent_pokemon.level = 3
    b.opponent_hp = b.opp_max_hp = b.opponent_pokemon.current_hp = 5000
    b._obey_level = lambda: 100
    return b


def turn(b, move):
    b.chosen_move = move
    b.resolve_turn(True)
    return drive(b)


print("1) PP: every move has the games' PP, and using it spends one")
b = fresh(moves=["THUNDERBOLT", "QUICK-ATTACK", "THUNDER-WAVE", "IRON-TAIL"])
p = b.player_pokemon
check(pplib.max_pp(g, p, "THUNDERBOLT") == 15 and pplib.max_pp(g, p, "QUICK-ATTACK") == 30, "Thunderbolt 15, Quick Attack 30")
turn(b, "QUICK-ATTACK")
check(pplib.left(g, p, "QUICK-ATTACK") == 29, f"one use: {pplib.left(g, p, 'QUICK-ATTACK')}/30")
check(pplib.left(g, p, "THUNDERBOLT") == 15, "the others are untouched")
b.opponent_pokemon.ability_slot = 0
from src.pokemon import abilities as ablib
orig_ab = b.ab
b.ab = lambda m: "PRESSURE" if m is b.opponent_pokemon else orig_ab(m)
turn(b, "QUICK-ATTACK")
check(pplib.left(g, p, "QUICK-ATTACK") == 27, "against Pressure a move spends 2 PP")
b.ab = orig_ab

print("2) out of PP: a move greys out; with none left, Struggle")
p.pp["THUNDERBOLT"] = 0
check("THUNDERBOLT" not in b._battle_moves(p) and "THUNDERBOLT" in b._menu_moves(p), "Thunderbolt at 0 PP: in the menu, not pickable")
b.phase = "MENU"
b.open_move_menu()
btn = next(x for x in b.move_buttons if getattr(x, "text", "").upper().startswith("THUNDERBOLT"))
check(btn.pp == (0, 15), f"its button shows PP 0/15 ({btn.pp})")
b.close_move_menu()
for m in p.moves:
    p.pp[m] = 0
check(b._battle_moves(p) == [movelib.STRUGGLE], "no PP in any move: Struggle")
hp0 = b.player_hp
lines = turn(b, "THUNDERBOLT")
check(any("STRUGGLE" in l.upper() for l in lines) and any("recoil" in l for l in lines), f"it struggles, with recoil: {lines[:3]}")
p.heal_full()
check(all(pplib.left(g, p, m) == pplib.max_pp(g, p, m) for m in p.moves), "a full heal (Pokemon Center) restores all PP")

print("3) two-turn moves spend PP once; the foe spends PP too")
b = fresh(moves=["SOLAR-BEAM", "TACKLE"])
p = b.player_pokemon
b.weather = None
turn(b, "SOLAR-BEAM"); turn(b, "TACKLE")
check(pplib.left(g, p, "SOLAR-BEAM") == pplib.max_pp(g, p, "SOLAR-BEAM") - 1, "Solar Beam: one PP for charge and hit")
foe = b.opponent_pokemon
check(any(pplib.left(g, foe, m) < pplib.max_pp(g, foe, m) for m in foe.moves), "the foe's moves spend PP")

print("4) saves keep PP and PP Ups; a newly set move has full PP")
p.pp["TACKLE"] = 3
p.pp_ups["TACKLE"] = 2
rec = story._pokemon_record(p)
back = story._load_pokemon(rec, g.loader)
check(back.pp.get("TACKLE") == 3 and back.pp_ups.get("TACKLE") == 2, "PP and PP Ups saved")
check(pplib.max_pp(g, back, "TACKLE") == 35 + 35 * 2 // 5, f"2 PP Ups: Tackle max {pplib.max_pp(g, back, 'TACKLE')}")
back.pp["EMBER"] = 0
movelib.set_move(back, 1, "EMBER")
check(pplib.left(g, back, "EMBER") == pplib.max_pp(g, back, "EMBER"), "a move set in comes with full PP")

print("5) PP items")
mon = mk(25); mon.moves = ["THUNDERBOLT", "QUICK-ATTACK"]
mon.pp = {"THUNDERBOLT": 2, "QUICK-ATTACK": 1}
ok, lines = pplib.use_item(g, mon, "ETHER", "THUNDERBOLT")
check(ok and pplib.left(g, mon, "THUNDERBOLT") == 12, f"Ether: +10 ({lines})")
ok, _ = pplib.use_item(g, mon, "MAX_ETHER", "THUNDERBOLT")
check(ok and pplib.left(g, mon, "THUNDERBOLT") == 15, "Max Ether: full")
ok, _ = pplib.use_item(g, mon, "MAX_ETHER", "THUNDERBOLT")
check(not ok, "Max Ether on a full move: no effect")
mon.pp = {"THUNDERBOLT": 2, "QUICK-ATTACK": 1}
pplib.use_item(g, mon, "ELIXIR")
check(pplib.left(g, mon, "THUNDERBOLT") == 12 and pplib.left(g, mon, "QUICK-ATTACK") == 11, "Elixir: +10 to every move")
pplib.use_item(g, mon, "MAX_ELIXIR")
check(not mon.pp, "Max Elixir: all full")
ok, _ = pplib.use_item(g, mon, "PP_UP", "THUNDERBOLT")
check(ok and pplib.max_pp(g, mon, "THUNDERBOLT") == 18 and pplib.left(g, mon, "THUNDERBOLT") == 18, "PP Up: 15 -> 18")
ok, _ = pplib.use_item(g, mon, "PP_MAX", "THUNDERBOLT")
check(ok and pplib.max_pp(g, mon, "THUNDERBOLT") == 24, "PP Max: 24")
check(not pplib.use_item(g, mon, "PP_UP", "THUNDERBOLT")[0], "no more PP Ups after the most")
# the Bag's way: a Pokemon, then a move
story.player_team = [mon]
mon.pp["THUNDERBOLT"] = 0
story.inventory["ETHER"] = 1
bag = BagState(g, None)
g.change_state(bag)
bag.use_item("ETHER")
check(type(g.current_state).__name__ == "PokemonPartyMenuState", "Ether: pick a Pokemon")
bag.on_pokemon_select_pp(0)
pick = g.current_state
check(type(pick).__name__ == "PickListState" and any("THUNDERBOLT" in r.text for r in pick.rows), "then pick its move (with PP shown)")
pick.pick("THUNDERBOLT")
check(pplib.left(g, mon, "THUNDERBOLT") == 10 and not story.inventory.get("ETHER"), "Ether used up: +10 PP")

print("6) a held Leppa Berry refills a move that runs out")
b = fresh(moves=["TACKLE", "GROWL"])
p = b.player_pokemon
p.pp["TACKLE"] = 1
p.held_item = "LEPPA_BERRY"; story.inventory["LEPPA_BERRY"] = 1
lines = turn(b, "TACKLE")
check(pplib.left(g, p, "TACKLE") == 10 and p.held_item is None and not story.inventory.get("LEPPA_BERRY"),
      f"Leppa: 0 -> 10 PP, eaten ({[l for l in lines if 'Leppa' in l]})")

print("7) held items in battle")
b = fresh(moves=["TACKLE", "GROWL"])
p, foe = b.player_pokemon, b.opponent_pokemon
s0 = b._speed(p)
p.held_item = "CHOICE_SCARF"
b.held_after_pick(p, "TACKLE")
check(b._battle_moves(p) == ["TACKLE"] and b._speed(p) > s0 * 1.4, "Choice Scarf: Speed x1.5, locked into Tackle")
b.vol(p).pop("choice_lock", None)
p.held_item = "CHOICE_BAND"
check(abs(b.ability_attack_mult(p, False) - 1.5) < 1e-6 and b.ability_attack_mult(p, True) == 1.0, "Choice Band: Attack x1.5")
p.held_item = "LIGHT_BALL"
check(b.held_attack_mult(p, True) == 2.0, "Light Ball: Pikachu's Sp. Atk x2")
p.held_item = "EXPERT_BELT"
check(b.held_final_mult(p, foe, 2.0) == 1.2 and b.held_final_mult(p, foe, 1.0) == 1.0, "Expert Belt: x1.2 when super effective")
p.held_item = "WIDE_LENS"; foe.held_item = "LAX_INCENSE"
check(abs(b.held_acc_mult(p, foe) - 0.99) < 1e-6, "Wide Lens x1.1, Lax Incense x0.9")
p.held_item = "IRON_BALL"; foe.held_item = None
check(abs(b._speed(p) * 2 - s0) <= 1 and b.grounded(p), "Iron Ball: half Speed, grounded")
p.held_item = "LAGGING_TAIL"
check(b.held_order(p) == -1, "Lagging Tail: moves last")
p.held_item = "KINGS_ROCK"
check(b.held_flinch(p, 0) == 10 and b.held_flinch(p, 30) == 30, "King's Rock: 10% flinch for attacks without one")
p.held_item = "METRONOME"
b.vol(p).pop("metronome_chain", None)
for _ in range(3):
    b.held_after_pick(p, "TACKLE")
check(abs(b.held_power_mult(p, foe, "TACKLE", {"type": "NORMAL"}) - 1.4) < 1e-6, "Metronome: third Tackle in a row x1.4")
p.held_item = "SILK_SCARF"
check(b.held_power_mult(p, foe, "TACKLE", {"type": "NORMAL"}) == itemlib.HELD_BOOST, "Silk Scarf: Normal moves x1.2")
p.held_item = "WHITE_HERB"; story.inventory["WHITE_HERB"] = 1
lines = b.change_stages(p, [["ATTACK", -2]], by_foe=True)
check(b.stages(p)["ATTACK"] == 0 and p.held_item is None and any("White Herb" in l for l in lines), "White Herb: lowered stats back, used up")
p.held_item = "SMOKE_BALL"
b.trainer_class = "WILD"
b.handle_run()
check(any("Got away" in l for l in b.dialogue_box.text_lines), "Smoke Ball: always gets away")
p.held_item = "SAFETY_GOGGLES"
check(not b._status_move_works(movelib.info(g, "SLEEP-POWDER"), p), "Safety Goggles: powder moves fail")

print("8) Power Herb, Rocky Helmet, Big Root, Destiny Knot")
b = fresh(moves=["SOLAR-BEAM", "TACKLE"])
p, foe = b.player_pokemon, b.opponent_pokemon
b.weather = None
p.held_item = "POWER_HERB"; story.inventory["POWER_HERB"] = 1
hp = b.opponent_hp
lines = turn(b, "SOLAR-BEAM")
check(b.opponent_hp < hp and p.held_item is None and any("Power Herb" in l for l in lines), "Power Herb: Solar Beam at once")
b = fresh(moves=["TACKLE"])
p, foe = b.player_pokemon, b.opponent_pokemon
foe.held_item = "ROCKY_HELMET"
hp = b.player_hp
lines = turn(b, "TACKLE")
check(any("Rocky Helmet" in l for l in lines), f"Rocky Helmet: Tackle hurts the attacker ({b.player_hp}/{hp})")
foe.held_item = None
p.held_item = "BIG_ROOT"
check(b.held_drain_mult(p) == 1.3, "Big Root: drain x1.3")
p.held_item = "DESTINY_KNOT"
p.gender, foe.gender = "M", "F"
lines = b.ailment_effect("infatuation", "ATTRACT", foe, p, "Foe", "Mine")
check(b.vol(p).get("infatuated") and b.vol(foe).get("infatuated"), f"Destiny Knot: both fall in love ({lines})")

print("9) held berries")
b = fresh(moves=["TACKLE"])
p, foe = b.player_pokemon, b.opponent_pokemon
p.held_item = "SITRUS_BERRY"; story.inventory["SITRUS_BERRY"] = 1
b.player_hp = p.current_hp = b.player_max_hp // 2
lines = b.held_after_action()
check(b.player_hp == b.player_max_hp // 2 + b.player_max_hp // 4 and not story.inventory.get("SITRUS_BERRY"),
      f"Sitrus at half HP: a quarter back ({lines})")
p.held_item = "LUM_BERRY"; story.inventory["LUM_BERRY"] = 1
p.status = "burn"
b.held_after_action()
check(not p.status and p.held_item is None, "Lum Berry cures a burn")
p.held_item = "PERSIM_BERRY"; story.inventory["PERSIM_BERRY"] = 1
b.vol(p)["confused"] = 3
b.held_after_action()
check(not b.vol(p).get("confused"), "Persim Berry: out of confusion")
p.held_item = "LIECHI_BERRY"; story.inventory["LIECHI_BERRY"] = 1
b.player_hp = p.current_hp = b.player_max_hp // 5
b.held_after_action()
check(b.stages(p)["ATTACK"] == 1, "Liechi Berry in a pinch: Attack up")
p.held_item = "ORAN_BERRY"; story.inventory["ORAN_BERRY"] = 0
check(b.held(p) is None, "a berry no longer in the Bag (used from it since) does nothing")
foe.held_item = "WACAN_BERRY"
ok, lines = b.held_resist_berry(p, foe, {"type": "ELECTRIC"}, 2.0)
check(ok and foe.held_item is None, f"Wacan Berry halves a super-effective Electric hit ({lines})")
p.held_item = "LEFTOVERS"
b.player_hp = p.current_hp = 10
b._status_chip(); after_chip = b.player_hp
b.effects_end_of_turn()
check(after_chip == 10 + max(1, b.player_max_hp // 16) and b.player_hp == after_chip, "Leftovers heal once a turn (not twice)")

print("10) the Bag: give or use, berries, Poke Toy, Gracidea, vitamins")
mon = mk(25); story.player_team = [mon]
story.inventory["ORAN_BERRY"] = 2
bag = BagState(g, None); g.change_state(bag)
bag.use_item("ORAN_BERRY")
check(type(g.current_state).__name__ == "PickListState", "an Oran Berry: use it, or give it to hold?")
g.current_state.pick("give")
bag.on_pokemon_select_hold(0)
check(mon.held_item == "ORAN_BERRY", "given to hold")
story.inventory["POMEG_BERRY"] = 1
mon.evs = {"HP": 20}
bag.selected_item = "POMEG_BERRY"; bag.on_pokemon_select_ev_berry(0)
check(mon.evs["HP"] == 10 and not story.inventory.get("POMEG_BERRY"), "Pomeg Berry: 10 fewer HP effort points")
check(bag.usable("PROTEIN") and bag.usable("PP_UP") and bag.usable("KINGS_ROCK"), "vitamins, PP Up, King's Rock usable from the Bag")
b = fresh(moves=["TACKLE"])
story.inventory["POKE_TOY"] = 1
bag = BagState(g, b, context="battle"); g.change_state(bag)
bag.use_item("POKE_TOY")
check(any("Got away" in l for l in b.dialogue_box.text_lines) and not story.inventory.get("POKE_TOY"), "Poke Toy: away from a wild Pokemon")
shaymin = mk(492); story.player_team = [shaymin]; story.inventory["GRACIDEA"] = 1
bag = BagState(g, None); g.change_state(bag)
import datetime as _dt
day = 6 <= _dt.datetime.now().hour < 20
bag.on_pokemon_select_gracidea(0)
check((story.player_team[0].form == "sky") == day, f"Gracidea: Shaymin's Sky Forme in the daytime ({story.player_team[0].form})")

print("11) every item the regions hand out has a description")
import glob, json, os, re
U = re.compile(r"^[A-Z][A-Z0-9_]+$")
keys = set()
def grab(v):
    if isinstance(v, str) and U.match(v):
        keys.add(v)
    elif isinstance(v, dict):
        for k, x in v.items():
            if U.match(str(k)) and isinstance(x, int):
                keys.add(k)
    elif isinstance(v, list):
        for x in v:
            grab(x)
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("gift_item", "rewards", "items", "stock", "extra_stock", "take_item", "daily_gift"):
                grab(v)
            else:
                walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)
for f in glob.glob("assets/*_area_data.json") + ["assets/town_maps.json", "assets/hoenn_oras.json", "assets/dungeon_routes.json"]:
    walk(json.load(open(f, encoding="utf-8")))
species = {str(n).upper() for n in g.name_to_id}
flags = {k for k in keys if k.endswith("_HALL_OF_FAME") or k.startswith("POKEMON_") or k in ("balls", "EVENT")}
missing = sorted(k for k in keys - species - flags - set(story.RETIRED_ITEMS) if not itemlib.describe(k))  # (retired items leave the Bag on load)
check(not missing, f"no item without a description: {missing[:12]}")

print("12) exchanges, balls, Day Care, Contests")
from src.states.overworld.common import _run_story_event
_tm = json.load(open("assets/town_maps.json", encoding="utf-8"))
def _find_event(o, key):
    if isinstance(o, dict):
        if isinstance(o.get("event"), dict) and key in o["event"]:
            return o["event"]
        o = list(o.values())
    if isinstance(o, list):
        for v in o:
            hit = _find_event(v, key)
            if hit:
                return hit
    return None
story.inventory.update({"SHOAL_SALT": 4, "SHOAL_SHELL": 4})
shown = []
ev = _find_event(_tm["HOENN_SHOAL_CAVE"], "craft")
class _S: pass
st = _S(); st.game = g
_run_story_event(st, ev, lambda c: True, lambda lines: shown.append(lines))
check(story.inventory.get("SHELL_BELL") == 1 and not story.inventory.get("SHOAL_SALT"), "Shoal Cave: 4 Salt + 4 Shells = a Shell Bell")
story.inventory["BLUE_SHARD"] = 1
ev = _find_event(_tm["HOENN_ROUTE_124"], "swap")
_run_story_event(st, ev, lambda c: True, lambda lines: shown.append(lines))
check(story.inventory.get("WATER_STONE", 0) >= 1 and not story.inventory.get("BLUE_SHARD"), "Treasure Hunter: a Blue Shard for a Water Stone")
snorlax, pika = mk(143), mk(25)
check(catching.ball_bonus("HEAVY_BALL", g, snorlax) > 1 and catching.ball_bonus("HEAVY_BALL", g, pika) < 1, "Heavy Ball: better for heavy Pokemon")
a, c = mk(25), mk(25)
a.held_item = "DESTINY_KNOT"
for x in (a, c):
    x.ivs = {k: 31 for k in x.ivs}
same = 0
random.seed(3)
egg = breeding.make_egg(g, a, c)
check(sum(1 for v in egg.ivs.values() if v == 31) >= 5, f"Destiny Knot: 5 IVs passed on ({egg.ivs})")
m = mk(25); m.condition["COOL"] = 100; m.held_item = "RED_SCARF"
check(scarf_condition(m, "COOL") == 110 and scarf_condition(m, "CUTE") == 0, "Red Scarf: Cool condition counts a tenth more")


print("13) effort points from battle; Exp. Share is the Option only")
b = fresh(moves=["TACKLE"])
p = b.player_pokemon
p.evs = {}
b.opponent_pokemon = mk(143)  # Snorlax: 2 HP
b.opponent_pokemon.level = 3
b.opponent_hp = 0
b._award_battle_xp()
check(p.evs.get("HP") == 2, f"beating a Snorlax: +2 HP effort points ({p.evs})")
p.held_item = "MACHO_BRACE"
b._award_battle_xp()
check(p.evs.get("HP") == 6, f"with a Macho Brace: twice as many ({p.evs})")
p.evs = {"HP": 251}
itemlib.gain_battle_evs(g, p, 143)
check(p.evs["HP"] == 252, "a stat stops at 252")
p.evs = {"ATTACK": 252, "SPEED": 252, "DEFENSE": 5}
itemlib.gain_battle_evs(g, p, 143)
check(sum(p.evs.values()) == 510, "510 in all")
story.inventory["EXP_SHARE"] = 1
story.sync_key_items()
check(not story.inventory.get("EXP_SHARE"), "an old save's Exp. Share item is taken out of the Bag")
story.exp_share = False
team = [p, mk(1)]
story.player_team = team
b._xp_participants = [p]
check([x for x, _ in b._xp_shares()] == [p], "EXP SHARE off in Options: only the battler shares")
story.exp_share = True


print("14) moves powered by weight; the Float Stone")
check(movelib.usable(movelib.info(g, "LOW-KICK")) and movelib.usable(movelib.info(g, "HEAVY-SLAM")), "Low Kick and Heavy Slam can be learned")
snorlax, pika, onix = mk(143), mk(25), mk(95)
check(movelib.weight_power(g, "LOW-KICK", pika, snorlax) == 120 and movelib.weight_power(g, "GRASS-KNOT", snorlax, pika) == 20,
      "Low Kick on a Snorlax (460 kg): 120; Grass Knot on a Pikachu (6 kg): 20")
check(movelib.weight_power(g, "HEAVY-SLAM", snorlax, pika) == 120 and movelib.weight_power(g, "HEAT-CRASH", pika, snorlax) == 40,
      "Heavy Slam: Snorlax on Pikachu 120, Pikachu on Snorlax 40")
snorlax.held_item = "FLOAT_STONE"
check(movelib.weight_power(g, "LOW-KICK", pika, snorlax) == 120 and catching.weight(g, snorlax) == 230, "a Float Stone halves its weight")
onix.held_item = "FLOAT_STONE"
check(movelib.weight_power(g, "LOW-KICK", pika, onix) == 100, "Onix (210 kg) with a Float Stone: Low Kick 100, not 120")
b = fresh(moves=["LOW-KICK"])
b.opponent_pokemon = foe = mk(143)
foe.level = 3
b.opponent_hp = b.opp_max_hp = foe.current_hp = 5000
lines = turn(b, "LOW-KICK")
check(b.opponent_hp < 5000 and any("LOW KICK" in l.upper() for l in lines), f"Low Kick hits in battle ({5000 - b.opponent_hp} damage)")

print("##### FAILURES:", fails)
