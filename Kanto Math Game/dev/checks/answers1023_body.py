
# Jordan's 10-23 answers: boss-only legendaries, Up-Grade in Sinnoh, Decolore Gen 5, Sirfetch'd crits,
# branch choice + second Cosmoem, Mt. Battle, the X/Y Kalos dex.
import json
from src.states.overworld import CityState, PlayState, _run_story_event
from src.states.systems import EvolutionState, PokeMartState, _dex_ids
from src.pokemon import evolution
fails = 0
SP = g.loader.area_data["STORY_PROGRESSION"]
AD = g.loader.area_data


def check(ok, msg):
    global fails
    print(("ok   " if ok else "FAIL ") + msg)
    fails += 0 if ok else 1


def pools_with(pid):
    return [k for k, v in AD.items() if k.endswith("PERCENTAGES") and isinstance(v, dict) and str(pid) in v]


# Boss-only legendaries.
for pid in (377, 378, 379, 637, 638, 645, 646):
    check(not pools_with(pid), f"#{pid} is not a wild encounter ({pools_with(pid)})")
bosses = {(o.get("boss") or {}).get("id"): k for k, a in SP.items() for o in a.get("route_menu", [])}
bosses.update({(a.get("area_boss") or {}).get("id"): k for k, a in SP.items()})
hoenn = {(o.get("boss") or {}).get("id"): k for k, a in SP.items() for o in a.get("route_menu", []) if k.startswith("HOENN_")}
hoenn.update({(a.get("area_boss") or {}).get("id"): k for k, a in SP.items() if k.startswith("HOENN_")})  # (Unova's Underground Ruins has them too)
check(hoenn.get(377) == "HOENN_ROUTE_111" and hoenn.get(378) == "HOENN_ROUTE_105" and hoenn.get(379) == "HOENN_ROUTE_120",
      f"Regis at the Desert Ruins, Island Cave and Ancient Tomb: {[hoenn.get(i) for i in (377, 378, 379)]}")
check(all(bosses.get(i) for i in (637, 638, 645, 646)), "Unova's legendaries all have bosses")

# Up-Grade: only at Veilstone.
for area, want in (("VEILSTONE_CITY", True), ("CELADON_CITY", False), ("GOLDENROD_CITY", False)):
    story.current_area_key = area
    check(("UPGRADE" in PokeMartState(g, None)._shop_items()) == want, f"Up-Grade at {area}: {want}")

# Decolore: Gen 5 or earlier only.
late = [(k, x) for k, v in AD.items() if k.startswith("DECOLORE") and k.endswith("PERCENTAGES") and isinstance(v, dict)
        for x in v if int(x) > 649]
check(not late, f"Decolore pools are Gen 5 or earlier {late}")

# Sirfetch'd: critical hits add up.
far = Pokemon(g.loader.fetch_specific(2024), g.assets, size_mult=2.5)
story.current_area_key = "MOTOSTOKE"; story.enter_region("GALAR")
far.level = 30
rule = next(r for e, t, r in evolution.evolution_options(g, far) if t == 865)
far.counters["crits"] = 2
check(not evolution.rule_met(g, far, rule), "2 critical hits in total: not yet")
far.counters["crits"] = 3
check(evolution.rule_met(g, far, rule), "3 critical hits in total (any battles): Sirfetch'd")
src = open("src/states/battle.py", encoding="utf-8").read()
check('mon.counters["crits"] = mon.counters.get("crits", 0) + 1' in src and 'max(p.counters.get("crits"' not in src,
      "crits add up as they land, never reset to one battle's best")

