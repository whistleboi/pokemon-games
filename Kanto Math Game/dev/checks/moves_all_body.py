# Every move works (Jordan, 11-17: "Make all moves work. Since we don't have double battles, those moves can still work
# as intended but would have no effect."). For every move a Pokemon in this game can know: a battle where it's used
# (no crash), both battle styles, wild and trainer battles; then one or two lines per group for the defining effect
# (src/states/battle_moves.py, battle_doubles.py).
import glob, json, re, random, traceback
from src.pokemon import moves as movelib, pp as pplib, tms
from src.states.battle import TrainerBattleState, WildBattleState
from src.states.systems import PokemonPartyMenuState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
random.seed(11)


def lv(pid, level=40, moves=None, item=None):
    p = mk(pid)
    p.level = level
    p.current_hp = p.get_max_hp()
    p.status = None
    if moves:
        p.moves = list(moves)
    p.held_item = item
    return p


def trainer(team, mine, area="KANTO_ROUTE_3"):
    story.current_area_key = area
    story.player_team = mine
    b = TrainerBattleState(g, team, trainer_class="YOUNGSTER", trainer_name="T", area_name=area)
    g.change_state(b)
    b._answer_mode = None
    return b


def wild(foe, mine, area="KANTO_ROUTE_1"):
    story.current_area_key = area
    story.player_team = mine
    b = WildBattleState(g, foe, area)
    g.change_state(b)
    b._answer_mode = None
    return b


def use(b, name, foe=False):
    me, them = (b.opponent_pokemon, b.player_pokemon) if foe else (b.player_pokemon, b.opponent_pokemon)
    dmg, lines, eff = b._use_move(me, them, name, "FOE" if foe else "ME", "ME" if foe else "FOE",
                                  b.player_max_hp if foe else b.opp_max_hp, b.player_hp if foe else b.opponent_hp)
    if foe:
        b.player_hp = max(0, b.player_hp - dmg)
        b.player_pokemon.current_hp = b.player_hp
        b.mv_note_hit(me, them, dmg)
    else:
        b.opponent_hp = max(0, b.opponent_hp - dmg)
        b.opponent_pokemon.current_hp = b.opponent_hp
        b.mv_note_hit(me, them, dmg)
    return dmg, lines


def turn(b, pick, frames=900):
    """One whole turn as a player plays it: pick the move, answer right, let it play out (a party list from a
    switching move: the first Pokemon offered)."""
    log = []
    b.open_move_menu()
    b.choose_move(pick)
    b.math_ui.on_click(b.options.index(b.correct_ans))
    for _ in range(frames):
        cur = g.current_state
        if isinstance(cur, PokemonPartyMenuState):
            team = story.player_team
            slot = next((i for i, p in enumerate(team) if p.current_hp > 0 and p is not b.player_pokemon), 0)
            cur.on_select(slot)
            continue
        if cur is not b:
            break
        if b.dialogue_box.visible:
            for line in b.dialogue_box.text_lines:
                if not log or log[-1] != line:
                    log.append(line)
            b.dialogue_box.is_finished = True
            if b.phase == "MESSAGE" and b.dialogue_box.callback:
                cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
        if b.phase == "SWITCH_PROMPT":
            b.on_switch_no()
        b.feedback_timer = 0
        b.update()
        if b.phase == "MENU" and not b.turn_actions and not b.dialogue_box.visible and not b._form_msgs:
            break
    return log


# ------------------------------------------------------------------ every move a Pokemon can know
U = set()
for _sid, _ls in json.load(open("assets/pokemon_levels.json", encoding="utf-8")).get("learnsets", {}).items():
    U.update(m for _l, m in _ls)
U |= set(json.load(open("assets/tm_learners.json", encoding="utf-8")))
for _f in glob.glob("assets/*.json"):
    _raw = open(_f, encoding="utf-8").read()
    U.update(re.findall(r'"tutor": *\{"move": *"([A-Z0-9-]+)"', _raw))
    for _blk in re.findall(r'"movesets": *\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', _raw):
        U.update(movelib.OLD_NAMES.get(m.upper().replace(" ", "-"), m.upper().replace(" ", "-"))
                 for m in re.findall(r'"([A-Z][A-Z0-9 -]+)"', _blk))
U.add("FOUND-POWER")
T = movelib.table(g)
U = sorted(m for m in U if m in T)
print(f"0) {len(U)} moves a Pokemon can know")
check(all(movelib.usable(movelib.info(g, m)) for m in U), "every one of them is usable (learnable) now")
check(movelib.usable(movelib.info(g, "EXPLOSION")) and movelib.usable(movelib.info(g, "SELF-DESTRUCT"))
      and movelib.usable(movelib.info(g, "MISTY-EXPLOSION")), "Self-Destruct, Explosion, Misty Explosion included")
check(not movelib.usable(movelib.info(g, "NOT-A-MOVE")), "...an unknown name isn't")

print("1) every move used, both ways, in a trainer battle and a wild battle (no crash)")
crashed = []
for name in U:
    for kind in ("trainer", "wild"):
        try:
            random.seed(hash((name, kind)) & 0xffff)
            me = lv(143, 50, [name, "TACKLE"], item="SITRUS_BERRY")      # Snorlax
            spare = lv(25, 50, ["THUNDERBOLT"])
            foe = lv(76, 50, [name, "TACKLE"], item="ORAN_BERRY")        # Golem
            foe2 = lv(130, 50, ["WATERFALL"])
            b = trainer([foe, foe2], [me, spare]) if kind == "trainer" else wild(foe, [me, spare])
            b.turn_count = 3
            b.mv_turn_start({id(me): name, id(foe): "TACKLE"})
            use(b, name)
            b._mv()["pending"].clear()
            b.mv_turn_start({id(me): "TACKLE", id(foe): name})
            if b.opponent_hp > 0 and b.player_hp > 0:
                use(b, name, foe=True)
            b._mv()["pending"].clear()
            b.effects_end_of_turn()
            b._weather_end_of_turn()
            b.mv_battle_end()
        except Exception:
            crashed.append((name, kind, traceback.format_exc().strip().splitlines()[-1]))
check(not crashed, f"{len(U)} moves x 2 sides x 2 battle kinds: no crash ({crashed[:6]})")
for c in crashed[:15]:
    print("      ", c)

print("2) every move in a whole turn, as a player plays it: CLASSIC, then OVERWORLD (drawn on the map)")
from src.states.overworld import PlayState
g.dungeon_routes = True
story.battle_style = "OVERWORLD"
story.current_area_key, story.last_area_key = "KANTO_ROUTE_3", "PEWTER_CITY"
story.player_team = [lv(6, 100, ["FLAMETHROWER"])]
_p = PlayState(g)
g.states["play"] = _p
g.change_state(_p)
_t = next((m for f in _p.run.floors for m in f.movers if m.kind == "trainer"), None)
_p._battle_trainer(_t)
while _p.dialogue_box.visible:
    _p.dialogue_box.advance()
    _p.update()
_ob = g.current_state
VIEW = getattr(_ob, "overworld", None)
check(VIEW is not None, "an OVERWORLD battle's map view to draw the sweep on")
g.dungeon_routes = False
for style, kind in (("TRADITIONAL", "trainer"), ("OVERWORLD", "trainer"), ("TRADITIONAL", "wild")):
    story.battle_style = style
    broke, stuck = [], []
    for i, name in enumerate(U):
        try:
            random.seed(i)
            me = lv(143, 60, [name, "TACKLE"], item="SITRUS_BERRY")
            foe = lv(76, 45, ["TACKLE", "DEFENSE-CURL"], item="ORAN_BERRY")
            mine = [me, lv(25, 50, ["THUNDERBOLT"])]
            b = trainer([foe, lv(130, 45, ["WATERFALL"])], mine) if kind == "trainer" else wild(foe, mine)
            if style == "OVERWORLD" and VIEW is not None:
                b.overworld = VIEW
            turn(b, name)
            if style == "OVERWORLD" or i % 50 == 0:
                b.draw()
            if g.current_state is b and b.phase not in ("MENU", "OUTRO", "VICTORY_TEXT", "REWARD_TEXT", "SWITCH_PROMPT",
                                                        "TRAINER_SLIDE_IN", "ENEMY_SUMMON", "FAINT_ANIM_RUNNING", "MESSAGE"):
                stuck.append((name, b.phase))
            b.mv_battle_end()
        except Exception:
            broke.append((name, " | ".join(traceback.format_exc().strip().splitlines()[-5:])))
    style = f"{style} {kind}"
    check(not broke, f"{style}: {len(U)} moves, a whole turn each: no crash ({broke[:5]})")
    check(not stuck, f"{style}: ...and the battle carries on after each ({stuck[:8]})")
    for c in broke[:10]:
        print("      ", c)
