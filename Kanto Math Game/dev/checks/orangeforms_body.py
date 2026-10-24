
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
story.current_area_key = "PINKAN_RESERVE"
pinkan = {int(k): v["id"] for k, v in FM.items() if v.get("form") == "pinkan"}
check(len(pinkan) == 36, f"36 Pinkan forms: {len(pinkan)}")
pool = g.loader.area_data["ORANGE_PINKAN_RESERVE_PERCENTAGES"]
check(sum(pool.values()) == 100 and "9136" not in pool, "Pinkan Reserve pool: the listed lines (no Scyther)")
cat = mkf(9101); cat.level = 7
ready = evolution.ready_evolutions(g, cat)
check(ready == ["METAPOD_PINKAN"], f"Pinkan Caterpie -> Pinkan Metapod: {ready}")
gloom = mkf(9119)
check(evolution.item_evolution(g, gloom, "LEAF_STONE") == ("VILEPLUME_PINKAN", 45), "Pinkan Gloom + Leaf Stone")
valencia = [k for k, v in FM.items() if v.get("form") == "valencia"]
check(len(valencia) == 11, f"11 Valencia variants: {len(valencia)}")
beach = g.loader.area_data["ORANGE_VALENCIA_BEACH_PERCENTAGES"]
check(sum(beach.values()) == 100 and all(k in beach for k in valencia), "Valencia Beach has Ivy's variants")

# Crystal Onix: stats, types, its own learnset, and the Crystal Stone.
co = mkf(9201)
check(co.types == ["ROCK", "ICE"] and co.base_stats == {"HP": 70, "ATTACK": 90, "DEFENSE": 60, "SPECIAL-ATTACK": 110,
                                                         "SPECIAL-DEFENSE": 70, "SPEED": 110}, f"Crystal Onix: {co.base_stats}")
co.level = 60
check({"ICICLE-CRASH", "HEAD-SMASH", "POWER-GEM"} <= evolution.known_moves(g, co), "Crystal Onix's own moves")
onix = mkf(95)
check(evolution.item_evolution(g, onix, "CRYSTAL_STONE") == ("ONIX_CRYSTAL", 95), "Onix + Crystal Stone -> Crystal Onix")
check(evolution.item_evolution(g, onix, "METAL_COAT") == ("STEELIX", 208), "Steelix branch unchanged")
story.inventory["CRYSTAL_STONE"] = 1
story.player_team = [onix]
bag = BagState(g, None); g.change_state(bag)
bag.selected_item = "CRYSTAL_STONE"; bag.on_pokemon_select(0)
st = g.current_state
check(type(st).__name__ == "EvolutionState" and st.evolution_id == 95 and st.next_form == "crystal",
      f"using the stone starts the evolution: {type(st).__name__} {getattr(st, 'next_form', None)}")
mateo = next(o for o in SP["SUNBURST_ISLAND"]["explore_options"] if (o.get("event") or {}).get("flag") == "got_mateo_gift")
check(mateo["event"]["gift_item"].get("CRYSTAL_STONE") == 1, "Mateo gives a Crystal Stone")
story.current_area_key = "PUMMELO_ISLAND"
story.story_flags.pop("beat_orange_champion", None)
check("CRYSTAL_STONE" not in PokeMartState(g, None)._shop_items(), "Pummelo: no stone before the League")
story.story_flags["beat_orange_champion"] = True
check("CRYSTAL_STONE" in PokeMartState(g, None)._shop_items(), "Pummelo sells it after the League")
story.current_area_key = "CELADON_CITY"
check("CRYSTAL_STONE" not in PokeMartState(g, None)._shop_items(), "no department store sells it")

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
check(type(g.current_state).__name__ == "PokemonDetailState" and g.current_state.pokemon.form == "valencia",
      "Pokedex INFO opens the summary")

evolved = Pokemon(g.loader.fetch_specific(95, form="crystal"), g.assets, size_mult=2.5); evolved.level = 60
check("HEAD-SMASH" in evolved.moves or "HEAD-SMASH" in evolution.known_moves(g, evolved), "an evolved Crystal Onix uses its own learnset")
print(f"##### orangeforms: {fails} fails")
