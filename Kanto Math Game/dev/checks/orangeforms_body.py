import json

# Pinkan / Valencia forms, Crystal Onix and its stone, and cycling forms on the summary page.
from src.pokemon import evolution
from src.states.systems import PokemonDetailState, PokeMartState, PokedexState, BagState
fails = 0
SP = g.loader.area_data["STORY_PROGRESSION"]
FM = g.loader.area_data["FORM_MAP"]


def check(ok, msg):
    global fails
    print(("ok   " if ok else "FAIL ") + msg)
    fails += 0 if ok else 1


mkf = lambda pid: Pokemon(g.loader.fetch_specific(pid), g.assets, size_mult=2.5)
story.current_area_key = "PINKAN_ISLAND"   # (11-17: 5.7's one Pinkan; the Reserve folded in)
pinkan = {int(k): v["id"] for k, v in FM.items() if v.get("form") == "pinkan"}
check(len(pinkan) == 36, f"36 Pinkan forms: {len(pinkan)}")
pool = g.loader.area_data["ORANGE_PINKAN_ISLAND_PERCENTAGES"]
check(all(str(f) in pool for f in range(9101, 9136)) and "9136" not in pool, "Pinkan Island's pool: the listed lines (no Scyther), with 5.7's own species")
cat = mkf(9101); cat.level = 7; cat.evo_due = True
ready = evolution.ready_evolutions(g, cat)
check(ready == ["METAPOD_PINKAN"], f"Pinkan Caterpie -> Pinkan Metapod: {ready}")
gloom = mkf(9119)
check(evolution.item_evolution(g, gloom, "LEAF_STONE") == ("VILEPLUME_PINKAN", 45), "Pinkan Gloom + Leaf Stone")
valencia = [k for k, v in FM.items() if v.get("form") == "valencia"]
check(len(valencia) == 17, f"17 Valencia variants: {len(valencia)}")
beach = g.loader.area_data["ORANGE_VALENCIA_PARK_PERCENTAGES"]
check(all(k in beach for k in valencia), "Valencia Park, on Valencia, has Ivy's variants (11-17: Route 49 is open sea in 5.7)")

# Crystal Onix: stats, types, its own learnset, and the Crystal Stone.
co = mkf(9201)
check(co.types == ["ROCK", "ICE"] and co.base_stats == {"HP": 70, "ATTACK": 90, "DEFENSE": 60, "SPECIAL-ATTACK": 110,
                                                         "SPECIAL-DEFENSE": 70, "SPEED": 110}, f"Crystal Onix: {co.base_stats}")
co.level = 60
check({"ICICLE-CRASH", "HEAD-SMASH", "POWER-GEM"} <= evolution.known_moves(g, co), "Crystal Onix's own moves")
onix = mkf(95)
check(evolution.item_evolution(g, onix, "CRYSTAL_STONE") is None, "no Crystal Stone any more (Jordan 11-17)")
check(evolution.item_evolution(g, onix, "METAL_COAT") == ("STEELIX", 208), "Steelix branch unchanged")
_cb = SP["CRYSTAL_CAVE"].get("area_boss") or {}
check(_cb.get("id") == 9201 and _cb.get("catchable") and _cb.get("level") == 40, "the Crystal Onix is caught in the Crystal Cave (5.7: Lv 40)")
check(not any("CRYSTAL_STONE" in json.dumps(a) for a in SP.values()), "no Crystal Stone anywhere in the data")
import os as _os
check(_os.path.isfile("assets/dungeon/followers/95_crystal.png"), "the Crystal Onix's own follower sheet (an Onix recoloured)")

# Forms on the summary page.
g.data.data["pokedex"] = {}
for pid in (12, 9103, 9501):
    g.data.add_pokemon(mkf(pid))
bf = mkf(12)
d = PokemonDetailState(g, bf, None); g.change_state(d)
names = [m.display_name for m in d.forms]
check(len(d.forms) == 3, f"Butterfree summary cycles 3 forms: {names}")
d.draw(); pygame.image.save(g.screen, os.path.join(S, "forms_1.png"))
d.cycle_form(1); d.draw(); pygame.image.save(g.screen, os.path.join(S, "forms_2.png"))
check(d.pokemon.form == "pinkan", f"next form: {d.pokemon.display_name}")
d.cycle_form(1); d.cycle_form(1)
check(d.pokemon is bf, "cycles back to your own Pokemon")
dex = PokedexState(g, None); g.change_state(dex)
dex.selected_pkmn_id = 9501
dex.show_selected_info()
check(type(g.current_state).__name__ == "DexEntryState" and g.current_state.pid == 9501,
      "the Pokedex opens its entry (Journeys' INFO / AREA / FORMS)")

evolved = Pokemon(g.loader.fetch_specific(95, form="crystal"), g.assets, size_mult=2.5); evolved.level = 60
check("HEAD-SMASH" in evolved.moves or "HEAD-SMASH" in evolution.known_moves(g, evolved), "an evolved Crystal Onix uses its own learnset")
print(f"##### orangeforms: {fails} fails")