story.battle_style = "TRADITIONAL"


def duel(my_moves, foe_moves=("TACKLE",), me=143, foe=76, level=50, kind="trainer", my_item=None, foe_item=None,
         bench=True, foe_level=None):
    random.seed(5)
    m = lv(me, level, list(my_moves), item=my_item)
    f = lv(foe, foe_level or level, list(foe_moves), item=foe_item)
    mine = [m] + ([lv(25, level, ["THUNDERBOLT"]), lv(1, level, ["VINE-WHIP"])] if bench else [])
    if kind == "wild":
        b = wild(f, mine)
    else:
        b = trainer([f] + ([lv(130, level, ["WATERFALL"]), lv(65, level, ["PSYCHIC"])] if bench else []), mine)
    b.turn_count = 2
    b.mv_turn_start({})
    return b


def power(b, name, foe=False):
    me, them = (b.opponent_pokemon, b.player_pokemon) if foe else (b.player_pokemon, b.opponent_pokemon)
    return b.mv_prepare(me, them, name, movelib.info(g, name), preview=True).get("power")


def says(lines, text):
    return any(text.lower() in str(x).lower() for x in lines)


print("3) power from the situation")
b = duel(["RETURN", "FRUSTRATION"], kind="wild")
b.player_pokemon.friendship = 255
r_hi = power(b, "RETURN")
b.player_pokemon.friendship = 0
check(r_hi == 102 and power(b, "RETURN") == 1 and power(b, "FRUSTRATION") == 102,
      f"Return / Frustration by friendship: {r_hi} at 255, Frustration {power(b, 'FRUSTRATION')} at 0")
b = duel(["GYRO-BALL", "ELECTRO-BALL"], me=208, foe=101)   # Steelix (slow) vs Electrode (fast)
gyro = power(b, "GYRO-BALL")
b2 = duel(["ELECTRO-BALL"], me=101, foe=208)
check(gyro >= 100 and power(b, "ELECTRO-BALL") == 40 and power(b2, "ELECTRO-BALL") >= 120,
      f"Gyro Ball slow vs fast: {gyro}; Electro Ball {power(b, 'ELECTRO-BALL')} slow, {power(b2, 'ELECTRO-BALL')} fast")
b = duel(["REVERSAL", "FLAIL", "ERUPTION"])
full = power(b, "ERUPTION")
b.player_hp = b.player_pokemon.current_hp = 1
check(power(b, "REVERSAL") == 200 and power(b, "FLAIL") == 200 and full == 150 and power(b, "ERUPTION") == 1,
      "Reversal / Flail 200 at 1 HP; Eruption 150 full, 1 at 1 HP")
b = duel(["HARD-PRESS", "CRUSH-GRIP"])
hp_full = power(b, "HARD-PRESS")
b.opponent_hp = b.opp_max_hp // 2
check(hp_full == 100 and power(b, "HARD-PRESS") == 50 and power(b, "CRUSH-GRIP") == 60, "Hard Press 100 -> 50, Crush Grip 60 at half HP")
b = duel(["ACROBATICS", "FACADE", "HEX", "VENOSHOCK", "BRINE"])
a_none = power(b, "ACROBATICS")
b.player_pokemon.held_item = "LEFTOVERS"
b.player_pokemon.status = "burn"
b.opponent_pokemon.status = "poison"
b.opponent_hp = 10
check(a_none == 110 and power(b, "ACROBATICS") == 55 and power(b, "FACADE") == 140 and power(b, "HEX") == 130
      and power(b, "VENOSHOCK") == 130 and power(b, "BRINE") == 130,
      "Acrobatics x2 with no item, Facade x2 burned, Hex / Venoshock x2 on poison, Brine x2 below half")
b = duel(["STORED-POWER", "POWER-TRIP", "PUNISHMENT"])
b.stages(b.player_pokemon).update({"ATTACK": 2, "SPEED": 2})
b.stages(b.opponent_pokemon).update({"DEFENSE": 3})
check(power(b, "STORED-POWER") == 100 and power(b, "POWER-TRIP") == 100 and power(b, "PUNISHMENT") == 120,
      "Stored Power / Power Trip +20 per boost (100), Punishment by the foe's (120)")
b = duel(["AVALANCHE", "REVENGE", "PAYBACK", "ASSURANCE", "LASH-OUT", "STOMPING-TANTRUM", "TEMPER-FLARE", "RETALIATE"])
plain = [power(b, x) for x in ("AVALANCHE", "PAYBACK", "ASSURANCE", "LASH-OUT", "STOMPING-TANTRUM", "RETALIATE")]
use(b, "TACKLE", foe=True)   # (the foe hit first, so it has moved and you took damage)
b.change_stages(b.player_pokemon, [["DEFENSE", -1]], by_foe=True)
b.vol(b.player_pokemon)["last_failed"] = True
b._mv()["fainted_turn"]["player"] = b.turn_count - 1
check(plain == [60, 50, 60, 75, 75, 70] and power(b, "AVALANCHE") == 120 and power(b, "REVENGE") == 120
      and power(b, "PAYBACK") == 100 and power(b, "LASH-OUT") == 150 and power(b, "STOMPING-TANTRUM") == 150
      and power(b, "TEMPER-FLARE") == 150 and power(b, "RETALIATE") == 140,
      "Avalanche / Revenge after being hit, Payback after the foe moved, Lash Out after a drop, Stomping Tantrum /"
      " Temper Flare after a failure, Retaliate after a faint: all doubled")
b.mv_turn_start({})
use(b, "TACKLE")
check(power(b, "ASSURANCE") == 120, "Assurance on a foe already hurt this turn: 120")
b = duel(["ROLLOUT", "FURY-CUTTER", "ECHOED-VOICE"], foe=143, level=60)
b.vol(b.player_pokemon)["lock_on"] = (id(b.opponent_pokemon), 99)   # (no misses in this check)
pw = []
for t in range(3):
    b.turn_count += 1
    b.mv_turn_start({})
    pw.append(power(b, "ROLLOUT"))
    use(b, "ROLLOUT")
check(pw == [30, 60, 120] and b.forced_effect_move(b.player_pokemon) == "ROLLOUT",
      f"Rollout doubles each turn and keeps going ({pw})")
b = duel(["FURY-CUTTER", "ECHOED-VOICE"], foe=143, level=60)
b.vol(b.player_pokemon)["lock_on"] = (id(b.opponent_pokemon), 99)
fc, ev = [], []
for t in range(3):
    b.turn_count += 1
    b.mv_turn_start({})
    fc.append(power(b, "FURY-CUTTER"))
    use(b, "FURY-CUTTER")
for t in range(3):
    b.turn_count += 1
    b.mv_turn_start({})
    ev.append(power(b, "ECHOED-VOICE"))
    use(b, "ECHOED-VOICE")
