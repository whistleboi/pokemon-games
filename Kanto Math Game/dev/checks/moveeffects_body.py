
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
print("Encore (Jordan, 11-03): the foe repeats its last move for 3 turns")
b = fresh()
check(not any("encore" in l for l in use(b, "ENCORE")[1]), "no last move yet: it fails")
use(b, "TACKLE", foe=True)
_, lines, _ = use(b, "ENCORE")
check(any("received an encore" in l for l in lines) and b.forced_effect_move(b.opponent_pokemon) == "TACKLE",
      f"after its Tackle: {lines[-1]}")
for _ in range(3):
    b.effects_end_of_turn()
check(b.forced_effect_move(b.opponent_pokemon) is None, "it ends after 3 turns")
check(movelib.usable(movelib.info(g, "ENCORE")), "Encore can be learned and used")
print("Poison still hurts the foe on the turn it knocks your Pokemon out (Jordan, 11-03)")
b = fresh()
b.opponent_pokemon.status = "poison"
b._turn_end_done = False
b.player_hp = 0
before = b.opponent_hp
lines = b._count_weather_on_faint()
check(b.opponent_hp == before - b.opp_max_hp // 8 and any("hurt by its poison" in l for l in lines), f"{lines[:1]}")
b = fresh()
b.opponent_pokemon.status = "poison"
b._turn_end_done = False
b.player_hp, b.opponent_hp = 0, 1
b._count_weather_on_faint()
check(b.opponent_hp == 0 and b._start_pending_faint() and b.fainting_side == "opponent",
      "if the poison knocks it out too, it faints next")
print("Abilities (Jordan, 11-03): from the Journeys / PokeAPI data, working in battle")
from src.pokemon import abilities as ablib
pika = g.loader.fetch_specific(25)
from src.pokemon.data import Pokemon as _P
_pk = _P(pika, g.assets); _pk.ability_slot = 0
check(ablib.ability(g, _pk) == "STATIC", f"Pikachu's ability: {ablib.ability(g, _pk)}")
_pk.ability_slot = 2
check(ablib.ability(g, _pk) == "LIGHTNINGROD" and ablib.is_hidden(g, _pk), "slot 2: its hidden Lightning Rod")
check(ablib.name(g, "LIGHTNINGROD") == "Lightning Rod" and "Electric" in ablib.desc(g, "LIGHTNINGROD"), "its name and text")


def give(b, mon, key):
    b.vol(mon)["ability"] = key


def avg_damage(make, n=40):
    total = 0
    for _ in range(n):
        b = make()
        total += use(b, "TACKLE")[0]
    return total / n


b = fresh()
give(b, b.opponent_pokemon, "VOLTABSORB")
b.opponent_hp = b.opp_max_hp // 2
dmg, lines, _ = use(b, "THUNDER-SHOCK")
check(dmg == 0 and any("Volt Absorb" in l for l in lines) and b.opponent_hp > b.opp_max_hp // 2,
      f"Volt Absorb heals instead: {lines[-1]}")
b = fresh()
give(b, b.opponent_pokemon, "LEVITATE")
dmg, lines, _ = use(b, "MUD-SLAP")
check(dmg == 0 and any("Levitate" in l for l in lines), "Levitate: Ground moves miss it")
b = fresh()
give(b, b.player_pokemon, "INTIMIDATE")
lines = b.ability_on_entry(b.player_pokemon)
check(b.stages(b.opponent_pokemon)["ATTACK"] == -1 and any("Intimidate" in l for l in lines), "Intimidate lowers the foe's Attack")
b = fresh()
give(b, b.opponent_pokemon, "CLEARBODY")
give(b, b.player_pokemon, "INTIMIDATE")
b.ability_on_entry(b.player_pokemon)
check(b.stages(b.opponent_pokemon)["ATTACK"] == 0, "Clear Body stops it")
b = fresh()
give(b, b.player_pokemon, "DRIZZLE")
b.ability_on_entry(b.player_pokemon)
check(b.weather == "RAIN", "Drizzle brings rain")
random.seed(5)
plain = avg_damage(fresh)
random.seed(5)
huge = avg_damage(lambda: (lambda b: (give(b, b.player_pokemon, "HUGEPOWER"), b)[1])(fresh()))
check(huge > plain * 1.7, f"Huge Power doubles Attack ({plain:.1f} -> {huge:.1f})")
random.seed(5)
fat = avg_damage(lambda: (lambda b: (give(b, b.opponent_pokemon, "FURCOAT"), b)[1])(fresh()))
check(fat < plain * 0.65, f"Fur Coat halves physical hits ({plain:.1f} -> {fat:.1f})")
b = fresh()
give(b, b.opponent_pokemon, "STURDY")
b.opponent_hp = b.opp_max_hp
dmg, lines, _ = b._use_move(b.player_pokemon, b.opponent_pokemon, "TACKLE", "ME", "FOE", b.opp_max_hp, 1) \
    if False else (None, None, None)
b.player_pokemon.level = 100
b.opponent_pokemon.level = 2
b.player_max_hp = b.player_pokemon.get_max_hp(); b.opp_max_hp = b.opponent_pokemon.get_max_hp()
b.opponent_hp = b.opp_max_hp
dmg, lines, _ = use(b, "TACKLE")
check(dmg == b.opp_max_hp - 1 and any("Sturdy" in l for l in lines), f"Sturdy: survives a KO from full HP ({lines[-1]})")
b = fresh()
give(b, b.opponent_pokemon, "STATIC")
random.seed(1)
hits = 0
for _ in range(60):
    b.player_pokemon.status = None
    use(b, "TACKLE")
    hits += b.player_pokemon.status == "paralysis"
check(8 < hits < 35, f"Static paralyses about 30% of contact ({hits}/60)")
b = fresh()
give(b, b.player_pokemon, "TRUANT")
first = b.before_move(b.player_pokemon)[0]
second = b.before_move(b.player_pokemon)
check(not first and second[0] and "loafing" in second[1][0], "Truant: every other turn it loafs around")
b = fresh()
give(b, b.player_pokemon, "SPEEDBOOST")
b.effects_end_of_turn()
check(b.stages(b.player_pokemon)["SPEED"] == 1, "Speed Boost at the end of the turn")
b = fresh()
give(b, b.player_pokemon, "POISONHEAL")
b.player_pokemon.status = "poison"
b.player_hp = b.player_max_hp // 2
b._status_chip()
check(b.player_hp > b.player_max_hp // 2, "Poison Heal heals instead of hurting")
b = fresh()
give(b, b.player_pokemon, "CONTRARY")
b.change_stages(b.player_pokemon, [["ATTACK", -1]], by_foe=True)
check(b.stages(b.player_pokemon)["ATTACK"] == 1, "Contrary turns drops into boosts")
b = fresh()
give(b, b.player_pokemon, "DEFIANT")
b.change_stages(b.player_pokemon, [["DEFENSE", -1]], by_foe=True)
check(b.stages(b.player_pokemon)["ATTACK"] == 2, "Defiant: a drop sharply raises Attack")
b = fresh()
give(b, b.player_pokemon, "PRANKSTER")
check(b.ability_priority(b.player_pokemon, movelib.info(g, "GROWL")) == 1, "Prankster: status moves go first")
b = fresh()
give(b, b.player_pokemon, "LIMBER")
check(not b._can_inflict("paralysis", b.player_pokemon), "Limber: can't be paralysed")
b = fresh()
give(b, b.opponent_pokemon, "WONDERGUARD")
dmg, lines, _ = use(b, "TACKLE")
check(dmg == 0 and any("Wonder Guard" in l for l in lines) and any("super-effective" in l for l in lines), "Wonder Guard: only super-effective hits, and the battle says so")
b = fresh()
give(b, b.player_pokemon, "MOXIE")
b.opponent_hp = 1
use(b, "TACKLE")
check(b.stages(b.player_pokemon)["ATTACK"] == 1, "Moxie: a knockout raises Attack")
check(len(__import__("src.states.battle_abilities", fromlist=["x"]).IMPLEMENTED) >= 120,
      f"{len(__import__('src.states.battle_abilities', fromlist=['x']).IMPLEMENTED)} abilities work in battle")
print("The TMs' moves (11-03): terrains, swaps, rooms, Imprison, Beat Up, Self-Destruct")
b = fresh()
use(b, "ELECTRIC-TERRAIN")
check(b.terrain() == "electric" and not b._can_inflict("sleep", b.opponent_pokemon), "Electric Terrain: no sleep")
for _ in range(5):
    b.effects_end_of_turn()
check(b.terrain() is None, "it lasts 5 turns")
b = fresh()
b.stages(b.player_pokemon)["ATTACK"] = 2
use(b, "POWER-SWAP")
check(b.stages(b.opponent_pokemon)["ATTACK"] == 2 and b.stages(b.player_pokemon)["ATTACK"] == 0, "Power Swap")
b = fresh()
use(b, "WONDER-ROOM")
check(b.field().get("wonder_room") == 5, "Wonder Room")
b = fresh()
b.player_pokemon.moves = ["TACKLE", "IMPRISON"]
use(b, "IMPRISON")
dmg, lines, _ = use(b, "TACKLE", foe=True)
check(dmg == 0 and "sealed" in lines[0], "Imprison: the foe can't use a move you know")
b = fresh()
dmg, lines, _ = use(b, "BEAT-UP")
check(dmg > 0, f"Beat Up hits ({lines[-1]})")
b = fresh()
dmg, lines, _ = use(b, "SELF-DESTRUCT")
check(dmg > 0 and b.player_hp == 0, "Self-Destruct: a big hit, and the user faints")
print("FAILURES:", fails)
