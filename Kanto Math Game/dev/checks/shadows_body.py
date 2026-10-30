
# Orre Shadow Pokemon: every Colosseum/XD Shadow Pokemon, snag pools, reverse stats, optional purify.
from src.states.overworld import CityState, PlayState, _run_story_event
from src.states.battle import TrainerIntroState
fails = 0
SP = g.loader.area_data["STORY_PROGRESSION"]
FM = g.loader.area_data["FORM_MAP"]


def check(ok, msg):
    global fails
    print(("ok   " if ok else "FAIL ") + msg)
    fails += 0 if ok else 1


KANTO_STARTERS = {str(i) for i in range(9432, 9441)}  # Jordan's Shadow starter lines (10-30, not in the games)
shadows = {k: v for k, v in FM.items() if v.get("form") == "shadow" and int(k) < 9601 and k not in KANTO_STARTERS}
check(len(shadows) == 131, f"131 Shadow forms (Colosseum + XD, one per species): {len(shadows)}")
pooled = [s for a in SP.values() for s in a.get("shadow_pool", [])]
check({str(s["id"]) for s in pooled} == set(shadows) | {"9432", "9435", "9438"} and len(pooled) == len(shadows) + 3,
      "every Shadow form is in a snag pool (and the three Kanto starters, at the Shadow Pokemon Lab)")
import os
missing = [k for k in shadows if not os.path.exists(f"assets/sprites/pokemon/{k}.png")]
check(not missing, f"every Shadow form has a sprite (missing {missing[:5]})")

# Reverse stats: same total, Attack <-> Defense, Sp. Atk <-> Sp. Def.
base = Pokemon(g.loader.fetch_specific(248), g.assets, size_mult=2.5)
shade = Pokemon(g.loader.fetch_specific(9399), g.assets, size_mult=2.5)
b, s = base.base_stats, shade.base_stats
check(s["ATTACK"] == b["DEFENSE"] and s["DEFENSE"] == b["ATTACK"]
      and s["SPECIAL-ATTACK"] == b["SPECIAL-DEFENSE"] and s["SPECIAL-DEFENSE"] == b["SPECIAL-ATTACK"]
      and sum(s.values()) == sum(b.values()), f"Shadow Tyranitar stats swapped: {s}")

# Snag: one button per area, next un-snagged Shadow each time, hidden when the area is done.
story.inventory["SNAG_MACHINE"] = 1
story.story_flags["cipher_defeated"] = True
story.current_area_key = "ORRE_DESERT"
p = PlayState(g); g.change_state(p); p.show_progression_menu()
btns = [b.text for b in p.route_buttons]
check(btns.count("SNAG SHADOW POKEMON") == 1, f"one SNAG button: {btns}")
pool = SP["ORRE_DESERT"]["shadow_pool"]
check(p._next_shadow()["id"] == pool[0]["id"], "first snag is the area's first Shadow")
story.story_flags[pool[0]["flag"]] = True
check(p._next_shadow()["id"] == pool[1]["id"], "a snagged Shadow is skipped")
for s_ in pool:
    story.story_flags[s_["flag"]] = True
p.show_progression_menu()
check("SNAG SHADOW POKEMON" not in [b.text for b in p.route_buttons], "SNAG hidden once the area is cleared")
for s_ in pool:
    story.story_flags.pop(s_["flag"], None)

# XD: Gateon Port opens after Ein's lab (Orre as a region, 10-27), lairs open in order.
story.story_flags["orre_ein_lab"] = True
story.current_area_key = "PHENAC_CITY"
c = CityState(g); g.change_state(c); c.open_travel_menu()
check("Gateon Port" in [b.text for b in c.hover_buttons], "Gateon Port opens after Ein's lab")
story.current_area_key = "GATEON_PORT"
c = CityState(g); g.change_state(c); c.open_travel_menu()
t = [b.text for b in c.hover_buttons]
check("Cipher Lab" in t and "ONBS Building" not in t, f"XD lairs gated: {t}")

# Pokedex: a Shadow Pokemon is its own variant entry.
g.data.data["pokedex"] = {}
g.data.add_pokemon(shade)
check(set(g.data.data["pokedex"]) == {"9399-shadow"}, f"Shadow Tyranitar registers as a variant: {set(g.data.data['pokedex'])}")

# Optional purify at the Relic Stone: only the chosen Shadow Pokemon.
sh1 = Pokemon(g.loader.fetch_specific(9348), g.assets, size_mult=2.5); sh1.level = 40   # Bayleef
sh2 = Pokemon(g.loader.fetch_specific(9406), g.assets, size_mult=2.5); sh2.level = 20   # Makuhita
story.player_team = [sh1, sh2]
story.current_area_key = "AGATE_VILLAGE"
c = CityState(g); g.change_state(c)
shown = []
_run_story_event(c, {"purify": "choose", "lines": ["The Relic Stone glows."]}, lambda cond: True, shown.append)
menu = g.current_state
check(type(menu).__name__ == "PokemonPartyMenuState", "Relic Stone asks which Pokemon")
menu.on_select(0)
check(story.player_team[0].id == 154 and story.player_team[1].id == 9406,
      f"only the chosen one purified (and evolved): {[p.name for p in story.player_team]}")
check(any("MEGANIUM" in l for l in shown[-1]), f"purify message: {shown[-1]}")

print(f"##### shadows: {fails} fails")