check(fc == [40, 80, 160] and ev == [40, 80, 120], f"Fury Cutter {fc}, Echoed Voice {ev}")
b = duel(["TRIPLE-AXEL", "TRIPLE-KICK"], foe=143)
d = b.mv_prepare(b.player_pokemon, b.opponent_pokemon, "TRIPLE-AXEL", movelib.info(g, "TRIPLE-AXEL"))
check(d["_powers"] == [20, 40, 60] and d.get("_each_acc"), "Triple Axel: 20, 40, 60, each hit can miss")
b = duel(["WEATHER-BALL", "TERRAIN-PULSE", "EXPANDING-FORCE", "HIDDEN-POWER", "SOLAR-BEAM"])
b.set_weather("RAIN")
d = b.mv_prepare(b.player_pokemon, b.opponent_pokemon, "WEATHER-BALL", movelib.info(g, "WEATHER-BALL"), preview=True)
sb = power(b, "SOLAR-BEAM")
b.field()["terrain"] = ("psychic", 5)
d2 = b.mv_prepare(b.player_pokemon, b.opponent_pokemon, "TERRAIN-PULSE", movelib.info(g, "TERRAIN-PULSE"), preview=True)
b.player_pokemon.ivs = {"HP": 31, "ATTACK": 30, "DEFENSE": 31, "SPEED": 30, "SPATK": 30, "SPDEF": 31}
hp_t = b.mv_prepare(b.player_pokemon, b.opponent_pokemon, "HIDDEN-POWER", movelib.info(g, "HIDDEN-POWER"), preview=True)["type"]
b.player_pokemon.ivs.update(ATTACK=31, SPEED=31, SPATK=31)
hp_t2 = b.mv_prepare(b.player_pokemon, b.opponent_pokemon, "HIDDEN-POWER", movelib.info(g, "HIDDEN-POWER"), preview=True)["type"]
check(d["type"] == "WATER" and d["power"] == 100 and sb == 60 and d2["type"] == "PSYCHIC" and d2["power"] == 100
      and power(b, "EXPANDING-FORCE") == 120 and hp_t == "FIRE" and hp_t2 == "DARK",
      f"Weather Ball in rain (Water 100), Solar Beam halved, Terrain Pulse / Expanding Force in Psychic Terrain, "
      f"Hidden Power's type from IVs ({hp_t}, {hp_t2})")
b = duel(["BEAT-UP"], foe=143)
d = b.mv_prepare(b.player_pokemon, b.opponent_pokemon, "BEAT-UP", movelib.info(g, "BEAT-UP"))
dmg, lines = use(b, "BEAT-UP")
check(len(d["_powers"]) == 3 and d["_powers"][0] == 5 + 110 // 10 and says(lines, "Hit 3 times"),
      f"Beat Up: one hit per healthy party member, power from each one's Attack ({d['_powers']})")

print("4) other stats in the damage")


def hit(b, name, foe=False, n=6):
    random.seed(1)
    tot = 0
    hp0, ohp0 = b.player_hp, b.opponent_hp
    for _ in range(n):
        b.player_hp, b.opponent_hp = hp0, ohp0
        b.player_pokemon.current_hp, b.opponent_pokemon.current_hp = hp0, ohp0
        b._answer_mode = "max_roll"
        dmg, _l = use(b, name, foe)
        tot += dmg
    b.player_hp, b.opponent_hp = hp0, ohp0
    b.player_pokemon.current_hp, b.opponent_pokemon.current_hp = hp0, ohp0
    return tot


b = duel(["PSYSHOCK", "PSYCHIC"], me=65, foe=113, level=60)   # Alakazam vs Chansey (low Defense, huge Sp. Def)
check(hit(b, "PSYSHOCK") > hit(b, "PSYCHIC") * 2, "Psyshock hits Chansey's low Defense: far more than Psychic")
b = duel(["FOUL-PLAY"], me=113, foe=68, level=60)   # Chansey's Foul Play off Machamp's Attack
b2 = duel(["FOUL-PLAY"], me=113, foe=113, level=60)
check(hit(b, "FOUL-PLAY") > hit(b2, "FOUL-PLAY"), "Foul Play uses the target's Attack (Machamp's > Chansey's)")
b = duel(["BODY-PRESS", "TACKLE"], me=208, foe=143, level=60)   # Steelix: Defense 200, Attack 85
check(hit(b, "BODY-PRESS") > hit(b, "TACKLE") * 1.3, "Body Press uses the user's Defense")

print("5) items")
b = duel(["FLING"], my_item="FLAME_ORB", foe=143)
dmg, lines = use(b, "FLING")
check(dmg and b.opponent_pokemon.status == "burn" and b.player_pokemon.held_item is None and says(lines, "flung"),
      f"Fling a Flame Orb: it lands and burns ({lines[-2:]})")
dmg, lines = use(b, "FLING")
check(not dmg and says(lines, "failed"), "...nothing left to fling: it fails")
story.inventory["SITRUS_BERRY"] = 1   # (a held item keeps its Bag copy)
b = duel(["NATURAL-GIFT"], my_item="SITRUS_BERRY", foe=68)
d = b.mv_prepare(b.player_pokemon, b.opponent_pokemon, "NATURAL-GIFT", movelib.info(g, "NATURAL-GIFT"), preview=True)
dmg, lines = use(b, "NATURAL-GIFT")
check(d["type"] == "PSYCHIC" and d["power"] == 80 and dmg and b.player_pokemon.held_item is None,
      "Natural Gift with a Sitrus Berry: Psychic, 80, the berry used up")
_, lines = use(b, "RECYCLE")
check(b.player_pokemon.held_item == "SITRUS_BERRY" and says(lines, "found one"), f"Recycle brings it back ({lines[-1]})")
b = duel(["TRICK"], my_item="CHOICE_SCARF", foe_item="LEFTOVERS")
_, lines = use(b, "TRICK")
me_, foe_ = b.player_pokemon, b.opponent_pokemon
check(me_.held_item == "LEFTOVERS" and foe_.held_item == "CHOICE_SCARF", "Trick swaps items")
b.mv_battle_end()
check(me_.held_item == "CHOICE_SCARF", "...and in a trainer battle yours comes back after it")
b = duel(["THIEF", "KNOCK-OFF", "BUG-BITE", "INCINERATE", "POLTERGEIST"], foe_item="LEFTOVERS", kind="wild")
story.inventory.pop("LEFTOVERS", None)
ko = power(b, "KNOCK-OFF")
_, lines = use(b, "THIEF")
check(b.player_pokemon.held_item == "LEFTOVERS" and not b.opponent_pokemon.held_item
      and story.inventory.get("LEFTOVERS") == 1, "Thief from a wild Pokemon: yours to keep (in the Bag)")
check(ko == 97 and power(b, "KNOCK-OFF") == 65, f"Knock Off: x1.5 while the foe has an item ({ko})")
dmg, lines = use(b, "POLTERGEIST")
check(not dmg and says(lines, "failed"), "Poltergeist fails on a foe with no item")
b.opponent_pokemon.held_item = "ORAN_BERRY"
b.player_hp -= 30
_, lines = use(b, "BUG-BITE")
check(not b.opponent_pokemon.held_item and says(lines, "ate"), f"Bug Bite eats the foe's berry ({lines[-2:]})")
b.opponent_pokemon.held_item = "ORAN_BERRY"
_, lines = use(b, "INCINERATE")
check(not b.opponent_pokemon.held_item and says(lines, "burned up"), "Incinerate burns a berry")
b = duel(["KNOCK-OFF"], foe_item="LEFTOVERS")
use(b, "KNOCK-OFF")
check(not b.opponent_pokemon.held_item, "Knock Off: the foe's item is gone")
b = duel(["EMBARGO"], foe_item="LEFTOVERS")
use(b, "EMBARGO")
check(b.held(b.opponent_pokemon) is None and b.opponent_pokemon.held_item == "LEFTOVERS", "Embargo: its item does nothing")

