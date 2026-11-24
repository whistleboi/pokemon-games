# Self-Destruct, Explosion, Misty Explosion (Jordan, 11-18: keep them, with their real effect): the user faints, as in
# the games from Gen 5 on - hit, miss, a Ghost or a Protect alike; Damp stops the blast and the user stays up.
# Played as real turns: the switch-in after it, your last Pokemon (a loss), a foe trainer's last (your win), a
# wrong math answer, and a double battle (it hits both foes, then the user faints).   bash dev/checks/run.sh selfko
import random
from src.pokemon import moves as movelib
from src.states.battle import TrainerBattleState
from src.states.battle_double import DoubleBattleState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
story.level_cap_mode = "NONE"
random.seed(7)


def mon(pid, level, moves):
    p = mk(pid)
    p.level = level
    p.moves = list(moves)
    p.current_hp = p.get_max_hp()
    return p


def fresh(me=74, foe=19, lv=30, foe_lv=30):
    b = battle("KANTO_ROUTE_1", me, foe)
    b.player_pokemon.level, b.opponent_pokemon.level = lv, foe_lv
    b.player_hp = b.player_max_hp = b.player_pokemon.current_hp = b.player_pokemon.get_max_hp()
    b.opponent_hp = b.opp_max_hp = b.opponent_pokemon.current_hp = b.opponent_pokemon.get_max_hp()
    b._obey_level = lambda: 100
    return b


def use(b, name, foe=False):
    me, them = (b.opponent_pokemon, b.player_pokemon) if foe else (b.player_pokemon, b.opponent_pokemon)
    return b._use_move(me, them, name, "ME", "FOE", b.player_max_hp if foe else b.opp_max_hp,
                       b.player_hp if foe else b.opponent_hp)


def turn(b, move, right=True):
    b.player_pokemon.moves = [move] + [m for m in b.player_pokemon.moves if m != move][:3]
    b.chosen_move = move
    b.resolve_turn(right)
    return drive(b, 1500)


print("1) the move itself (Geodude's Self-Destruct and Explosion, Lv 30 vs Rattata)")
for mv in ("SELF-DESTRUCT", "EXPLOSION", "MISTY-EXPLOSION"):
    b = fresh()
    dmg, lines, _ = use(b, mv)
    check(dmg > 0 and b.player_hp == 0, f"{mv}: a hit ({dmg}) and the user faints")
b = fresh()
b.acc_mult = lambda a, d: 0
dmg, lines, _ = use(b, "EXPLOSION")
check(dmg == 0 and b.player_hp == 0 and any("missed" in l for l in lines), f"a miss: the user still faints ({lines[-1]})")
b = fresh(foe=92)
dmg, lines, _ = use(b, "EXPLOSION")
check(dmg == 0 and b.player_hp == 0 and any("doesn't affect" in l for l in lines), "a Ghost (Gastly): no damage, the user still faints")
b = fresh()
b._acts_second = id(b.player_pokemon)
use(b, "PROTECT", foe=True)
dmg, lines, _ = use(b, "EXPLOSION")
check(dmg == 0 and b.player_hp == 0, f"the foe's Protect: blocked, the user still faints ({lines[-1]})")
b = fresh(foe=54)  # Psyduck
_ab = b.ab
b.ab = lambda m: "DAMP" if m is b.opponent_pokemon else _ab(m)
dmg, lines, _ = use(b, "EXPLOSION")
check(dmg == 0 and b.player_hp == b.player_max_hp and any("Damp" in l for l in lines), "Damp stops it, and the user doesn't faint")
dmg, lines, _ = use(b, "MEMENTO")
check(not any("Damp" in l for l in lines), "Damp doesn't stop Memento (only the exploding moves)")
b = fresh(foe=19)
b.opponent_pokemon.moves = ["EXPLOSION"]
dmg, lines, _ = use(b, "EXPLOSION", foe=True)
check(b.opponent_hp == 0, "a foe's Explosion faints the foe too")
b = fresh()
b.terrain = lambda: "misty"
b.grounded = lambda m: True
random.seed(2)
d1, _, _ = use(b, "MISTY-EXPLOSION")
b2 = fresh()
random.seed(2)
d2, _, _ = use(b2, "MISTY-EXPLOSION")
check(d1 > d2, f"Misty Explosion is stronger on Misty Terrain ({d1} vs {d2})")

print("2) a real turn in a wild battle")
b = fresh(foe_lv=60)  # (a foe it can't knock out)
b.opponent_hp = b.opp_max_hp = b.opponent_pokemon.current_hp = 9999
story.player_team = [b.player_pokemon, mon(25, 30, ["THUNDERBOLT"])]
seen = turn(b, "SELF-DESTRUCT")
check(story.player_team[0].current_hp == 0, "your Pokemon faints after its Self-Destruct")
check(any("fainted" in l and "GEODUDE" in l for l in seen), f"\"GEODUDE fainted!\" ({[l for l in seen if 'faint' in l]})")
check(type(g.current_state).__name__ == "PokemonPartyMenuState" and g.current_state.context == "forced_switch",
      f"with another Pokemon left you pick one to send in, not a loss ({type(g.current_state).__name__})")
