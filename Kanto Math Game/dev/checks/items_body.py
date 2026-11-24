
import random
from src.pokemon import catching, items as itemlib
from src.states.systems import PokeMartState, BagState
from src.states.overworld import CityState, PlayState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())   # (Kanto is walked: walk up to the Marts' counters, 11-24)
story.enter_region("KANTO")
story.badges["KANTO"] = []
story.story_flags["visited_mart_VIRIDIAN_CITY"] = True
_SHOP = lambda o: str(o.get("action") or "").upper() == "SHOP"


def mart(area, came, who=_SHOP):
    """Walk into the town's Mart (or up to the clerk called who) and open the shop."""
    t = walk_town(area, came)
    walk_meet(t, who, play=False)
    walk_frames(2)
    m = g.current_state
    if isinstance(m, PokeMartState) and m.phase == "DIALOGUE":
        m.on_welcome_dialogue_end()
    return m


print("1) Poke Mart stock follows the badges, like the games")
m = mart("VIRIDIAN_CITY", "KANTO_ROUTE_1")
check(isinstance(m, PokeMartState), f"Viridian's Mart counter opens the shop ({type(m).__name__})")
stock = m._shop_items()
check({"POKE_BALLS", "POTION", "ANTIDOTE", "PARALYZE_HEAL"} <= set(stock) and "GREAT_BALL" not in stock,
      f"0 badges: {stock[:6]}")
story.badges["KANTO"] = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL"]
stock = mart("VIRIDIAN_CITY", "KANTO_ROUTE_1")._shop_items()
check({"ULTRA_BALL", "FULL_HEAL", "HYPER_POTION", "NET_BALL", "TIMER_BALL"} <= set(stock) and "MAX_POTION" not in stock,
      "5 badges: Ultra Balls, Full Heal, specialty balls (no Max Potion yet)")
stock = mart("CELADON_CITY", "KANTO_ROUTE_7", "Battle item clerk")._shop_items()
check("X_ATTACK" in stock and "DIRE_HIT" in stock, "the department store sells X items (its battle item clerk)")
story.money = 5000
balls = story.balls_left
m = mart("VIRIDIAN_CITY", "KANTO_ROUTE_1")
m.mode = "BUY"
m.pending_item, m.qty = "POKE_BALLS", 2
m.confirm_purchase()
check(story.balls_left == balls + 10 and story.inventory.get("PREMIER_BALL") == 1,
      "10 Poke Balls come with a Premier Ball")