# Branch choice on the evolution screen; Lillie's second Cosmoem.
cos = Pokemon(g.loader.fetch_specific(790), g.assets, size_mult=2.5)
story.player_team = [cos]
ev = EvolutionState(g, cos, 791, 0, choices=["SOLGALEO", "LUNALA"]); g.change_state(ev)
check([b.text for b in ev.choice_buttons] == ["SOLGALEO", "LUNALA"] and not ev.btn_yes.visible, "Cosmoem: pick Solgaleo or Lunala")
ev.choice_buttons[1].callback()
check(ev.evolution_id == 792 and ev.phase == "START", "choosing Lunala evolves into Lunala")
gift = next(o for o in SP["ALTAR_SUNNE_MOONE"]["route_menu"] if o.get("text") == "LILLIE'S GIFT")
check(gift["event"]["gift_pokemon"] == 790 and gift["condition"] == "ALTAR_boss_defeated", "Lillie gives a second Cosmoem")

# Mt. Battle: 40 trainers, the Master, and starting over.
mt = SP["MT_BATTLE"]
check(len(mt["trainer_pool"]) == 40 and any(o["text"] == "MT. BATTLE MASTER" for o in mt["route_menu"]), "Mt. Battle: 40 + Master")
story.current_area_key = "MT_BATTLE"
for i in range(40):
    story.mark_trainer_defeated("MT_BATTLE", i)
story.story_flags["mt_battle_master_beaten"] = True
c = CityState(g)
restart = next(o for o in mt["route_menu"] if o["text"] == "START OVER FROM AREA 1")
_run_story_event(c, restart["event"], lambda x: True, lambda lines: None)
check(not story.is_trainer_defeated("MT_BATTLE", 0) and not story.story_flags.get("mt_battle_master_beaten"),
      "START OVER resets the mountain")

# Kalos: the X/Y Kalos dex, in its order.
cfg = story.get_region_start("KALOS")
check(len(cfg["dex_list"]) == 457 and cfg["dex_list"][:3] == [650, 651, 652], "Kalos dex = X/Y Kalos dex (457)")
check(_dex_ids(story, {}, [], view="KALOS") == cfg["dex_list"], "the Kalos Pokedex view uses that list")
syc = next(o for o in SP["LUMIOSE_CITY"]["explore_options"] if o.get("text") == "Sycamore's Kanto Pokemon")
check(syc["event"]["gift_pokemon"]["653"] == 4, "Sycamore's Kanto gift matches the starter")
den = [(o.get("boss") or {}).get("id") for o in SP["SEA_SPIRITS_DEN"]["route_menu"]] + [SP["SEA_SPIRITS_DEN"]["area_boss"]["id"]]
check({144, 145, 146} <= set(den), f"all three birds at the Sea Spirit's Den: {den}")
for pid in (1, 4, 7, 650, 653, 656):
    check(str(pid) in AD["KALOS_ROUTE_19_PERCENTAGES"], f"#{pid} rare on Route 19")

# Alola: the Alolan forms are Alola's own (its dex, pools, trainers, and its evolutions).
alolan = {int(k): v["id"] for k, v in AD["FORM_MAP"].items() if v.get("form") == "alolan"}
check(set(alolan) <= set(_dex_ids(story, {}, [], view="ALOLA")), "Alolan forms are in the Alola dex")
kanto_forms = [(k, x) for k, v in AD.items() if k.endswith("PERCENTAGES") and isinstance(v, dict)
               and k in {a.get("wild_pool_percentages") for a in SP.values() if str(a.get("region")).upper() == "ALOLA"}
               for x in v if int(x) in set(alolan.values())]
check(not kanto_forms, f"Alola's pools use Alolan forms only {kanto_forms[:5]}")
story.current_area_key = "IKI_TOWN"; story.enter_region("ALOLA")
pika = Pokemon(g.loader.fetch_specific(25), g.assets, size_mult=2.5)
check(evolution.item_evolution(g, pika, "THUNDER_STONE") == ("RAICHU_ALOLAN", 26), "Pikachu -> Alolan Raichu in Alola")
story.current_area_key = "VIRIDIAN_CITY"
check([e for e, _, _ in evolution.evolution_options(g, pika)] == ["RAICHU"], "Pikachu -> Raichu outside Alola")

print(f"##### answers1023: {fails} fails")