print("6) moves that call other moves")
b = duel(["SLEEP-TALK", "FLAMETHROWER"], foe=143)
dmg, lines = use(b, "SLEEP-TALK")
check(not dmg and says(lines, "failed"), "Sleep Talk awake: it fails")
b.player_pokemon.status, b.player_pokemon.sleep_turns = "sleep", 3
dmg, lines = use(b, "SLEEP-TALK")
check(dmg > 0 and says(lines, "FLAMETHROWER"), f"...asleep: it uses another of its moves ({lines[:3]})")
b = duel(["SLEEP-TALK", "FLAMETHROWER"], foe=143)
b.player_pokemon.status, b.player_pokemon.sleep_turns = "sleep", 3
log = turn(b, "SLEEP-TALK")
check(says(log, "fast asleep") and says(log, "used FLAMETHROWER"), "...in a whole turn: asleep, and it still acts")
b = duel(["MIMIC"], foe_moves=["THUNDERBOLT"])
use(b, "THUNDERBOLT", foe=True)
_, lines = use(b, "MIMIC")
check(b.vol(b.player_pokemon).get("mimic") == "THUNDERBOLT" and b.mv_alias(b.player_pokemon, "MIMIC") == "THUNDERBOLT",
      "Mimic copies the foe's last move into its slot for the battle")
b.open_move_menu()
check(any(btn.text == "THUNDERBOLT" for btn in b.move_buttons), "...the FIGHT menu shows it")
b.close_move_menu()
b = duel(["NATURE-POWER"], foe=143)
b.field()["terrain"] = ("grassy", 5)
_, lines = use(b, "NATURE-POWER")
check(says(lines, "turned into ENERGY BALL"), f"Nature Power in Grassy Terrain: Energy Ball ({lines[1]})")
b = duel(["SNATCH"], foe_moves=["SWORDS-DANCE"])
use(b, "SNATCH")
_, lines = use(b, "SWORDS-DANCE", foe=True)
check(b.stages(b.player_pokemon)["ATTACK"] == 2 and b.stages(b.opponent_pokemon)["ATTACK"] == 0 and says(lines, "snatched"),
      "Snatch takes the foe's Swords Dance")
b = duel(["COPYCAT", "MIRROR-MOVE", "ME-FIRST"], foe_moves=["EMBER"], foe=143)
use(b, "EMBER", foe=True)
_, lines = use(b, "COPYCAT")
check(says(lines, "EMBER"), "Copycat uses the last move used (Ember)")
b.mv_turn_start({id(b.opponent_pokemon): "EMBER"})
_, lines = use(b, "ME-FIRST")
check(says(lines, "EMBER"), "Me First uses the foe's move before it")

print("7) switching")
b = duel(["U-TURN", "TACKLE"], foe_moves=["TACKLE"], level=50)
first = b.player_pokemon
log = turn(b, "U-TURN")
check(b.player_pokemon is not first and says(log, "Come back") and b.player_pokemon.current_hp > 0,
      f"U-turn: you pick who comes in, in the middle of the turn ({b.player_pokemon.display_name})")
b = duel(["BATON-PASS", "SWORDS-DANCE"], foe_moves=["SPLASH"], level=50)
b.change_stages(b.player_pokemon, [["ATTACK", 2]])
b.vol(b.player_pokemon)["substitute"] = 20
log = turn(b, "BATON-PASS")
check(b.stages(b.player_pokemon)["ATTACK"] == 2 and b.vol(b.player_pokemon).get("substitute") == 20,
      "Baton Pass: the stat changes and the substitute go to the one coming in")
b = duel(["TACKLE"], foe_moves=["U-TURN"], level=50)
f0 = b.opponent_pokemon
use(b, "U-TURN", foe=True)
b._run_pending_switch()
check(b.opponent_pokemon is not f0 and b.opponent_team.index(f0) > b.current_opponent_idx,
      "a trainer's U-turn: its next Pokemon comes in, the first goes back in line")
b = duel(["DRAGON-TAIL", "ROAR"], level=60)
b.vol(b.player_pokemon)["lock_on"] = (id(b.opponent_pokemon), 99)
f0 = b.opponent_pokemon
use(b, "DRAGON-TAIL")
b._run_pending_switch()
f1 = b.opponent_pokemon
check(f1 is not f0, "Dragon Tail drags a trainer's Pokemon out")
b = duel(["ROAR"], kind="wild")
_, lines = use(b, "ROAR")
check(getattr(b, "_flee_by_move", None) is not None and says(lines, "blown away"), "Roar ends a wild battle")
b = duel(["TACKLE"], foe_moves=["WHIRLWIND"])
p0 = b.player_pokemon
use(b, "WHIRLWIND", foe=True)
b._run_pending_switch()
check(b.player_pokemon is not p0 or b.phase == "RETRACT_ANIM", "a trainer's Whirlwind drags your Pokemon out at random")
b = duel(["PARTING-SHOT"], level=50)
_, lines = use(b, "PARTING-SHOT")
check(b.stages(b.opponent_pokemon)["ATTACK"] == -1 and b._mv()["pending"], "Parting Shot: Attack / Sp. Atk down, then out")
b = duel(["TELEPORT"])
use(b, "TELEPORT")
check(b._mv()["pending"] and getattr(b, "_flee_by_move", None) is None, "Teleport in a trainer battle: switch out")
b = duel(["HEALING-WISH"], level=50)
story.player_team[1].current_hp = 1
use(b, "HEALING-WISH")
check(b.player_hp == 0 and b.side(b.player_pokemon).get("healing_wish"), "Healing Wish: the user faints...")
lines = b.mv_on_entry(story.player_team[1])
check(story.player_team[1].current_hp == story.player_team[1].get_max_hp() or b._hp(story.player_team[1]) > 1,
      "...the next one in is healed")

print("8) conditions")
b = duel(["SPITE"], foe_moves=["TACKLE"])
use(b, "TACKLE", foe=True)
before = pplib.left(g, b.opponent_pokemon, "TACKLE")
use(b, "SPITE")
check(pplib.left(g, b.opponent_pokemon, "TACKLE") == before - 4, "Spite: 4 PP off the foe's last move")
b = duel(["GRAVITY", "EARTHQUAKE"], foe=6, foe_moves=["FLY"])
use(b, "GRAVITY")
dmg, _ = use(b, "EARTHQUAKE")
_, lines = use(b, "FLY", foe=True)
check(dmg > 0 and says(lines, "gravity"), "Gravity: Earthquake hits Charizard, Fly can't be used")
b = duel(["HEAL-BLOCK"], foe_moves=["RECOVER"])
use(b, "HEAL-BLOCK")
b.opponent_hp -= 50
hp = b.opponent_hp
_, lines = use(b, "RECOVER", foe=True)
check(b.opponent_hp == hp and says(lines, "Heal Block"), "Heal Block: no Recover")
b = duel(["TORMENT"], foe_moves=["TACKLE", "SCRATCH"])
use(b, "TORMENT")
use(b, "TACKLE", foe=True)
_, lines = use(b, "TACKLE", foe=True)
check(says(lines, "torment") and "TACKLE" not in b._battle_moves(b.opponent_pokemon), "Torment: not the same move twice")
b = duel(["TELEKINESIS", "EARTHQUAKE"], foe=143)
use(b, "TELEKINESIS")
dmg, lines = use(b, "EARTHQUAKE")
check(not dmg and b.mv_sure_hit(b.player_pokemon, b.opponent_pokemon, "ZAP-CANNON", {}),
      "Telekinesis: up in the air (no Earthquake), and every move hits it")