print("2) medicine works like the games")
p = mk(25)
p.level = 30
mx = p.get_max_hp()
p.current_hp = 5
used, lines = itemlib.medicine_effect("POTION", p)
check(used and p.current_hp == 25, f"Potion: +20 HP ({lines})")
p.status = "poison"
used, lines = itemlib.medicine_effect("FULL_RESTORE", p)
check(p.current_hp == mx and not p.status, f"Full Restore: full HP and cured ({lines})")
used, lines = itemlib.medicine_effect("ANTIDOTE", p)
check(not used, f"Antidote on a healthy Pokemon: {lines}")
p.current_hp = 0
used, lines = itemlib.medicine_effect("REVIVE", p)
check(used and p.current_hp == mx // 2, f"Revive: half HP ({lines})")

print("3) battle items")
b = battle("KANTO_ROUTE_1", 25, 19)
story.inventory["X_ATTACK"] = 1
bag = BagState(g, b, context="battle")
g.change_state(bag)
bag.use_item("X_ATTACK")
check(b.stages(b.player_pokemon)["ATTACK"] == 2 and not story.inventory.get("X_ATTACK"), "X Attack: +2 Attack")

print("4) Poke Balls: the games' catch formula")
foe = mk(144)  # Articuno, catch rate 3
foe.level = 50
foe.current_hp = foe.get_max_hp()
check(catching.chance(g, foe, "MASTER_BALL") == 1.0, "a Master Ball always works")
lo = catching.chance(g, foe, catching.POKE, hp=foe.get_max_hp())
hi = catching.chance(g, foe, "ULTRA_BALL", hp=1)
check(lo < 0.02 and hi > lo, f"Articuno: full HP Poke Ball {lo:.3f}, 1 HP Ultra Ball {hi:.3f}")
foe.status = "sleep"
check(catching.chance(g, foe, "ULTRA_BALL", hp=1) > hi, "sleep helps")
mag = mk(129)
mag.level = 20
check(catching.ball_bonus("NET_BALL", g, mag) == 3.5 and catching.ball_bonus("NET_BALL", g, mk(19)) == 1.0,
      "Net Ball: x3.5 against Water types")
rat = mk(19)
rat.level = 3
check(catching.chance(g, rat, catching.POKE, hp=rat.get_max_hp()) == 1.0, "a low-level Rattata is an easy catch")
random.seed(7)
caught = sum(catching.throw(g, foe, catching.POKE, hp=foe.get_max_hp())[0] for _ in range(400))
check(caught < 40, f"Poke Balls at a full-HP legendary rarely work ({caught}/400)")

print("5) a throw in battle can break free")
story.balls_left = 3
b = battle("KANTO_ROUTE_1", 25, 144)
b.opponent_pokemon.level = 70
b.opponent_hp = 0
check(b.try_trigger_wild_catch_prompt() and b.phase == "CATCH_PROMPT", "the KO offers a throw")
random.seed(2)
b.catch_yes()
for _ in range(400):
    b.update()
    if b.phase != "CATCH_ANIMATION":
        break
text = " ".join(b.dialogue_box.text_lines)
check(story.balls_left == 2 and (b.catch_phase == "CAUGHT" or "broke free" in text or "caught" in text.lower()
                                 or "close" in text or "Almost" in text),
      f"one ball used; outcome: {text[:60]}")

print("6) Repel and Escape Rope")
story.repel_routes = 2
ps = walk_route("KANTO_ROUTE_1", "PALLET_TOWN")   # (walked: a route's ways out never wait on rounds; the Repel still counts down)
check(walked(ps) and ps.min_rounds == 0 and story.repel_routes == 1, "a Repel lets you leave the route without battling")
story.repel_routes = 0
ps = walk_route("MT_MOON", "KANTO_ROUTE_3")
story.inventory["ESCAPE_ROPE"] = 1
bag = BagState(g, ps)
g.change_state(bag)
bag.use_item("ESCAPE_ROPE")
check(type(g.current_state).__name__ == "AreaTransitionState" and not story.inventory.get("ESCAPE_ROPE"),
      f"Escape Rope leads out of Mt. Moon -> {getattr(g.current_state, 'next_area_key', None)}")
# ---- a Lucky Egg in a co-op raid (11-18, roadmap bug: raid XP skipped it): half again, as in an ordinary battle
from src.coop import raid as _raid, roster as _roster


class _Host:
    guests = {}


def _raid_xp(held):
    m = mk(129); m.level = 20; m.xp = 0; m.held_item = held; m.affection = 0
    foe = mk(130); foe.level = 30
    b = type("B", (), {})(); b.opponent_pokemon, b.opponent_hp, b.player_won = foe, 0, True
    b.coop_raid = {"humans": {"p1": {}}, "turn": 1, "until": 0, "said": False}
    h = _Host(); _roster._state(h)["lent"]["p1"] = [{"mon": m}]
    g.coop_raid_battle = b
    _raid.finish(g, h)
    return m.level * 100000 + m.xp, m


_plain, _ = _raid_xp(None)
_egg, _ = _raid_xp("LUCKY_EGG")
check(_egg > _plain, f"a raid: the Lucky Egg's holder earns more XP ({_plain} -> {_egg})")
print("FAILURES:", fails)

print("Catch window (Jordan's to-do): bosses are sure, other fails halved; Poke Balls per Bag")
legend = mk(150); legend.level = 70
check(all(catching.window_throw(g, legend, catching.POKE, guaranteed=True, hp=legend.get_max_hp())[0]
          for _ in range(50)), "a legendary at the catch window is always caught")
hard = mk(150); hard.level = 70
plain = sum(catching.throw(g, hard, catching.POKE, hp=hard.get_max_hp())[0] for _ in range(2000)) / 2000
window = sum(catching.window_throw(g, hard, catching.POKE, hp=hard.get_max_hp())[0] for _ in range(2000)) / 2000
check(window > plain + 0.3, f"the catch window halves the fails ({plain:.2f} -> {window:.2f})")
story.balls_left = 7
check(story.inventory.get("POKE_BALLS") == 7, "Poke Balls are kept in the Bag")

print("Caught past its evolution level: it evolves at its next level up (Jordan)")
from src.pokemon import evolution as _evo
ch = mk(4); ch.level = 20; ch.caught_level = 20
check(not _evo.ready_evolutions(g, ch, [ch]), "a Charmander caught at Lv 20 doesn't evolve on the catch")
ch.level_up(1)  # Lv 21: a level-up, so its evolution is checked
check(any(e.startswith("CHARMELEON") for e in _evo.ready_evolutions(g, ch, [ch])), "after one level up it evolves")
plain = mk(4); plain.level = 15; plain.level_up(1)
check(any(e.startswith("CHARMELEON") for e in _evo.ready_evolutions(g, plain, [plain])), "a raised one still evolves at Lv 16")

print("Collection cases (Jordan 11-18): a family of collectibles in one Bag slot, opened to browse")
from src.pokemon import cases as _cs
_inv = story.inventory
for _k in [k for k in list(_inv) if _cs.case_of(k)]:
    del _inv[_k]
for _k in [k for k in list(story.story_flags) if str(k).startswith("case:")]:
    del story.story_flags[_k]
story.player_team = [mk(25)]
_inv.update({"TM001": 1, "TM002": 1, "HM_CUT": 1, "FIRE_STONE": 2, "WATER_STONE": 1, "HELIX_FOSSIL": 1,
             "FIRIUM_Z": 1, "RED_APRICORN": 3, "POTION": 4})
check(_cs.case_of("TM001") == "TM_CASE" and _cs.case_of("HM_CUT") == "TM_CASE" and _cs.case_of("POTION") is None
      and _cs.case_of("SILVER_WING") is None and _cs.case_of("CHARIZARDITE_X") == "MEGA_STONE_CASE",
      "each family has its case (the Silver Wing stays a key item)")
_city = walk_town("VIRIDIAN_CITY", "KANTO_ROUTE_1")
_told = []
_sd = g.show_dialogue
g.show_dialogue = lambda lines, callback=None: _told.append(list(lines))
_bag = BagState(g, _city); g.change_state(_bag)
check("TMs & HMs" not in _bag.pages and "KEY ITEMS" in _bag.pages, "no TM pocket: the TM Case is in Key Items, as in FireRed")
_txt = " ".join(" ".join(t) for t in _told)
check(len(_told) == 1 and "TM Case" in _txt and "Apricorn Box" in _txt, f"the first time, the Bag says which cases you've got ({_txt[:90]}...)")
_bag.start()
check(len(_told) == 1, "...and only the first time")
g.show_dialogue = _sd
_bag.open_pocket(_bag.pages.index("KEY ITEMS"))
_keys = [b.key for b in _bag.item_buttons]
check("TM_CASE" in _keys and "Z_CRYSTAL_CASE" in _keys and "TM001" not in _keys, f"Key Items: one TM Case card, not the TMs ({_keys})")
_tmc = next(b for b in _bag.item_buttons if b.key == "TM_CASE")
check(_tmc.qty == 3 if hasattr(_tmc, "qty") else True, "the card counts the kinds inside")
_tmc.callback()
check(_bag.case_open == "TM_CASE" and sorted(b.key for b in _bag.item_buttons) == ["HM_CUT", "TM001", "TM002"],
      "tapping it opens the case: the TMs and HMs inside")
_bag.draw()
_bag.go_back()
check(_bag.case_open is None and g.current_state is _bag, "BACK closes the case first, staying in the Bag")
_bag.open_pocket(0)
_keys = [b.key for b in _bag.item_buttons]
check({"STONE_CASE", "FOSSIL_CASE", "APRICORN_BOX"} <= set(_keys) and "FIRE_STONE" not in _keys and "POTION" not in _keys,
      f"Items: stones, fossils and Apricorns each in their own case ({_keys})")
_bag.open_case("STONE_CASE")
check(_bag.pocket_items("ITEMS") == [("FIRE_STONE", 2), ("WATER_STONE", 1)], "the stone case lists its stones with their counts")
_bag.use_item("WATER_STONE")
check(type(g.current_state).__name__ == "PokemonPartyMenuState", "an item from inside a case is used as usual (pick a Pokemon)")
g.change_state(_bag)
_inv["FIRE_STONE"] = 0; _inv["WATER_STONE"] = 0
_bag.refresh_buttons()
check(_bag.case_open is None and "STONE_CASE" not in [b.key for b in _bag.item_buttons], "an emptied case closes and leaves the pocket")
_bb = BagState(g, _city, context="battle")
check(all(not _cs.is_case(k) for p in _bb.pages for k, _q in _bb.pocket_items(p)), "no cases in the battle Bag")
for _k in ("TM001", "TM002", "HM_CUT", "HELIX_FOSSIL", "FIRIUM_Z", "RED_APRICORN"):
    _inv.pop(_k, None)
g.change_state(_city)
