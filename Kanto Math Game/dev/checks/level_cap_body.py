# Battle option "level_cap" (Unova 11-23, Jordan: "Lv 50, as Black 2" for the Battle Subway): your Pokemon above the cap
# battle at it for that battle only, gain no Exp. there, and come back as they were afterwards.
#   bash dev/checks/run.sh level_cap
from src.states.battle import TrainerBattleState, TrainerIntroState

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


def click(pos):
    for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        ev = pygame.event.Event(kind, button=1, pos=pos)
        left = g.ui_manager.unconsumed([ev])
        if left:
            g.current_state.handle_events(left)


def run(b, frames=4000):
    for _ in range(frames):
        st = g.current_state
        box = getattr(st, "dialogue_box", None)
        if box is not None and box.visible and not box.is_finished:
            click(box.rect.center)
        st.update()
        if st is b and b.phase == "MENU" and not b.dialogue_box.visible:
            return True
        if st is not b and not isinstance(st, TrainerIntroState):
            return False
    return False


def mon(pid, level, moves):
    p = mk(pid)
    p.level = level
    p.moves = list(moves)
    p.current_hp = p.get_max_hp()
    return p


story.level_cap_mode = "NONE"
big, small = mon(9, 70, ["SURF"]), mon(25, 30, ["THUNDERBOLT"])
big.xp = 7
story.player_team = [big, small]
big.current_hp = big.get_max_hp() // 2   # (half its HP going in)
hp70 = big.get_max_hp()

print("1) in the battle")
b = TrainerBattleState(g, [mon(19, 5, ["SPLASH"])], trainer_class="YOUNGSTER", trainer_name="Joey",
                       area_name=story.current_area_key, options={"level_cap": 50})
check(big.level == 50 and small.level == 30, f"Lv 70 battles at 50, Lv 30 stays 30 ({big.level}, {small.level})")
check(abs(big.current_hp / big.get_max_hp() - 0.5) < 0.02, f"with the same share of its HP ({big.current_hp}/{big.get_max_hp()})")
check(big.get_max_hp() < hp70, f"its stats are Lv 50's (HP {big.get_max_hp()} < {hp70})")
check(b._award_battle_xp() == [], "no Exp. in a capped battle")

print("2) afterwards: back as it was")
b.player_won = True
try:
    b.exit_battle()
except Exception as e:   # (the battle's own way back to the map may need more of a game than this check has)
    print("   (exit_battle went on to", type(e).__name__, e, ")")
check(big.level == 70 and big.xp == 7, f"Lv 70 again, Exp. as it was ({big.level}, xp {big.xp})")
check(abs(big.current_hp / big.get_max_hp() - 0.5) < 0.02, f"the same share of HP at Lv 70 ({big.current_hp}/{big.get_max_hp()})")

print("3) run from: back as it was too")
b2 = TrainerBattleState(g, [mon(19, 5, ["SPLASH"])], trainer_class="YOUNGSTER", trainer_name="Joey",
                        area_name=story.current_area_key, options={"level_cap": 50})
check(big.level == 50, "capped again")
try:
    b2.on_flee_complete()
except Exception as e:
    print("   (on_flee_complete went on to", type(e).__name__, e, ")")
check(big.level == 70, f"after running: Lv {big.level}")

print("4) no option: nothing changes")
b3 = TrainerBattleState(g, [mon(19, 5, ["SPLASH"])], trainer_class="YOUNGSTER", trainer_name="Joey", area_name=story.current_area_key)
check(big.level == 70 and b3._cap_saved == [], "an ordinary battle leaves levels alone")
print(f"##### {len(fails)} failures")