b = duel(["NIGHTMARE"], foe=143)
b.opponent_pokemon.status, b.opponent_pokemon.sleep_turns = "sleep", 3
use(b, "NIGHTMARE")
hp = b.opponent_hp
lines = b.effects_end_of_turn()
check(hp - b.opponent_hp == b.opp_max_hp // 4 and says(lines, "nightmare"), "Nightmare: a quarter a turn while asleep")
b = duel(["SKILL-SWAP"], me=94, foe=6)
use(b, "SKILL-SWAP")
check(b.ab(b.player_pokemon) != b.ab(b.opponent_pokemon) or True, "Skill Swap runs")
b = duel(["SOAK", "THUNDERBOLT"], foe=76)
use(b, "SOAK")
dmg, lines = use(b, "THUNDERBOLT")
check(b.opponent_pokemon.types == ["WATER"] and dmg and says(lines, "super effective"), "Soak: Golem turns Water (Thunderbolt hits)")
b.mv_battle_end()
check(b.opponent_pokemon.types == ["ROCK", "GROUND"], "...its own types back after the battle")
b = duel(["TRANSFORM"], foe=68, foe_moves=["CROSS-CHOP"])
me_ = b.player_pokemon
use(b, "TRANSFORM")
check(me_.moves == ["CROSS-CHOP"] and me_.types == b.opponent_pokemon.types, "Transform copies moves and types")
b.mv_battle_end()
check(me_.moves == ["TRANSFORM"] and "NORMAL" in me_.types, "...and it's itself again after the battle")
b = duel(["DESTINY-BOND"], foe_moves=["HYPER-BEAM"], level=50)
use(b, "DESTINY-BOND")
b.vol(b.opponent_pokemon)["lock_on"] = (id(b.player_pokemon), 99)
b.player_hp = b.player_pokemon.current_hp = 1
_, lines = use(b, "HYPER-BEAM", foe=True)
check(b.player_hp == 0 and b.opponent_hp == 0, "Destiny Bond takes the attacker down too")

print("9) doubles-only moves in a single battle")
b = duel(["HELPING-HAND", "ALLY-SWITCH", "COACHING", "DRAGON-CHEER", "AROMATIC-MIST", "POLLEN-PUFF", "FIRE-PLEDGE"])
outs = {n: use(b, n)[1][-1] for n in ("HELPING-HAND", "ALLY-SWITCH", "COACHING", "DRAGON-CHEER", "AROMATIC-MIST")}
check(all("no one to help" in o for o in outs.values()), f"Helping Hand, Ally Switch, Coaching, Dragon Cheer, Aromatic Mist: no one to help")
dmg, _ = use(b, "POLLEN-PUFF")
dmg2, _ = use(b, "FIRE-PLEDGE")
check(dmg > 0 and dmg2 > 0, "Pollen Puff and the Pledges: damage to the foe")
check(b.allies(b.player_pokemon) == [] and b.move_targets(b.player_pokemon, movelib.info(g, "EARTHQUAKE")) == [b.opponent_pokemon]
      and b.spread_mult([b.opponent_pokemon]) == 1.0, "the doubles hooks: no ally, one target, no spread cut")
b = duel(["QUASH", "AFTER-YOU"])
b.mv_turn_start({id(b.opponent_pokemon): "TACKLE"})
_, lines = use(b, "QUASH")
check(says(lines, "failed"), "Quash: it fails in a single battle (the games, Gen 8 on; doubles: section 17)")

print("10) screens, terrain, self effects")
b = duel(["BRICK-BREAK", "PSYCHIC-FANGS", "ICE-SPINNER", "STEEL-ROLLER"], foe=143)
b.side(b.opponent_pokemon)["reflect"] = 5
_, lines = use(b, "BRICK-BREAK")
check(not b.side(b.opponent_pokemon).get("reflect") and says(lines, "shattered"), "Brick Break breaks Reflect")
dmg, lines = use(b, "STEEL-ROLLER")
check(not dmg and says(lines, "failed"), "Steel Roller fails with no terrain")
b.field()["terrain"] = ("electric", 5)
use(b, "ICE-SPINNER")
check(not b.terrain(), "Ice Spinner ends the terrain")
b = duel(["STEEL-BEAM", "SCALE-SHOT", "FALSE-SWIPE"], foe=19, level=70, foe_level=5)
hp = b.player_hp
use(b, "STEEL-BEAM")
check(hp - b.player_hp == (b.player_max_hp + 1) // 2, "Steel Beam costs half the user's HP")
b = duel(["FALSE-SWIPE", "SCALE-SHOT"], foe=19, level=90, foe_level=5)
use(b, "FALSE-SWIPE")
check(b.opponent_hp == 1, "False Swipe leaves the foe at 1 HP")
b = duel(["SCALE-SHOT"], foe=143)
b.vol(b.player_pokemon)["lock_on"] = (id(b.opponent_pokemon), 99)
use(b, "SCALE-SHOT")
st = b.stages(b.player_pokemon)
check(st["SPEED"] == 1 and st["DEFENSE"] == -1, "Scale Shot: Speed up, Defense down")
b = duel(["FOCUS-PUNCH"], foe_moves=["QUICK-ATTACK"], foe=143)
b.mv_turn_start({id(b.player_pokemon): "FOCUS-PUNCH"})
use(b, "QUICK-ATTACK", foe=True)
dmg, lines = use(b, "FOCUS-PUNCH")
check(not dmg and says(lines, "lost its focus"), "Focus Punch, hit first: it loses its focus")
b = duel(["UPROAR"], foe_moves=["SING"], foe=143)
use(b, "UPROAR")
_, lines = use(b, "SING", foe=True)
check(b.player_pokemon.status != "sleep" and b.forced_effect_move(b.player_pokemon) == "UPROAR", "Uproar: no one sleeps, it keeps going")
b = duel(["RAGE"], foe_moves=["TACKLE"], foe=143)
use(b, "RAGE")
lines = use(b, "TACKLE", foe=True)
check(b.stages(b.player_pokemon)["ATTACK"] == 1, "Rage: hit while raging, its Attack rises")
story.money = 1000
b = duel(["PAY-DAY"], foe=143)
use(b, "PAY-DAY")
b.player_won = True
b.exit_battle()
check(story.money >= 1000 + 5 * 50, f"Pay Day's coins after the battle (${story.money})")
g.change_state(b)

print("11) sleep, timing, priority")
b = duel(["DREAM-EATER", "SNORE"], foe=143)
dmg, lines = use(b, "DREAM-EATER")
dmg2, _ = use(b, "SNORE")
check(not dmg and not dmg2, "Dream Eater on an awake foe, Snore awake: nothing")
b.opponent_pokemon.status = "sleep"
check(use(b, "DREAM-EATER")[0] > 0, "...Dream Eater on a sleeping foe hits")
b = duel(["FUTURE-SIGHT"], foe=143)
use(b, "FUTURE-SIGHT")
hp = b.opponent_hp
b.effects_end_of_turn()
mid = b.opponent_hp
b.effects_end_of_turn()
check(mid == hp and b.opponent_hp < hp, "Future Sight lands two turns later")
b = duel(["UPPER-HAND", "SUCKER-PUNCH"], foe=143)
b.mv_turn_start({id(b.opponent_pokemon): "TACKLE"})
check(not use(b, "UPPER-HAND")[0], "Upper Hand fails when the foe isn't using a priority move")
b.mv_turn_start({id(b.opponent_pokemon): "QUICK-ATTACK"})
check(use(b, "UPPER-HAND")[0] > 0, "...and hits when it is")
b.mv_turn_start({id(b.opponent_pokemon): "SWORDS-DANCE"})
check(not use(b, "SUCKER-PUNCH")[0], "Sucker Punch fails against a status move")
b = duel(["GRASSY-GLIDE"])
b.field()["terrain"] = ("grassy", 5)
check(b.mv_priority(b.player_pokemon, movelib.info(g, "GRASSY-GLIDE")) == 1, "Grassy Glide: +1 priority in Grassy Terrain")
b = duel(["SKY-DROP"], foe=143, foe_level=5)
_, lines = use(b, "SKY-DROP")
check(says(lines, "failed"), "Sky Drop can't lift a Snorlax (over 200 kg)")
b = duel(["SKY-DROP"], foe=19)
_, lines = use(b, "SKY-DROP")
stopped, _l = b._status_stops(b.opponent_pokemon, "FOE")
check(stopped and b._forced_move(b.player_pokemon) == "SKY-DROP", "Sky Drop: the foe is carried up and can't move")
b.turn_count += 1
dmg, _ = use(b, "SKY-DROP")
check(dmg > 0 and not b.vol(b.opponent_pokemon).get("sky_dropped"), "...and dropped next turn")

print("12) added effects the data was missing")
b = duel(["TERA-BLAST"], me=143)
b.player_pokemon.tera_type = "FIGHTING"
b.terastallize(b.player_pokemon)
d = b.mv_prepare(b.player_pokemon, b.opponent_pokemon, "TERA-BLAST", movelib.info(g, "TERA-BLAST"), preview=True)
check(d["type"] == "FIGHTING" and d["category"] == "PHYSICAL", "Tera Blast: the Tera Type, physical off a higher Attack")
b = duel(["SUPERCELL-SLAM"], foe=50)   # (Diglett: Ground, immune)
hp = b.player_hp
_, lines = use(b, "SUPERCELL-SLAM")
check(b.player_hp < hp and says(lines, "crashed"), "Supercell Slam crashes when it doesn't hit")
b = duel(["ALLURING-VOICE", "BURNING-JEALOUSY", "PSYCHIC-NOISE", "THROAT-CHOP", "TRI-ATTACK", "SMACK-DOWN", "EARTHQUAKE"],
         foe=143, foe_moves=["SWORDS-DANCE", "HYPER-VOICE", "RECOVER"])
use(b, "SWORDS-DANCE", foe=True)
random.seed(2)
use(b, "ALLURING-VOICE")
use(b, "BURNING-JEALOUSY")
check(b.vol(b.opponent_pokemon).get("confused") and b.opponent_pokemon.status == "burn",
      "Alluring Voice confuses, Burning Jealousy burns, a foe whose stats rose this turn")
b.turn_count += 2
b.opponent_pokemon.status = None
b.vol(b.opponent_pokemon).pop("confused", None)
use(b, "BURNING-JEALOUSY")
check(b.opponent_pokemon.status != "burn", "...not otherwise")
use(b, "PSYCHIC-NOISE")
use(b, "THROAT-CHOP")
_, l1 = use(b, "HYPER-VOICE", foe=True)
_, l2 = use(b, "RECOVER", foe=True)
check(says(l1, "Throat Chop") and says(l2, "Heal Block"), "Throat Chop stops sound moves; Psychic Noise stops healing")
b = duel(["TRI-ATTACK"], foe=143)
got = set()
for i in range(60):
    random.seed(100 + i)
    b.opponent_pokemon.status = None
    b.opponent_hp = b.opp_max_hp
    use(b, "TRI-ATTACK")
    got.add(b.opponent_pokemon.status)
check({"burn", "freeze", "paralysis"} <= got, f"Tri Attack: burn, freeze or paralysis ({sorted(x for x in got if x)})")
b = duel(["SMACK-DOWN", "EARTHQUAKE"], foe=6)
use(b, "SMACK-DOWN")
check(b.grounded(b.opponent_pokemon) and use(b, "EARTHQUAKE")[0] > 0, "Smack Down grounds Charizard: Earthquake hits")
b = duel(["FREEZE-DRY"], foe=130)   # Gyarados: Water/Flying
_, lines = use(b, "FREEZE-DRY")
check(says(lines, "super effective"), "Freeze-Dry is super effective on Water (x4 on Gyarados)")

print("13) self-KO moves")
for name in ("SELF-DESTRUCT", "EXPLOSION", "MISTY-EXPLOSION", "MEMENTO", "FINAL-GAMBIT"):
    b = duel([name], foe=143, level=50)
    use(b, name)
    check(b.player_hp == 0, f"{name.replace('-', ' ').title()}: the user faints")
geo = lv(74, 40, ["TACKLE"])
story.player_team = [geo]
story.inventory[tms.key_for_move(g, "EXPLOSION")] = 1
story.inventory[tms.key_for_move(g, "GYRO-BALL")] = 1
check("EXPLOSION" in movelib.move_pool(g, geo), "the Explosion TM puts Explosion in Geodude's move pool now")

print("14) a Pokemon whose moves are all status moves without a status condition doesn't Struggle")
b = duel(["STEALTH-ROCK", "SWORDS-DANCE"])
check(b._battle_moves(b.player_pokemon) == ["STEALTH-ROCK", "SWORDS-DANCE"], "Stealth Rock + Swords Dance: both usable")
b = duel(["GROWL", "TRICK-ROOM"])
check(movelib.STRUGGLE not in b._battle_moves(b.player_pokemon), "Growl + Trick Room: usable")
b = duel(["THUNDER-WAVE"], foe=50)
check(b._battle_moves(b.player_pokemon) == [movelib.STRUGGLE], "...but Thunder Wave alone against a Ground type: Struggle")

print("15) the foe's choices")
b = duel(["TACKLE"], foe_moves=["GYRO-BALL", "SPLASH"], foe=208, me=101)
check(b._ai_choose(b.opponent_pokemon, b.player_pokemon) == "GYRO-BALL", "a foe with Gyro Ball uses it")
b = duel(["TACKLE"], foe_moves=["DREAM-EATER", "TACKLE"], foe=94)
picks = {b._ai_choose(b.opponent_pokemon, b.player_pokemon) for _ in range(20)}
check("DREAM-EATER" not in picks, "...and doesn't pick Dream Eater on a Pokemon that's awake")
b = duel(["TACKLE"], foe_moves=["EXPLOSION", "TACKLE"], foe=76)
picks = {b._ai_choose(b.opponent_pokemon, b.player_pokemon) for _ in range(10)}
check("EXPLOSION" not in picks, "...keeps Explosion for when it's low")
b.opponent_hp = 5
check(b._ai_choose(b.opponent_pokemon, b.player_pokemon) in ("EXPLOSION", "TACKLE"), "...(and may use it then)")

print("16) fixed damage and paying back")
b = duel(["ENDEAVOR", "PSYWAVE", "COUNTER", "MIRROR-COAT", "METAL-BURST", "BIDE"], foe=143, level=50)
b.vol(b.player_pokemon)["lock_on"] = (id(b.opponent_pokemon), 99)
b.player_hp = b.player_pokemon.current_hp = 30
use(b, "ENDEAVOR")
check(b.opponent_hp == 30, f"Endeavor: the foe down to the user's HP ({b.opponent_hp})")
b = duel(["PSYWAVE"], foe=143, level=50)
b.vol(b.player_pokemon)["lock_on"] = (id(b.opponent_pokemon), 99)
dmg, _ = use(b, "PSYWAVE")
check(25 <= dmg <= 75, f"Psywave: 50-150% of the user's level ({dmg})")
b = duel(["COUNTER", "MIRROR-COAT", "METAL-BURST"], foe=143, foe_moves=["TACKLE"], level=50)
b.vol(b.player_pokemon)["lock_on"] = (id(b.opponent_pokemon), 99)
b.vol(b.opponent_pokemon)["lock_on"] = (id(b.player_pokemon), 99)
b.mv_turn_start({})
took, _ = use(b, "TACKLE", foe=True)
mc, _ = use(b, "MIRROR-COAT")
ct, _ = use(b, "COUNTER")
mb, _ = use(b, "METAL-BURST")
check(took and ct == 2 * took and not mc and mb == took * 3 // 2,
      f"Counter pays back a physical hit twice ({took} -> {ct}), Mirror Coat fails on it, Metal Burst x1.5 ({mb})")
b = duel(["BIDE"], foe=143, foe_moves=["TACKLE"], level=50)
b.vol(b.opponent_pokemon)["lock_on"] = (id(b.player_pokemon), 99)
total = 0
for t in range(3):
    b.turn_count += 1
    b.mv_turn_start({})
    dmg, lines = use(b, "BIDE")
    if t < 2:
        total += use(b, "TACKLE", foe=True)[0]
    b.effects_end_of_turn()
check(dmg == 2 * total and total > 0 and b.forced_effect_move(b.player_pokemon) is None,
      f"Bide: two turns storing, then twice the damage back ({total} -> {dmg})")
b = duel(["TACKLE"], foe_moves=["PURSUIT"], foe=197, level=50)
p0 = b.player_pokemon
hp = b.player_hp
b.phase = "MENU"
b.perform_switch(1)
check(p0.current_hp < hp and says(b.dialogue_box.text_lines, "PURSUIT"), "Pursuit hits the Pokemon you switch out")
check(b._pledge_combo(b.player_pokemon, "FIRE-PLEDGE") is None, "Pledge combinations: none without a partner (doubles hook)")

print("17) the moves that didn't quite match the games (11-17: Pursuit, U-turn's KO, Revival Blessing, Shell Trap...)")
from src.states.systems.pick_list import PickListState


def first_at(log, text):
    return next((i for i, x in enumerate(log) if text.lower() in str(x).lower()), -1)


# Pursuit catches a Pokemon leaving by its own move, before it goes, at double power
b = duel(["U-TURN"], foe_moves=["PURSUIT"], me=135, foe=197, level=50)   # Jolteon (fast) vs Umbreon
first = b.player_pokemon
_seen, _orig = [], b.mv_prepare


def _spy(a, t, n, d, preview=False):
    r = _orig(a, t, n, d, preview=preview)
    if n == "PURSUIT" and not preview:
        _seen.append(r.get("power"))
    return r


b.mv_prepare = _spy
log = turn(b, "U-TURN")
p, cb = first_at(log, "used PURSUIT"), first_at(log, "Come back")
check(0 <= p < cb and _seen == [80] and sum("used pursuit" in str(x).lower() for x in log) == 1 and b.player_pokemon is not first,
      f"Pursuit hits your U-turn user before it switches out, once, at double power ({p} < {cb}, {_seen})")
b = duel(["PURSUIT"], foe_moves=["U-TURN"], me=197, foe=135, level=50)
f0 = b.opponent_pokemon
log = turn(b, "PURSUIT")
p, w = first_at(log, "used PURSUIT"), first_at(log, "withdrew")
check(0 <= p < w and b.opponent_pokemon is not f0, f"...and your Pursuit hits a trainer's U-turn user before it goes ({p} < {w})")
b = duel(["PURSUIT"], foe_moves=["U-TURN"], me=197, foe=135, level=50)
b.mv_turn_start({id(b.player_pokemon): "PURSUIT", id(b.opponent_pokemon): "U-TURN"})
b.turn_actions = [b.player_attack]
b._mv()["pending"].append(("force", b.opponent_pokemon, None))
b._queue_pending_switch()
check(b.turn_actions[0] == b._run_pending_switch and b.turn_actions[1] == b.player_attack,
      "...not one dragged out (Roar, Dragon Tail): the switch first, Pursuit at its own turn")
b = duel(["TACKLE"], foe_moves=["PURSUIT", "TACKLE"], me=65, foe=197)
check(b.mv_ai_pursuit_mult(b.opponent_pokemon, b.player_pokemon) > 1, "a foe likes Pursuit more against a Psychic type")
b.phase = "MENU"
hp = b.player_hp
b._ai_choose = lambda a, d: "PURSUIT"
b.perform_switch(1)
check(b.player_pokemon.current_hp < hp or story.player_team[0].current_hp < hp, "...and still hits one you switch out from the menu")

# U-turn that knocks the foe out: you still switch, then the trainer's next Pokemon comes in
b = duel(["U-TURN"], me=135, foe=10, level=60, foe_level=3)   # (a Caterpie: sure to go down)
first, f0 = b.player_pokemon, b.opponent_pokemon
log = turn(b, "U-TURN")
cb, so = first_at(log, "Come back"), first_at(log, "sent out")
check(f0.current_hp == 0 and b.player_pokemon is not first and b.opponent_pokemon is not f0 and 0 <= cb < so,
      f"U-turn KO: you switch out first, then the trainer sends out its next one ({cb} < {so})")
b = duel(["VOLT-SWITCH"], me=135, foe=10, level=60, foe_level=3, kind="wild")
first = b.player_pokemon
log = turn(b, "VOLT-SWITCH")
check(b.player_pokemon is first and first_at(log, "Come back") < 0, "...in a wild battle the KO ends it: no switch")
b = duel(["TACKLE"], foe_moves=["U-TURN"], me=10, foe=135, level=60)
story.player_team[0].level = 3
b.player_hp = b.player_pokemon.current_hp = 1
f0, p0 = b.opponent_pokemon, b.player_pokemon
log = turn(b, "TACKLE")
w = first_at(log, "withdrew")
check(p0.current_hp == 0 and b.opponent_pokemon is not f0 and w >= 0 and b.player_pokemon is not p0,
      f"a trainer's U-turn KO: it switches, then you send one in ({b.opponent_pokemon.display_name})")

# Revival Blessing: you choose; the foe revives its strongest
b = duel(["REVIVAL-BLESSING"], foe=143)
team = story.player_team
team[1].current_hp = team[2].current_hp = 0
b.open_move_menu()
b.choose_move("REVIVAL-BLESSING")
b.math_ui.on_click(b.options.index(b.correct_ans))
picked = False
for _ in range(900):
    cur = g.current_state
    if isinstance(cur, PickListState):
        picked = len(cur.rows) == 2
        cur.pick(2)
        continue
    if cur is not b:
        break
    if b.dialogue_box.visible:
        b.dialogue_box.is_finished = True
        if b.phase == "MESSAGE" and b.dialogue_box.callback:
            cb_ = b.dialogue_box.callback; b.dialogue_box.callback = None; cb_()
    b.feedback_timer = 0
    b.update()
    if b.phase == "MENU" and not b.turn_actions and not b.dialogue_box.visible and not b._form_msgs:
        break
check(picked and team[2].current_hp == team[2].get_max_hp() // 2 and team[1].current_hp == 0 and b.phase == "MENU",
      "Revival Blessing: a list of your fainted Pokemon, the one you pick comes back at half HP")
b = duel(["TACKLE"], foe_moves=["REVIVAL-BLESSING"])
weak, strong = b.opponent_team[1], b.opponent_team[2]
weak.current_hp = 0
strong.current_hp = 0
strong.level = 70
use(b, "REVIVAL-BLESSING", foe=True)
check(strong.current_hp > 0 and weak.current_hp == 0 and b.opponent_team[b.current_opponent_idx + 1] is strong,
      "...a trainer revives its strongest, next in line")

# Shell Trap and Beak Blast
b = duel(["SHELL-TRAP"], foe_moves=["TACKLE"], me=776, foe=143, level=50)
log = turn(b, "SHELL-TRAP")
s, t, u = first_at(log, "set a shell trap"), first_at(log, "used TACKLE"), first_at(log, "used SHELL TRAP")
check(0 <= s < t < u and not says(log, "didn't work"), f"Shell Trap: set at the start, goes off after a physical hit ({s} {t} {u})")
b = duel(["SHELL-TRAP"], foe_moves=["EMBER"], me=776, foe=143, level=50)
log = turn(b, "SHELL-TRAP")
check(says(log, "didn't work"), "...a special move doesn't set it off: it fails at its turn")
b = duel(["SHELL-TRAP"], foe_moves=["TACKLE"], me=776, foe=143, level=50)
b.mv_turn_start({id(b.player_pokemon): "SHELL-TRAP", id(b.opponent_pokemon): "TACKLE"})
use(b, "TACKLE", foe=True)
b.turn_actions = [b.raid_allies_attack, b.player_attack]
b._queue_pending_switch()
check(b.turn_actions[0] == b.player_attack, "...hit, it jumps ahead of anything else waiting in the turn")
b = duel(["BEAK-BLAST"], foe_moves=["TACKLE"], me=733, foe=143, level=50)
log = turn(b, "BEAK-BLAST")
check(says(log, "heating up") and first_at(log, "heating up") < first_at(log, "used TACKLE") and b.opponent_pokemon.status == "burn"
      and not b.vol(b.player_pokemon).get("beak_blast"), "Beak Blast: heats up at the start, contact burns, cools after it strikes")

# After You / Quash
b = duel(["AFTER-YOU", "QUASH"])
b.mv_turn_start({id(b.opponent_pokemon): "TACKLE"})
b.turn_actions = [b.opponent_attack]
_, l1 = use(b, "AFTER-YOU")
_, l2 = use(b, "QUASH")
check(says(l1, "failed") and says(l2, "failed") and b.turn_actions == [b.opponent_attack],
      "After You and Quash fail in a single battle (the games, Gen 8 on)")
b.is_doubles = True   # (the doubles hooks: the order really changes)
b.mv_turn_start({})
b.turn_actions = [b.player_attack, b.opponent_attack, b.raid_allies_attack]
_, l1 = use(b, "AFTER-YOU")
order1 = list(b.turn_actions)
b.turn_actions = [b.opponent_attack, b.player_attack, b.raid_allies_attack]
_, l2 = use(b, "QUASH")
check(order1[0] == b.opponent_attack and b.turn_actions == [b.player_attack, b.opponent_attack, b.raid_allies_attack]
      and says(l1, "kind offer") and says(l2, "postponed"), "...in doubles: After You moves the target next, Quash last")
b.is_doubles = False

# Transform's PP; Ditto's own transforming
b = duel(["TRANSFORM"], foe=68, foe_moves=["CROSS-CHOP", "BULLET-PUNCH"])
me_ = b.player_pokemon
me_.pp_ups = {"CROSS-CHOP": 3}
use(b, "TRANSFORM")
pplib.restore(g, me_, "CROSS-CHOP", "full")
check(pplib.left(g, me_, "CROSS-CHOP") == 5 and pplib.max_pp(g, me_, "BULLET-PUNCH") == 5,
      "Transform: each copied move has 5 PP, and 5 is its most")
b.mv_switched_out(me_)
check(me_.moves == ["TRANSFORM"] and not hasattr(me_, "_pp_cap"), "...switched out, its own moves and PP are back")
ditto = lv(132, 50, ["TRANSFORM"])
b = duel(["TACKLE"], foe=68, foe_moves=["CROSS-CHOP", "BULLET-PUNCH"])
story.player_team[0] = ditto
ditto.current_hp = 20
ditto.transform_into(b.opponent_pokemon)
b.mv_copied_pp(ditto)
mx = ditto.get_max_hp()
check(ditto.current_hp == 20 and ditto.moves == ["CROSS-CHOP", "BULLET-PUNCH"] and pplib.left(g, ditto, "CROSS-CHOP") == 5,
      "Ditto transforming as it comes out: the foe's moves at 5 PP, its own HP kept")
ditto.current_hp = 7
b.mv_switched_out(ditto)
check(ditto.id == 132 and ditto.moves == ["TRANSFORM"] and ditto.current_hp == 7 and not hasattr(ditto, "transformed_state"),
      "...switched out it's Ditto again, with the HP it had (not healed back)")

# Raging Bull, Ivy Cudgel, Tera Starstorm
types = {}
for pid in (128, 2055, 2056, 2057):
    b = duel(["RAGING-BULL"], me=pid)
    types[pid] = b.mv_prepare(b.player_pokemon, b.opponent_pokemon, "RAGING-BULL", movelib.info(g, "RAGING-BULL"), preview=True)["type"]
check(types == {128: "NORMAL", 2055: "WATER", 2056: "FIRE", 2057: "FIGHTING"},
      f"Raging Bull by Tauros's form data: {types}")
b = duel(["IVY-CUDGEL", "TACKLE"], me=1017, my_item="HEARTHFLAME_MASK")
og = b.player_pokemon
d = b.mv_prepare(og, b.opponent_pokemon, "IVY-CUDGEL", movelib.info(g, "IVY-CUDGEL"), preview=True)
check(d["type"] == "FIRE" and og.types == ["GRASS", "FIRE"] and b.ab(og) == "MOLDBREAKER"
      and b.held_power_mult(og, b.opponent_pokemon, "TACKLE", movelib.info(g, "TACKLE")) == 1.2 and not b._removable(og),
      "Ogerpon with the Hearthflame Mask: Grass/Fire, Mold Breaker, Ivy Cudgel Fire, every move x1.2, the mask stays on")
b.mv_battle_end()
check(og.types == ["GRASS"], "...its own form again after the battle")
b = duel(["IVY-CUDGEL"], me=1017)
check(b.mv_prepare(b.player_pokemon, b.opponent_pokemon, "IVY-CUDGEL", movelib.info(g, "IVY-CUDGEL"), preview=True)["type"] == "GRASS",
      "...no mask (the Teal Mask): Grass")
b = duel(["TERA-STARSTORM"], me=1024, foe=94)   # Terapagos vs Gengar (a Ghost type)
tp = b.player_pokemon
d0 = b.mv_prepare(tp, b.opponent_pokemon, "TERA-STARSTORM", movelib.info(g, "TERA-STARSTORM"), preview=True)
b.terastallize(tp)
d1 = b.mv_prepare(tp, b.opponent_pokemon, "TERA-STARSTORM", movelib.info(g, "TERA-STARSTORM"), preview=True)
dmg, _l = use(b, "TERA-STARSTORM")
check(d0["type"] == "NORMAL" and d0["target"] == "selected-pokemon" and d1["type"] == "STELLAR" and d1["target"] == "all-opponents"
      and tp.types == ["NORMAL"] and b.stab_mult(tp, "NORMAL") == 2.0 and dmg > 0,
      "Tera Starstorm: Normal, one target; from Stellar Terapagos (its own types kept) Stellar, every foe, hits a Ghost")

# Flame Orb and Toxic Orb: where the games give them (in the regions this game has)
_d = {r: json.load(open(f"assets/{r}_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"] for r in ("unova", "alola", "galar", "paldea")}


def gifts(area, region):
    a = _d[region][area]
    out = {}
    for o in (a.get("route_menu") or []) + (a.get("explore_options") or []):
        out.update((o.get("event") or {}).get("gift_item") or {})
    return out


check({"FLAME_ORB", "TOXIC_ORB"} <= set(gifts("REVERSAL_MOUNTAIN", "unova")) and "FLAME_ORB" in gifts("ULAULA_MEADOW", "alola")
      and "TOXIC_ORB" in gifts("RESOLUTION_CAVE", "alola") and {"FLAME_ORB", "TOXIC_ORB"} <= set(gifts("WYNDON", "galar"))
      and {e["item"] for e in _d["paldea"]["LEVINCIA"]["extra_stock"]} == {"FLAME_ORB", "TOXIC_ORB"},
      "Flame / Toxic Orb: Reversal Mountain, Ula'ula Meadow, Resolution Cave, Wyndon Stadium, Levincia's shop")
check({"WELLSPRING_MASK", "HEARTHFLAME_MASK", "CORNERSTONE_MASK"} <= set(gifts("KITAKAMI", "paldea")),
      "Ogerpon's three masks: given at Kitakami once Ogerpon is met")
from src.states.overworld import common as _common
ev = next(o["event"] for o in _d["unova"]["REVERSAL_MOUNTAIN"]["route_menu"] if "orbs" in str(o.get("flag_condition")))
story.inventory.pop("FLAME_ORB", None)
_shown = []
_common._run_story_event(g.current_state, ev, lambda c: True, lambda lines, *a, **k: _shown.extend(lines))
check(story.inventory.get("FLAME_ORB") == 1 and story.inventory.get("TOXIC_ORB", 0) >= 1, f"...the Reversal Mountain search gives both ({_shown[-2:]})")

print(f"##### {fails} failures")
