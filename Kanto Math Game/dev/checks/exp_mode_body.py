# Options > Gameplay > Difficulty (Jordan 11-24): EXP Mode, an easy mode - 30% more Exp. from every battle.
#   bash dev/checks/run.sh exp_mode
from src.core import settings
from src.pokemon import growth
from src.states.battle import TrainerBattleState
from src.states.systems.options import OptionsState

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


print("1) the option")
check(settings.get(story, "difficulty") == "NORMAL", "a new game is on Normal")
o = OptionsState(g, g.current_state, lambda: None)
o.tab = o.tabs.index("GAMEPLAY")
rows = o.rows()
check(rows[0][0] == "Difficulty" and [v for v, _l in rows[0][1]] == ["NORMAL", "EXP"], "Gameplay's first row: Difficulty, Normal or EXP Mode")
o._step(rows[0], 1)
check(settings.get(story, "difficulty") == "EXP" and growth.EXP_MODE == 1.3, "stepped to EXP Mode: on at once (x1.3)")
check(all(o._row_rect(i).bottom <= o.bar.top for i in range(len(o.rows()))), "every Gameplay row fits above the bottom bar")
check(story.serialize().get("prefs", {}).get("difficulty") == "EXP", "kept in the save")

print("2) 30% more Exp.")
settings.put(g, "difficulty", "NORMAL")
n = growth.battle_xp(100, 20, 20, trainer=True)
settings.put(g, "difficulty", "EXP")
e = growth.battle_xp(100, 20, 20, trainer=True)
check(abs(e / n - 1.3) < 0.02, f"the same win: {n} Exp. on Normal, {e} in EXP Mode")
mon = mk(25); mon.level = 8; mon.xp = 0; mon.moves = ["THUNDERBOLT"]; mon.current_hp = mon.get_max_hp()
story.player_team = [mon]
foe = mk(19); foe.level = 8
b = TrainerBattleState(g, [foe], trainer_class="YOUNGSTER", trainer_name="Joey", area_name=story.current_area_key)
b.player_pokemon, b.opponent_pokemon = mon, foe
said = " ".join(b._award_battle_xp())
_want = growth.battle_xp(int(b.game.assets.movesets.get("19", {}).get("base_xp") or 100), 8, 8, trainer=True)
check("gained" in said and mon.xp > 0, f"...a real battle's win pays EXP Mode's Exp. ({said[:60]}; the formula gives {_want})")
settings.put(g, "difficulty", "NORMAL")
check(growth.EXP_MODE == 1.0, "back on Normal: as the games give it")
print(f"##### {len(fails)} failures")
