
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
story.current_area_key = "VIRIDIAN_CITY"
story.badges["KANTO"] = []
story.story_flags["visited_mart_VIRIDIAN_CITY"] = True

print("1) Poke Mart stock follows the badges, like the games")
m = PokeMartState(g, None)
stock = m._shop_items()
check({"POKE_BALLS", "POTION", "ANTIDOTE", "PARALYZE_HEAL"} <= set(stock) and "GREAT_BALL" not in stock,
      f"0 badges: {stock[:6]}")
story.badges["KANTO"] = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL"]
stock = PokeMartState(g, None)._shop_items()
check({"ULTRA_BALL", "FULL_HEAL", "HYPER_POTION", "NET_BALL", "TIMER_BALL"} <= set(stock) and "MAX_POTION" not in stock,
      "5 badges: Ultra Balls, Full Heal, specialty balls (no Max Potion yet)")
story.current_area_key = "CELADON_CITY"
stock = PokeMartState(g, None)._shop_items()
check("X_ATTACK" in stock and "DIRE_HIT" in stock, "the department store sells X items")
story.money = 5000
balls = story.balls_left
m = PokeMartState(g, None)
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
story.current_area_key = "KANTO_ROUTE_1"
ps = PlayState(g)
check(ps.min_rounds == 0 and story.repel_routes == 1, "a Repel lets you leave the route without battling")
story.repel_routes = 0
story.current_area_key = "MT_MOON"
story.inventory["ESCAPE_ROPE"] = 1
bag = BagState(g, ps)
g.change_state(bag)
bag.use_item("ESCAPE_ROPE")
check(type(g.current_state).__name__ == "AreaTransitionState" and not story.inventory.get("ESCAPE_ROPE"),
      f"Escape Rope leads out of Mt. Moon -> {getattr(g.current_state, 'next_area_key', None)}")
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
ch.level = 21
check(any(e.startswith("CHARMELEON") for e in _evo.ready_evolutions(g, ch, [ch])), "after one level up it evolves")
plain = mk(4); plain.level = 16
check(any(e.startswith("CHARMELEON") for e in _evo.ready_evolutions(g, plain, [plain])), "a raised one still evolves at Lv 16")