check(not any("whited out" in l for l in seen), "no whiting out")
b = fresh(foe_lv=60)
b.opponent_hp = b.opp_max_hp = b.opponent_pokemon.current_hp = 9999
story.player_team = [b.player_pokemon]
seen = turn(b, "EXPLOSION")
check(b.player_won is False and any("defeated" in l for l in seen), f"your last Pokemon explodes: the battle is lost ({seen[-2:]})")
b = fresh(lv=60, foe_lv=5)
story.player_team = [b.player_pokemon]
seen = turn(b, "EXPLOSION")
check(any("Foe RATTATA fainted" in l for l in seen) and any("GEODUDE fainted" in l for l in seen) and b.player_won is False
      and not any("catch" in l.lower() for l in seen),
      f"your last one knocks the wild one out too: both faint, no catch, and it's your loss, as the games ({seen[-3:]})")
b = fresh(lv=60, foe_lv=5)
story.player_team = [b.player_pokemon, mon(25, 30, ["THUNDERBOLT"])]
seen = turn(b, "EXPLOSION")
check(not any("defeated" in l or "whited" in l for l in seen) and any("XP" in l for l in seen),
      f"...with another Pokemon left it's a win (XP, no loss: {seen[-2:]})")
b = fresh(me=6, lv=60, foe_lv=5)
b.player_hp = b.player_pokemon.current_hp = 1
b.opponent_pokemon.moves = ["TAIL-WHIP"]   # (a wild Rattata can know Quick Attack, which would knock the 1-HP attacker out first)
story.player_team = [b.player_pokemon]
seen = turn(b, "DOUBLE-EDGE")
check(not any("defeated" in l or "whited" in l for l in seen) and any("catch" in l for l in seen),
      f"recoil (not a blast) taking both last ones: the attacker wins, as the games ({seen[-2:]})")
b = fresh(lv=30, foe_lv=60)
b.opponent_hp = b.opp_max_hp = b.opponent_pokemon.current_hp = 9999
story.player_team = [b.player_pokemon, mon(25, 30, ["THUNDERBOLT"])]
seen = turn(b, "EXPLOSION", right=False)
check(story.player_team[0].current_hp == 0 and any("weaker" in l for l in seen),
      "a wrong math answer: a weaker blast, but the user still faints (it was used)")

print("3) a trainer's last Pokemon explodes")
story.player_team = [mon(25, 40, ["THUNDERBOLT"]), mon(7, 40, ["SURF"])]
foe = mon(74, 10, ["EXPLOSION"])
t = TrainerBattleState(g, [foe], trainer_class="HIKER", trainer_name="Rocky", area_name="KANTO_ROUTE_1")
g.change_state(t)
t._obey_level = lambda: 100
t.opponent_pokemon.speed_override = None
t._ai_choose = lambda a, d: "EXPLOSION"
t.chosen_move = "THUNDERBOLT"
t.player_hp = t.player_max_hp = t.player_pokemon.current_hp = t.player_pokemon.get_max_hp()
t.opponent_hp = t.opp_max_hp = t.opponent_pokemon.current_hp = 9999
t.resolve_turn(True)
seen = drive(t, 2000)
check(t.opponent_pokemon.current_hp == 0 or t.opponent_hp == 0, "the Hiker's Geodude explodes and faints")
check(not any("whited out" in l for l in seen) and t.phase in ("VICTORY_TEXT", "REWARD_TEXT", "OUTRO", "MENU", "SWITCH_PROMPT", "EXIT")
      or any("defeated" in l.lower() for l in seen), f"its trainer is out of Pokemon: your win (phase {t.phase}, {seen[-2:]})")

print("4) a double battle: it hits both foes, then the user faints")
story.player_team = [mon(74, 50, ["EXPLOSION"]), mon(25, 50, ["THUNDERBOLT"]), mon(7, 50, ["SURF"])]
foes = [mon(19, 50, ["TACKLE"]), mon(16, 50, ["TACKLE"])]
d = DoubleBattleState(g, foes, trainer_class="TWINS", trainer_name="Amy & May", area_name="KANTO_ROUTE_1")
g.change_state(d)
for f in d.o_slots:
    f.current_hp = 9999
    d._hurt(f, 0)
hp0 = [f.current_hp for f in d.o_slots]
boom = d.p_slots[0]
d._plans = {id(boom): {"kind": "move", "move": "EXPLOSION", "target": d.o_slots[0]}}
d._act(boom)
hit = [f.current_hp < h for f, h in zip(d.o_slots, hp0)]
check(all(hit), f"Explosion hits both foes ({hit})")
check(boom.current_hp == 0, "...and then GEODUDE faints")
print("FAILURES:", fails)
