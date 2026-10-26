
import json, tempfile, os as _os
from src.ui.dialogue import ClassicDialogueBox
from src.ui.widgets import Button
from src.states.overworld import CityState, PlayState, GymLobbyState
from src.states.battle import TrainerBattleState, WildBattleState
from src.states.systems import BagState, PokeMartState, EvolutionState
from src.core.data import DataManager
from src.world import regional_forms
from src.pokemon import evolution
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def kanto_only():
    story.starting_region = "KANTO"
    story.visited_region_set = {"KANTO"}
    story.story_flags = {k: v for k, v in story.story_flags.items() if not k.startswith("unlocked_")}


prog = g.loader.area_data["STORY_PROGRESSION"]
font = g.assets.fonts["med"]

print("1) text boxes")
long = "This is a very long line of dialogue " * 12
box = ClassicDialogueBox(pygame.Rect(40, 500, 1000, 160), [long, "Line two"], font)
pages = len(box._pages(0))
check(pages > 1, f"long line split into {pages} pages that fit the box")
for _ in range(pages):
    box.advance(); box.advance()
check(box.current_line == 1, "line index only moves after the last page")
box.advance(); box.advance()
check(box.is_finished, "finished after the last line")
ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=box.rect.center)
check(not box.handle_event(ev), "a finished box lets taps through")
hits = []
btn = Button((0, 0, 200, 80), "A", font, lambda: hits.append("A"), autosize=False)
g.ui_manager.elements = [btn]
left = g.ui_manager.unconsumed([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 10)),
                                pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(900, 900))])
check(hits == ["A"] and len(left) == 1, "each tap is routed on its own; unused taps reach the screen")
og = g.show_dialogue(["Hi"])
og.advance(); og.advance()
check(not og.visible, "overlay message boxes close themselves")

print("2) bag messages")
p = mk(25); p.level = 20; p.current_hp = p.get_max_hp()
story.player_team = [p]; story.inventory["POTION"] = 1
bag = BagState(g, g.current_state); g.change_state(bag)
bag.on_pokemon_select_potion(0)
msgs = [e for e in g.ui_manager.elements if isinstance(e, ClassicDialogueBox) and e.visible]
check(g.current_state is bag and msgs and "full health" in msgs[-1].text_lines[0],
      f"'already at full health' is shown: {msgs[-1].text_lines if msgs else None}")

print("3) whiteout / region filter")
story.current_area_key = "HOENN_ROUTE_101"
story.story_flags["forced_white_out"] = True
story.player_team = [mk(258)]
b = WildBattleState(g, mk(263), "HOENN_ROUTE_101")
check("forced_white_out" not in story.story_flags and b.phase == "MENU", "stale forced_white_out is cleared; battle starts")
a = mk(258); a.current_hp = 0
story.player_team = [a]
b = WildBattleState(g, mk(263), "HOENN_ROUTE_101")
check(b.phase == "OUTRO" and not b.player_won, "an all-fainted party goes straight to the whiteout")
k = mk(25); k.caught_region = "KANTO"
h = mk(258); h.caught_region = "HOENN"
story.player_team = [h, k]; story.pc_pokemon = [mk(1)] * 300
TrainerBattleState(g, [mk(263)], trainer_class="HIKER", trainer_name="T")
check(k in story.player_team, "PC full: the other-region Pokemon stays in the party (not deleted)")
story.pc_pokemon = [None] * 300
TrainerBattleState(g, [mk(263)], trainer_class="HIKER", trainer_name="T")
check(k in story.player_team and k not in story.pc_pokemon,
      "PC has room: it still stays (regional storage separates regions now, not battles)")

print("4) saves")
import importlib, src.core.data as _cd
_cd = importlib.reload(_cd)  # the harness stubs save(); test the real one
tmpdir = tempfile.mkdtemp()
dm = _cd.DataManager(tmpdir)
dm.data["story"] = {"x": {1, 2}}  # a set used to crash json.dump half-way through
dm.save(); dm.data["story"] = {"x": 2}; dm.save()
with open(dm.save_file, "w") as f:
    f.write('{"broken"')
data, status = _cd.DataManager.read_json(dm.save_file)
check(status == "restored" and data["story"] == {"x": [1, 2]}, f"damaged save falls back to .bak: {status}")
story.pc_pokemon = [mk(1)] * 300
idx = story.deposit_to_pc(mk(4))
check(idx == 300, "a full PC still stores the Pokemon")
rec = story.serialize()
story.deserialize(rec, g.loader)
check(len(story.pc_pokemon) == 301 and story.pc_pokemon[300].id == 4, "PC slot 301 survives save + load")
story.pc_pokemon = [None] * 300

