
from src.pokemon import moves as movelib, forms
from src.states.systems import PokemonDetailState
from src.world.story import StoryManager
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None

print("1) level-up moves join the pool; nothing is forgotten")
p = mk(4)
p.level = 20
p.moves = []
movelib.ensure_moves(g, p)
start = list(p.moves)
check(len(start) == 4, f"Lv 20 Charmander knows 4: {start}")
p.level = 40
lines = movelib.learn_new_moves(g, p, 20)
pool = movelib.move_pool(g, p)
check(p.moves == start, "its four moves stay as they were (no automatic replacing)")
new = [m for m in movelib.learnable(g, p, after=20)]
check(new and all(m in pool for m in new), f"new moves are in its pool: {new}")
check(lines and all("Summary" in l for l in lines if "learned" in l), f"{lines[:1]}")

print("2) fewer than four: a new move is set right away")
q = mk(1)
q.level = 1
q.moves = []
movelib.ensure_moves(g, q)
n0 = len(q.moves)
q.level = 15
movelib.learn_new_moves(g, q, 1)
check(n0 < 4 and len(q.moves) == min(4, len(movelib.learnable(g, q))), f"{n0} -> {len(q.moves)} moves")

print("3) picking moves in the Summary")
story.player_team = [p]
s = PokemonDetailState(g, p, g.current_state)
s.show_tab("MOVES")
s.draw()
choices = s._pool_choices()
check(choices, f"pool shows {len(choices)} other moves")
target = choices[0]
s.click_moves(s.slot_rects[0].center)
check(s.sel_slot == 0, "tap a move: it's selected")
s.draw()
r = next(r for r, n in s.pool_rects if n == target)
s.click_moves(r.center)
check(p.moves[0] == target and start[0] in movelib.move_pool(g, p), f"swapped in {target}; {start[0]} stays in the pool")

print("4) saving, loading and evolving keep the pool")
data = story.serialize()
s2 = StoryManager()
s2.game = g
s2.deserialize(data, g.loader)
lp = s2.player_team[0]
check(lp.moves == p.moves and set(movelib.move_pool(g, lp)) >= set(pool), "save and load")

print("5) trainers: canon movesets, else their best four")
foe = mk(25)
foe.level = 50
forms.mark_trainer_team([foe], {"movesets": {"25": ["THUNDERBOLT", "QUICK-ATTACK", "THUNDER-WAVE", "DOUBLE-TEAM"]}})
got = movelib.ensure_moves(g, foe)
check(got[:3] == ["THUNDERBOLT", "QUICK-ATTACK", "THUNDER-WAVE"] and len(got) == 4,
      f"Pikachu: {got} (Double Team isn't used in this game, so a learnset move fills in)")
wild = mk(19)
wild.level = 30
check(len(movelib.ensure_moves(g, wild)) == 4, f"a wild Lv 30 Rattata has 4 moves: {wild.moves}")

print("6) a real Gym battle uses canon moves")
from src.states import overworld as ow
from src.states.battle import TrainerIntroState
story.current_area_key = "PEWTER_CITY"
story.player_team = [mk(7)]
story.story_flags["gym_progress_PEWTER_CITY"] = len(g.loader.area_data["STORY_PROGRESSION"]["PEWTER_CITY"]["gym"]["trainers"])
lobby = ow.GymLobbyState(g, None)
g.change_state(lobby)
lobby.challenge_gym()
b = g.current_state.next_state if isinstance(g.current_state, TrainerIntroState) else g.current_state
onix = next(p for p in b.opponent_team if p.id == 95)
got = movelib.ensure_moves(g, onix)
check({"TACKLE", "BIND", "ROCK-TOMB"} <= set(got) and len(got) == 4, f"Brock's Onix: {got}")
print("FAILURES:", fails)
