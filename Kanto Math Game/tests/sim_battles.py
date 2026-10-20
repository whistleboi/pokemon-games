"""Headless smoke: drive many full turns (resolve_turn + queued actions) with random answers."""
import random, traceback
import _env
from _env import make_game, mk
from src.states.battle import TrainerBattleState
G = make_game(); errs = 0; turns = 0
ids = [1, 4, 7, 12, 25, 63, 92, 94, 95, 113, 123, 129, 130, 137, 143, 149, 66, 32, 18, 6]
moves = ["SOLAR-BEAM", "HYPER-BEAM", "SEISMIC-TOSS", "DOUBLE-KICK", "GIGA-DRAIN", "TAKE-DOWN", "TOXIC",
         "THUNDER-WAVE", "SLEEP-POWDER", "HEADBUTT", "FLY", "SLASH", "SUPER-FANG", "TACKLE"]
for n in range(150):
    team = [mk(G, random.choice(ids), random.randint(10, 60)) for _ in range(2)]
    foes = [mk(G, random.choice(ids), random.randint(10, 60)) for _ in range(2)]
    for m in team + foes:
        m.moves = random.sample(moves, 4)
    G.story_manager.player_team = team
    try:
        b = TrainerBattleState(G, foes, trainer_class="HIKER", trainer_name="T", battle_type="event")
        G.change_state(b)
        for _ in range(12):
            if b.player_hp <= 0 or b.opponent_hp <= 0: break
            b.chosen_move = random.choice(b._battle_moves(b.player_pokemon))
            b.resolve_turn(random.random() < 0.7)
            for act in list(b.turn_actions): act()
            b.turn_actions.clear(); turns += 1
            if hasattr(b, "_status_chip"): b._status_chip()
    except Exception:
        errs += 1; traceback.print_exc()
print(f"SIM {turns} turns, {errs} errors")
