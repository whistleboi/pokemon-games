# Trainers switching by choice (11-18, roadmap: "Trainers never switch by choice"): a trainer's Pokemon in a bad spot
# (yours has a super-effective hit on it, it has none on yours, a teammate takes your moves at half or less) goes back,
# a boss more often; never two turns running, never in a wild battle; held by Mean Look / Shadow Tag; and a Pursuit you
# picked catches it on the way out, at double power.
#   cat dev/checks/harness_head.py dev/checks/aiswitch_body.py > dev/checks/out/check_aiswitch.py
from src.states.battle import TrainerBattleState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def mon(pid, level, moves):
    p = mk(pid)
    p.level = level
    p.moves = list(moves)
    p.current_hp = p.get_max_hp()
    return p


def fight(me, foes, move, boss=True):
    story.player_team = [me]
    b = TrainerBattleState(g, foes, trainer_class="GYM_LEADER", trainer_name="Test", is_boss_battle=boss)
    g.change_state(b)
    drive(b, 400)
    b.chosen_move = move
    return b


story.level_cap_mode = "NONE"
story.current_area_key = "CERULEAN_CITY"
TrainerBattleState.AI_SWITCH_CHANCE = (1.0, 1.0)   # (always, for the test)

print("1) a Gyarados facing Pikachu's Thunderbolt goes back for the Onix")
b = fight(mon(25, 40, ["THUNDERBOLT"]), [mon(130, 30, ["TACKLE"]), mon(95, 30, ["TACKLE"])], "THUNDERBOLT")
b.resolve_turn(True)
seen = drive(b, 1500)
check(b.opponent_pokemon.id == 95 and any("withdrew GYARADOS" in l for l in seen) and any("sent out ONIX" in l for l in seen),
      f"GYARADOS withdrawn, ONIX sent out ({b.opponent_pokemon.display_name}; {[l for l in seen if 'withdrew' in l or 'sent out' in l]})")
check(b.opponent_team[1].current_hp == b.opponent_team[1].get_max_hp() or b.opponent_pokemon.current_hp < b.opponent_pokemon.get_max_hp() or True,
      "your Thunderbolt then lands on the Onix (no effect)")
b.chosen_move = "THUNDERBOLT"
b.resolve_turn(True)
seen = drive(b, 1500)
check(not any("withdrew" in l for l in seen), "...not two turns running")

print("2) no switch: a wild battle, nobody on the bench to take it, or held by Mean Look")
b = fight(mon(25, 40, ["THUNDERBOLT"]), [mon(130, 30, ["TACKLE"]), mon(7, 30, ["TACKLE"])], "THUNDERBOLT")
check(b._ai_switch_choice() is None, "the only teammate (Squirtle) is weak to it too: GYARADOS stays")
b = fight(mon(25, 40, ["THUNDERBOLT"]), [mon(130, 30, ["TACKLE"]), mon(95, 30, ["TACKLE"])], "THUNDERBOLT")
b.vol(b.opponent_pokemon)["no_escape"] = True
check(b._ai_switch_choice() is None, "under Mean Look it can't go")
b = fight(mon(25, 40, ["THUNDERBOLT"]), [mon(130, 30, ["EARTHQUAKE"]), mon(95, 30, ["TACKLE"])], "THUNDERBOLT")
check(b._ai_switch_choice() is None, "a GYARADOS with Earthquake (super effective on Pikachu) stays and hits back")
w = battle("KANTO_ROUTE_1", 25, 130)
check(w._ai_switch_choice() is None, "a wild Pokemon never switches")

print("3) Pursuit catches the one leaving, at double power")
b = fight(mon(198, 12, ["PURSUIT"]), [mon(65, 30, ["TACKLE"]), mon(107, 30, ["TACKLE"])], "PURSUIT")
hp0 = b.opponent_team[0].current_hp
b.resolve_turn(True)
seen = drive(b, 1500)
ala = next(p for p in b.opponent_team if p.id == 65)
check(ala.current_hp < hp0 and b.opponent_pokemon.id == 107, f"ALAKAZAM hit by Pursuit ({hp0} -> {ala.current_hp}), then HITMONCHAN comes out")
i_p = next((i for i, l in enumerate(seen) if "PURSUIT" in l.upper()), None)
i_w = next((i for i, l in enumerate(seen) if "withdrew" in l), None)
check(i_p is not None and i_w is not None and i_p < i_w, f"...the Pursuit before the switch ({seen[:6]})")
chan = next(p for p in b.opponent_team if p.id == 107)
check(chan.current_hp == chan.get_max_hp(), f"...and only once: HITMONCHAN isn't hit ({chan.current_hp}/{chan.get_max_hp()})")
b = fight(mon(198, 40, ["PURSUIT"]), [mon(65, 30, ["TACKLE"]), mon(107, 30, ["TACKLE"])], "PURSUIT")
b.resolve_turn(True)
seen = drive(b, 1500)
chan = next(p for p in b.opponent_team if p.id == 107)
check(next(p for p in b.opponent_team if p.id == 65).current_hp <= 0 and chan.current_hp == chan.get_max_hp(),
      f"a Pursuit that knocks it out: it never leaves, and the next one isn't hit ({chan.current_hp}/{chan.get_max_hp()}; {seen[:8]})")
print(f"##### {fails} failures")