print("5) healing")
story.current_area_key = "HOENN_ROUTE_101"
pl = PlayState(g); g.change_state(pl)
z = mk(258); z.current_hp = 0
story.player_team = [z]
pl.check_team_hp()
boxes = [e for e in g.ui_manager.elements if isinstance(e, ClassicDialogueBox) and e.visible]
check(any("whited out" in " ".join(map(str, bb.text_lines)) for bb in boxes), "overworld whiteout fires when everyone fainted")
c = mk(4); c.level = 16; c.current_hp = 10
story.player_team = [c]
ev = EvolutionState(g, c, 5, 0, return_state=pl); g.change_state(ev); ev.evolve_yes()
for _ in range(400):
    ev.update()
    if ev.phase == "END":
        break
newmon = story.player_team[0]
check(newmon.id == 5 and newmon.current_hp < newmon.get_max_hp(), f"evolving keeps damage: {newmon.current_hp}/{newmon.get_max_hp()}")
x = mk(4); x.level = 10; x.current_hp = 20; mx = x.get_max_hp()
x.gain_xp(500)
check(x.current_hp == 20 + x.get_max_hp() - mx, "a level-up adds the HP it gained")

print("6) recoil and poison can knock out")
story.current_area_key = "HOENN_ROUTE_101"
me = mk(129); me.level = 30; me.moves = ["TACKLE"]
story.player_team = [me, mk(258)]
b = TrainerBattleState(g, [mk(92)], trainer_class="HIKER", trainer_name="T"); g.change_state(b)
b.player_hp = me.current_hp = 1
b._use_move(me, b.opponent_pokemon, "STRUGGLE", "A", "D", 999, 999)
check(b.player_hp == 0, "Struggle recoil can KO")
b.phase = "RESOLVE_TURN"; b.turn_actions = []; b.dialogue_box.visible = False; b.feedback_timer = 0
b.update()
check(b.fainting_side == "player" and b.phase == "MESSAGE", "a recoil KO starts the faint")
b2 = TrainerBattleState(g, [mk(19)], trainer_class="HIKER", trainer_name="T"); g.change_state(b2)
b2.opponent_pokemon.status = "poison"; b2.opponent_hp = 1
b2._status_chip()
check(b2.opponent_hp == 0, "poison can KO")

print("7) Kanto keeps other regions' Pokemon out")
kanto_only()
story.current_area_key = "KANTO_ROUTE_1"
pool = regional_forms.extend_pool(g, g.loader.area_data["KANTO_ROUTE_1_PERCENTAGES"])
check("2001" not in pool and "16" in pool, "no Alolan Rattata on Route 1 before Alola")
story.visited_region_set.add("ALOLA")
check("2001" in regional_forms.extend_pool(g, g.loader.area_data["KANTO_ROUTE_1_PERCENTAGES"]), "it appears after Alola")
kanto_only()
story.current_area_key = "KANTO_ROUTE_26"
check("194" not in regional_forms.extend_pool(g, g.loader.area_data["KANTO_ROUTE_26_PERCENTAGES"]), "no Wooper (Johto) in Kanto before Johto")
check(not g.loader._resolve_form_context(19, "normal", "RATTATA", {"alt_forms": {"enabled": True, "weights": {"19_alolan": 1.0}}})[0] == "alolan",
      "hand-placed Alolan forms wait too")
story.starting_region = "HOENN"; story.visited_region_set = {"HOENN"}; story.current_area_key = "HOENN_ROUTE_101"
kirlia = mk(281); kirlia.level = 40
check(475 in [t for _, t, _ in evolution.evolution_options(g, kirlia)], "Hoenn still allows Kirlia -> Gallade (its dex exception)")

print("8) Up-Grade")
kanto_only()
for area in ("CELADON_CITY", "GOLDENROD_CITY", "VIRIDIAN_CITY"):
    story.current_area_key = area
    check("UPGRADE" not in PokeMartState(g, None)._shop_items(), f"not sold at {area}")
por = mk(137); por.level = 30
check(evolution.item_evolution(g, por, "UPGRADE") is None, "Porygon2 locked in a Kanto-only game")
story.visited_region_set.add("JOHTO")
check(evolution.item_evolution(g, por, "UPGRADE") is not None, "Up-Grade works once Johto is visited")
story.current_area_key = "SILPH_CITY"; story.story_flags["silph_co_cleared"] = True
c = CityState(g); c.visit_silph_employee()
check(not story.inventory.get("UPGRADE") and "Veilstone" in " ".join(c.npc_dialogue.text_lines),
      "Silph employee points to Veilstone (no Kanto Up-Grade)")
story.current_area_key = "VEILSTONE_CITY"
check("UPGRADE" in PokeMartState(g, None)._shop_items(), "Veilstone Department Store sells the Up-Grade")

