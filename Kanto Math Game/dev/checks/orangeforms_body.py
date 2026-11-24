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
check(all(str(f) in pool for f in range(9101, 9137)), "Pinkan Island's pool: the listed lines, Scyther too (11-23: Quest Book's Orange Variants), with 5.7's own species")
cat = mkf(9101); cat.level = 7; cat.evo_due = True
ready = evolution.ready_evolutions(g, cat)
check(ready == ["METAPOD_PINKAN"], f"Pinkan Caterpie -> Pinkan Metapod: {ready}")
gloom = mkf(9119)
check(evolution.item_evolution(g, gloom, "LEAF_STONE") == ("VILEPLUME_PINKAN", 45), "Pinkan Gloom + Leaf Stone")
valencia = [k for k, v in FM.items() if v.get("form") == "valencia"]
check(len(valencia) == 17, f"17 Valencia variants: {len(valencia)}")
beach = g.loader.area_data["ORANGE_VALENCIA_PARK_PERCENTAGES"]
_evolved = {"9504", "9505", "9507", "9508", "9511", "9513", "9515"}   # (their earlier Valencia stage is in the park)
check(all(k in beach for k in valencia if k not in _evolved) and not _evolved & set(beach) and sum(beach.values()) == 100,
      "Valencia Park has each Valencia line's lowest stage only; Nidorina, Parasect... come by evolving (Jordan 11-24)")

# The Valencia Pokemon older than the park's Lv 6-15 meet you at their own levels, still rare (Jordan 11-24).
from src.world import levels as _lv
from src.dungeon import core as _core
_core.CURRENT_TILE = None
_lvs = {pid: {_lv.set_wild(g, mkf(pid), "VALENCIA_PARK").level for _ in range(40)} for pid in (9517, 9512, 9501, 9510)}
check(_lvs[9517] <= set(range(20, 23)) and _lvs[9512] <= set(range(25, 28)) and _lvs[9501] <= set(range(10, 16))
      and _lvs[9510] <= set(range(6, 16)) and beach["9517"] == 1,
      f"Valencia Park: Gyarados 20-22, Poliwhirl 25-27, Butterfree 10-15, Paras the park's 6-15, still 1-2% ({_lvs})")

# Eggs keep a Pinkan or Valencia colour from either parent (Jordan 11-24).
from src.pokemon import breeding


def _parent(pid, sex):
    m = mkf(pid); m.gender = sex
    return m


check(breeding.egg_species(g, _parent(9106, "F"), _parent(15, "M")) == 9104, "Pinkan Beedrill mother: a Pinkan Weedle Egg")
check(breeding.egg_species(g, _parent(46, "F"), _parent(9510, "M")) == 9510, "Valencia Paras father: a Valencia Paras Egg")
check(breeding.egg_species(g, _parent(9501, "F"), _parent(12, "M")) == 9501,
      "Valencia Butterfree (no Valencia Caterpie): the Egg is a Valencia Butterfree")
check(breeding.egg_species(g, _parent(9517, "F"), _parent(132, None)) == 9517, "Valencia Gyarados with Ditto keeps its colour")
check(breeding.egg_species(g, _parent(9505, "F"), _parent(34, "M")) == 9503, "Valencia Nidoqueen: a Valencia Nidoran-F Egg")
check(breeding.egg_species(g, _parent(13, "F"), _parent(15, "M")) == 13, "two plain parents: a plain Weedle")
_egg = breeding.make_egg(g, _parent(15, "F"), _parent(9106, "M"))
check(_egg.id == 9104 and getattr(_egg, "form", "") == "pinkan" and _egg.is_egg,
      f"the Day Care's Egg from a Pinkan father is a Pinkan Weedle: {_egg.id} {getattr(_egg, 'form', '')}")

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
# Pinkan / Valencia Mega Evolve like their species, in their own colours (Jordan 11-23).
from src.pokemon import forms as _forms
from src.states.battle import TrainerBattleState
from src.states.overworld.dungeon import follower_names
story.level_cap_mode = "NONE"
inv = story.inventory
for k in ("MEGA_BRACELET", "BEEDRILLITE", "GYARADOSITE"):
    inv[k] = 1
for pid, dex, var in ((9106, 15, "pinkan"), (9517, 130, "valencia")):
    me = mkf(pid); me.level = 50; me.current_hp = me.get_max_hp()
    f = _forms.player_form(g.assets, me, inv, False)
    check(bool(f) and f["form"] == "mega", f"{me.display_name} can Mega Evolve: {f and f['name']}")
    story.player_team = [me]
    b = TrainerBattleState(g, [mkf(19)], trainer_class="PKMN_TRAINER", trainer_name="Test")
    g.change_state(b)
    drive(b, 400)
    before = pygame.image.tostring(me.image, "RGBA")
    b.activate_player_form()
    check(b.form_armed is not None, f"the MEGA button arms {var}'s Mega")
    b._apply_transforms()
    check(me.form == "mega" and me.display_name.startswith(f"MEGA {var.upper()} "), f"in battle: {me.display_name}")
    plain = pygame.transform.scale(pygame.image.load(f"assets/sprites/pokemon/mega/{dex}_mega.png").convert_alpha(), me.image.get_size())
    check(pygame.image.tostring(me.image, "RGBA") not in (before, pygame.image.tostring(plain, "RGBA")),
          f"{var} Mega shows its own colours, not the plain Mega's")
    check(follower_names(g, me)[0] == f"{dex}_{var}_mega", f"on the map: {follower_names(g, me)[:2]}")
    b.draw(); pygame.image.save(g.screen, os.path.join(S, f"mega_{var}.png"))
    _forms.revert_form(me)
    check(me.form == var and _forms.player_form(g.assets, me, inv, False), f"after battle: {var} again")
print(f"##### orangeforms: {fails} fails")
