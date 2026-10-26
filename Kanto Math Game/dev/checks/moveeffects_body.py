
import random
from src.pokemon import moves as movelib
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
random.seed(3)


def fresh(me=4, foe=19, lv=30):
    b = battle("KANTO_ROUTE_1", me, foe)
    b.player_pokemon.level = b.opponent_pokemon.level = lv
    b.player_hp = b.player_max_hp = b.player_pokemon.get_max_hp()
    b.opponent_hp = b.opp_max_hp = b.opponent_pokemon.get_max_hp()
    return b


def use(b, name, foe=False):
    me, them = (b.opponent_pokemon, b.player_pokemon) if foe else (b.player_pokemon, b.opponent_pokemon)
    mx = b.player_max_hp if foe else b.opp_max_hp
    hp = b.player_hp if foe else b.opponent_hp
    return b._use_move(me, them, name, "ME", "FOE", mx, hp)


print("1) stat moves")
b = fresh()
_, lines, _ = use(b, "GROWL")
check(b.stages(b.opponent_pokemon)["ATTACK"] == -1 and any("Attack fell" in l for l in lines), f"Growl: {lines[-1]}")
_, lines, _ = use(b, "SWORDS-DANCE")
check(b.stages(b.player_pokemon)["ATTACK"] == 2 and "rose sharply" in lines[-1], f"Swords Dance: {lines[-1]}")
for _ in range(3):
    use(b, "SWORDS-DANCE")
_, lines, _ = use(b, "SWORDS-DANCE")
check("won't go any higher" in lines[-1], f"capped at +6: {lines[-1]}")
random.seed(1)
base = [b._calculate_damage(b.player_pokemon, b.opponent_pokemon, 80, 1.0, category="PHYSICAL", move_type="NORMAL")
        for _ in range(20)]
b.stages(b.player_pokemon)["ATTACK"] = 0
plain = [b._calculate_damage(b.player_pokemon, b.opponent_pokemon, 80, 1.0, category="PHYSICAL", move_type="NORMAL")
         for _ in range(20)]
check(sum(base) > 2.5 * sum(plain), f"+6 Attack hits much harder ({sum(base)} vs {sum(plain)})")

print("2) added effects of hits")
b = fresh()
dmg, lines, _ = use(b, "CLOSE-COMBAT")
check(b.stages(b.player_pokemon)["DEFENSE"] == -1 and b.stages(b.player_pokemon)["SPDEF"] == -1,
      f"Close Combat lowers the user's defenses: {lines[-2:]}")
b = fresh()
use(b, "CONFUSE-RAY")
check(b.vol(b.opponent_pokemon).get("confused"), "Confuse Ray confuses")
b = fresh()
use(b, "WRAP")
check(b.vol(b.opponent_pokemon).get("trapped"), "Wrap traps")
b.vol(b.player_pokemon)["no_escape"] = True
b.handle_run()
check("can't escape" in str(b.dialogue_box.text_lines).lower(), "Mean Look-style trap: can't run")

print("3) protection, healing, field")
b = fresh()
b._acts_second = id(b.opponent_pokemon)
use(b, "PROTECT")
dmg, lines, _ = use(b, "TACKLE", foe=True)
check(dmg == 0 and "protected itself" in lines[-1], f"Protect: {lines[-1]}")
b = fresh()
b.player_hp = 10
b.player_pokemon.current_hp = 10
_, lines, _ = use(b, "RECOVER")
check(b.player_hp > 10, f"Recover heals: {b.player_hp}/{b.player_max_hp}")
b = fresh(1, 19)
use(b, "LEECH-SEED")
hp = b.opponent_hp
lines = b.effects_end_of_turn()
check(b.opponent_hp < hp and any("sapped" in l for l in lines), f"Leech Seed drains: {lines}")
b = fresh()
random.seed(5)
no_screen = sum(b._calculate_damage(b.opponent_pokemon, b.player_pokemon, 80, 1.0, category="PHYSICAL",
                                    move_type="NORMAL") for _ in range(30))
b.side(b.player_pokemon)["reflect"] = 5
random.seed(5)
screen = sum(b._calculate_damage(b.opponent_pokemon, b.player_pokemon, 80, 1.0, category="PHYSICAL",
                                 move_type="NORMAL") for _ in range(30))
check(screen < 0.7 * no_screen, f"Reflect halves physical damage ({screen} vs {no_screen})")
b.stages(b.player_pokemon)["ATTACK"] = 3
use(b, "HAZE")
check(b.stages(b.player_pokemon)["ATTACK"] == 0, "Haze resets stages")

print("4) rampage, switching, learnsets")
b = fresh(56, 19)  # Mankey learns Thrash
use(b, "THRASH")
check(b.forced_effect_move(b.player_pokemon) == "THRASH", "Thrash locks the user in")
for _ in range(3):
    lines = b.end_rampage_turn(b.player_pokemon)
    if lines:
        break
check(b.vol(b.player_pokemon).get("confused") and "fatigue" in lines[0], f"then it's confused: {lines}")
b.stages(b.player_pokemon)["ATTACK"] = 2
old = b.player_pokemon
b.player_pokemon = mk(7)
b._check_forms()
check(id(old) not in b._fx()["stages"], "stat stages end when a Pokemon switches out")
bulba = mk(1)
bulba.level = 7
bulba.moves = []
check("GROWL" in movelib.ensure_moves(g, bulba), f"Bulbasaur Lv 7 knows Growl: {bulba.moves}")
check(movelib.usable(movelib.info(g, "SWORDS-DANCE")) and not movelib.usable(movelib.info(g, "EXPLOSION")),
      "status moves are learnable now (self-KO moves still aren't)")
print("FAILURES:", fails)
