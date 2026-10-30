
# Jordan's 10-29 changes: canon levels, EXP SHARE and XP for every battler, the town menu on routes,
# Hoenn's catching before the Pokedex and Galarian Zigzagoon.
from collections import Counter
from src.world import levels, regional_forms
from src.states.overworld import PlayState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
prog = g.loader.area_data["STORY_PROGRESSION"]

print("1) canon levels: each region's own game")
check(levels.CHAMPION_ACE["JOHTO"] == 50 and levels.CHAMPION_ACE["SINNOH"] == 66, "Lance 50 (HGSS), Cynthia 66 (BDSP)")
check(levels.GYM_ACE["ORANGE"] == [levels.GYM_ACE["JOHTO"][i] for i in (1, 3, 5, 7)], "Orange Gyms = Johto Gyms 2/4/6/8")
check(prog["PUMMELO_ISLAND"]["gym"]["leader"]["levels"][-1] == levels.CHAMPION_ACE["JOHTO"], "Drake's ace = Lance's")
check(levels.area_level(g, "JOHTO_ROUTE_44") == 23, f"Route 44 at HGSS's 22-26: {levels.area_level(g, 'JOHTO_ROUTE_44')}")
story.player_team = [mk(6)]
story.player_team[0].level = 80
check(levels.area_level(g, "JOHTO_ROUTE_29") == 3, "a Lv 80 team doesn't raise Route 29")

print("2) XP: every battler that hasn't fainted; EXP SHARE gives the rest half")
story.current_area_key = "HOENN_ROUTE_101"
story.level_cap_mode = "NONE"
a, b, c = mk(258), mk(261), mk(263)
for p in (a, b, c):
    p.level, p.xp = 10, 0
    p.current_hp = p.get_max_hp()
story.player_team = [a, b, c]
story.inventory.pop("EXP_SHARE", None)
story.exp_share = False
bt = battle(story.current_area_key, 258, 263)
story.player_team = [a, b, c]
bt.player_pokemon = a
bt._note_participant()
bt.player_pokemon = b
bt._note_participant()
shares = {id(p): k for p, k in bt._xp_shares()}
check(shares == {id(a): 0.5, id(b): 0.5}, "EXP SHARE off: the two battlers split it")
a.current_hp = 0
shares = {id(p): k for p, k in bt._xp_shares()}
check(shares == {id(b): 1.0}, "a fainted battler gets none")
a.current_hp = a.get_max_hp()
story.exp_share = True
shares = {id(p): k for p, k in bt._xp_shares()}
check(shares == {id(a): 1.0, id(b): 1.0, id(c): 0.5}, "EXP SHARE on: battlers all of it, the rest half")
check(getattr(type(story)(), "exp_share", None) is True, "EXP SHARE is on by default")

print("3) Hoenn: battle before the Pokedex, catch only after")
story.story_flags.pop("received_pokedex_hoenn", None)
check(not story.catch_unlocked("HOENN"), "no catching before Birch's Pokedex")
story.story_flags["received_pokedex_hoenn"] = True

print("4) Galarian Zigzagoon: not in Hoenn until Galar; wild battles follow the pool's odds")
pool = g.loader.area_data["HOENN_ROUTE_101_PERCENTAGES"]
story.visited_region_set = {"HOENN"}
story.current_area_key = "HOENN_ROUTE_101"
check("2032" not in regional_forms.extend_pool(g, pool), "Galarian Zigzagoon filtered out")
ps = PlayState(g)
picks = Counter()
orig = levels.set_wild
levels.set_wild = lambda game, poke, area: picks.update([poke.id]) or orig(game, poke, area)
for _ in range(120):
    g.change_state(ps)
    ps.action_battle_wild()
levels.set_wild = orig
check(picks[263] > picks[2032] * 5 and picks[263] > 20, f"Zigzagoon common, no Galarian: {dict(picks)}")

print("5) routes: the town menu (EXPLORE / PKDEX / POKeMON / TRAVEL) with pop-ups")
story.current_area_key = "HOENN_ROUTE_104"
ps = PlayState(g)
g.change_state(ps)
ps.rounds_completed = 99  # the route's opening rounds done: its ways out are open
ps.show_progression_menu()
check([b.text for b in ps.route_action_menu.buttons] == ["EXPLORE", "PKDEX", "POKéMON", "TRAVEL"], "four commands")
ps.toggle_route_popup("explore")
shown = [b for b in ps.route_buttons if b in g.ui_manager.elements]
check(shown and all(b.route_group == "explore" for b in shown), f"EXPLORE: {[b.text for b in shown]}")
ps.toggle_route_popup("travel")
shown = [b for b in ps.route_buttons if b in g.ui_manager.elements]
check(shown and all(b.route_group == "travel" for b in shown), f"TRAVEL: {[b.text for b in shown]}")
print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL(S)'}")