print("9) canon gates")
kanto_only(); story.badges["KANTO"] = []; story.inventory = {}
story.story_flags.pop("silph_co_cleared", None)


def town_opts(area, key):
    story.current_area_key = area
    c = CityState(g)
    return c, [o for o in prog[area][key] if c._check_menu_condition(o.get("condition")) if True]


c, opts = town_opts("PEWTER_CITY", "travel_options")
check("KANTO_ROUTE_3" not in [o["target_area"] for o in opts], "Pewter -> Route 3 closed before Brock")
story.badges["KANTO"] = ["BOULDER"]
c, opts = town_opts("PEWTER_CITY", "travel_options")
check("KANTO_ROUTE_3" in [o["target_area"] for o in opts], "open after the Boulder Badge")
c, opts = town_opts("CERULEAN_CITY", "travel_options")
check("KANTO_ROUTE_9" not in [o["target_area"] for o in opts], "Route 9 closed before Cut")
story.current_area_key = "KANTO_ROUTE_7"; p7 = PlayState(g); p7.rounds_completed = 9
sf = next(o for o in prog["KANTO_ROUTE_7"]["route_menu"] if o.get("target") == "SAFFRON_CITY")
check(not p7._check_route_condition(sf["condition"], False, sf), "Saffron gate closed without Tea")
story.current_area_key = "CELADON_CITY"; cc = CityState(g)
tea = next(o for o in prog["CELADON_CITY"]["explore_options"] if o["text"] == "Celadon Mansion")
cc._get_callback_for_option(tea)()
check(story.inventory.get("TEA") == 1, "Celadon Mansion gives Tea")
story.current_area_key = "KANTO_ROUTE_7"
check(p7._check_route_condition(sf["condition"], False, sf), "Saffron open with Tea")
for area, need in (("VERMILLION_CITY", "Cut"), ("SAFFRON_CITY", "Rocket"), ("CINNABAR_ISLAND", "key")):
    story.current_area_key = area; ci = CityState(g); g.change_state(ci); ci.start_gym_battle()
    check(type(g.current_state).__name__ == "CityState" and ci.npc_active, f"{area} gym closed ({need})")
story.current_area_key = "CINNABAR_ISLAND"; ci = CityState(g)
mansion = next(o for o in prog["CINNABAR_ISLAND"]["explore_options"] if o["text"] == "Pokemon Mansion")
story.player_team = [mk(9)]
ci._get_callback_for_option(mansion)()
bt = g.current_state.next_state
check(bt.opponent_team[-1].level == 36, "Mansion burglar battle")
bt.player_won = True; bt.exit_battle()
check(story.inventory.get("SECRET_KEY") == 1 and story.story_flags.get("got_secret_key"), "it gives the Secret Key")
story.current_area_key = "KANTO_ROUTE_16"; p16 = PlayState(g); p16.rounds_completed = 9
cy = next(o for o in prog["KANTO_ROUTE_16"]["route_menu"] if o.get("target") == "KANTO_ROUTE_17")
check(not p16._check_route_condition(cy["condition"], False, cy), "Cycling Road needs a Bicycle")

print("10) story triggers")
kanto_only(); story.badges["KANTO"] = []
story.story_flags.pop("defeated_rival_route22_early", None)
g.rival_name, g.rival_character = "GARY", "blue"
story.current_area_key = "KANTO_ROUTE_22"; p22 = PlayState(g)
g.change_state(p22)
intro = g.current_state
check(type(intro).__name__ == "TrainerIntroState" and intro.next_state.trainer_name == story.region_rivals["KANTO"]["name"],
      f"Route 22 rival appears at 0 badges: {getattr(getattr(intro, 'next_state', None), 'trainer_name', None)}")
story.current_area_key = "KANTO_ROUTE_11"; story.player_team = [mk(9)]
snor = mk(143)
wb = WildBattleState(g, snor, "KANTO_ROUTE_11", is_boss_battle=True)
wb.victory_flag = "KANTO_ROUTE_11_boss_defeated"
story.story_flags.pop("KANTO_ROUTE_11_boss_defeated", None)
wb.trigger_outro(True)
check(story.story_flags.get("KANTO_ROUTE_11_boss_defeated"), "knocking Snorlax out clears the road (no catch needed)")
story.badges["KANTO"] = []; story.story_flags.pop("viridian_rocket_defeated", None)
story.player_team = [mk(7)]; story.player_team[0].level = 5  # canon levels: a team that hasn't outgrown them
story.current_area_key = "VIRIDIAN_CITY"; vc = CityState(g); g.change_state(vc); vc.start_gym_battle()
rb = g.current_state.next_state
check(max(p.level for p in rb.opponent_team) <= 10, f"Viridian Team Rocket at fair levels: {[p.level for p in rb.opponent_team]}")
print(f"##### {fails} failures")
