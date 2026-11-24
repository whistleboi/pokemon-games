
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

# Snag: Orre is walked (legacy menu clear, Step 5, 11-24): the desert's SNAG figure; walk up and a Cipher trainer sends out
# the next un-snagged Shadow each time; gone from the map when the area is done.
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())
story.enter_region("ORRE")
story.inventory["SNAG_MACHINE"] = 1
story.story_flags["got_snag_machine"] = True   # (Snag menus open once Phenac's guards are beaten: the pilot, 11-20)
story.story_flags["cipher_defeated"] = True
pool = [e for e in SP["ORRE_DESERT"]["shadow_pool"] if not e.get("event_only")]   # (event_only: only its own battle has it, 11-21)
p = walk_route("ORRE_DESERT", "PHENAC_CITY")
walk_meet(p, "SNAG SHADOW POKEMON", fight=False)
b_ = g.current_state
check(getattr(getattr(b_, "opponent_pokemon", None), "id", None) == pool[0]["id"], f"walk up to the SNAG figure: the area's first Shadow ({type(b_).__name__})")
story.story_flags[pool[0]["flag"]] = True
p = walk_route("ORRE_DESERT", "PHENAC_CITY")
walk_meet(p, "SNAG SHADOW POKEMON", fight=False)
b_ = g.current_state
check(getattr(getattr(b_, "opponent_pokemon", None), "id", None) == pool[1]["id"], "a snagged Shadow is skipped")
for s_ in pool:
    story.story_flags[s_["flag"]] = True
p = walk_route("ORRE_DESERT", "PHENAC_CITY")
check(walk_who(p, "SNAG SHADOW POKEMON") is None, "SNAG figure gone once the area is cleared")
for s_ in pool:
    story.story_flags.pop(s_["flag"], None)

# XD: Gateon Port opens on the bike's list after Ein's lab (Orre as a region, 10-27), lairs open in order.
story.story_flags["orre_ein_lab"] = story.story_flags["orre_part2"] = True
t = walk_town("PHENAC_CITY", "ORRE_DESERT")
# (the button toward the Journal's next mission starts "> ": the way to Lovrina's lab, 11-01)
check("Gateon Port" in [x.lstrip("> ") for x in walk_door(t, "cycle") or []], "Gateon Port opens after Ein's lab")
story.story_flags["xd_machine_part_given"] = True   # (11-20, Orre batch 5a: the Cipher Lab joins the map once Datan has traced Cipher's car)
story.badges.setdefault("ORRE", []).append("GATEON")   # (...and Gateon's badge is won: its condition since batch 5a)
t = walk_town("GATEON_PORT", "PHENAC_CITY")
tx = [x.lstrip("> ") for x in walk_door(t, "cycle") or []]
check("Cipher Lab" in tx and "ONBS Building" not in tx, f"XD lairs gated: {tx}")
story.badges["ORRE"].remove("GATEON")

# Pokedex: a Shadow Pokemon is its own variant entry.
g.data.data["pokedex"] = {}
g.data.add_pokemon(shade)
check(set(g.data.data["pokedex"]) == {"9399-shadow"}, f"Shadow Tyranitar registers as a variant: {set(g.data.data['pokedex'])}")

# Optional purify at the Relic Stone: only the chosen Shadow Pokemon.
sh1 = Pokemon(g.loader.fetch_specific(9348), g.assets, size_mult=2.5); sh1.level = 40   # Bayleef
sh2 = Pokemon(g.loader.fetch_specific(9406), g.assets, size_mult=2.5); sh2.level = 20   # Makuhita
story.player_team = [sh1, sh2]
c = walk_town("AGATE_VILLAGE", "ORRE_DESERT")
shown = []
_run_story_event(c, {"purify": "choose", "lines": ["The Relic Stone glows."]}, lambda cond: True, shown.append)
menu = g.current_state
check(type(menu).__name__ == "PokemonPartyMenuState", "Relic Stone asks which Pokemon")
menu.on_select(0)
check(story.player_team[0].id == 154 and story.player_team[1].id == 9406,
      f"only the chosen one purified (and evolved): {[p.name for p in story.player_team]}")
check(any("MEGANIUM" in l for l in shown[-1]), f"purify message: {shown[-1]}")

print(f"##### shadows: {fails} fails")
