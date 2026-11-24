import pygame
from src.states.overworld import CityState
from src.states.systems import PCState, PokedexState, JournalState, BagState
fails = 0
def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m); fails += 0 if c else 1
def tap(st, pos):
    st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)])
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())   # (Pallet is walked: the menus open from its map, 11-24)
story.enter_region("KANTO")
a, b, c = mk(6), mk(25), mk(1)
story.player_team = [a, b, c]
story.pc_pokemon[:] = [None] * 300
story.pc_pokemon[0] = mk(16)
city = walk_town("PALLET_TOWN", "KANTO_ROUTE_1", play=False)

print("PC (menu redesign): taps on the new layout move Pokemon as before")
pc = PCState(g, city); g.change_state(pc)
tap(pc, pc.party_slot(1).center)
check(pc.popup == ("party", 1) and pc.btn_pop_summary.visible, "tapping a Pokemon opens its menu")
tap(pc, (pc.box_rect.centerx, pc.box_rect.y + 30))
check(pc.popup is None, "tapping elsewhere closes the menu")
tap(pc, pc.party_slot(1).center); pc.popup_move(); tap(pc, pc.box_slot(5).center)
check(story.pc_pokemon[5] is b and b not in story.player_team, "party -> empty Box slot stores it")
tap(pc, pc.box_slot(0).center); pc.popup_move(); tap(pc, pc.party_slot(3).center)
check(story.player_team[-1].id == 16 and story.pc_pokemon[0] is None, "Box -> empty party slot takes it out")
tap(pc, pc.box_slot(5).center); pc.popup_move(); tap(pc, pc.box_slot(9).center)
check(story.pc_pokemon[9] is b and story.pc_pokemon[5] is None, "Box -> Box moves it")
pc.draw()
tap(pc, pc.box_slot(9).center); pc.popup_summary()
check(type(g.current_state).__name__ == "PokemonDetailState" and g.current_state.pokemon is b,
      "SUMMARY in the PC menu opens its summary")
g.current_state.go_back()
pc.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=5, pos=(600, 300))])
check(pc.box_index == 1, "the wheel turns to the next Box")
pc.draw()

print("The other menus draw in the new frame")
for cls in (PokedexState, JournalState, BagState):
    st = cls(g, city); g.change_state(st); st.update(); st.draw()
    check(True, f"{cls.__name__} draws")
dx = PokedexState(g, city); g.change_state(dx); dx.draw()
from src.states.systems.pokedex import DexEntryState as _DE, DexSearchState as _DS, ROWS_SHOWN as _RS
check(len(dx.full_dex) >= 1 and _RS == 10 and dx.frame.k > 1, "Pokedex (Journeys' look): a list of 10 rows, scaled up")
check(not hasattr(dx, "tab_buttons"), "no MEGA / GMAX / ALT / BOSS / UNOWN tabs any more")
_seen = next((k for k, e in enumerate(dx.full_dex) if e.get("status", 0) > 0), None)
if _seen is not None:
    _e = _DE(g, dx, _seen)
    for _pg in (1, 2, 3):
        _e.page = _pg
        _e.draw()
    check(_e.forms and _e.forms[0][3], "an entry: INFO, AREA and FORMS draw; FORMS lists its looks")
_s = _DS(g, dx)
_s.s["type1"] = 2  # Flying
_s.begin()
check(all("FLYING" in [t.upper() for t in (g.assets.movesets.get(str(e["id"])) or {}).get("types", [])]
          or "FLYING" in [t.upper() for t in (g.assets.movesets.get(str(dx._species(e["id"]))) or {}).get("types", [])]
          for e in dx.full_dex), "SEARCH: Flying types only")
dx.go_back()
check(dx.search is None, "BACK from search results: the whole dex again")
dx.toggle_shiny_filter()
check(all(e.get("shiny") for e in dx.full_dex), "the shiny star: your shinies only")
dx.toggle_shiny_filter()
dx.draw()
from src.states.systems.pokedex import GEN_ORDER as _GO, gen_rank as _gr
_story = g.story_manager
_old_vis = set(_story.visited_region_set)
_story.visited_region_set |= {"ORANGE", "ORRE"}
_views = dx.dex_views()
check([v for v in _views if v != "NATIONAL"] == sorted([v for v in _views if v != "NATIONAL"], key=_gr)
      and "ORANGE" in _views and "ORRE" in _views, "the dexes in generation order (Orange after Johto, Orre after Hoenn)")
_v0 = dx.dex_view
tap(dx, dx.title_hits[">"].center)
check(dx.dex_view == _views[(_views.index(_v0) + 1) % len(_views)], "the title's right arrow: the next dex")
tap(dx, dx.title_hits["<"].center)
check(dx.dex_view == _v0, "its left arrow: back again")
tap(dx, dx.title_hits["name"].center)
check(dx.picking is not None, "the dex's name: the list of dexes")
dx.draw()
_pick = dict(dx._pick_rects())
tap(dx, _pick["ORANGE"].center)
check(dx.dex_view == "ORANGE" and dx.picking is None and dx.full_dex, "pick the Orange Islands: what lives there")
dx.set_dex_view(_v0)
_story.visited_region_set = _old_vis
if _seen is not None:
    _e = _DE(g, dx, _seen)
    _e.page = 1
    tap(_e, _e.frame.r(312, 4, 30, 26).center)
    check(_e.page == 2, "an entry's right arrow: the next page")
    tap(_e, _e.frame.r(14, 4, 30, 26).center)
    tap(_e, _e.frame.r(14, 4, 30, 26).center)
    check(_e.page == 3, "its left arrow: back, round to FORMS")
if len(dx.full_dex) > 10:
    tap(dx, dx.frame.r(468, 346, 40, 30).center)
    check(dx.top == 10, "the scroll bar's down arrow: the next 10")
tap(dx, dx._row_rect(dx.top + 1).center)
check(dx.index == dx.top + 1, "tapping a row picks it")

print("Party menu: the tap menu closes when tapping away, moves to another Pokemon")
from src.states.systems import PokemonPartyMenuState
pm = PokemonPartyMenuState(g, city); g.change_state(pm)
pm._slot_clicked(0)
check(pm.popup_active and pm.selected_slot_index == 0, "tapping a Pokemon opens its menu")
pm._slot_clicked(1)
check(pm.popup_active and pm.selected_slot_index == 1, "tapping another moves the menu there")
pm.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(5, 5))])
check(not pm.popup_active, "tapping away closes it")
pm.draw()

print("Summary: the STATS bars judge the stats; SHOW IVs switches")
from src.states.systems import PokemonDetailState
sm = PokemonDetailState(g, a, city); g.change_state(sm); sm.show_tab("STATS"); sm.draw()
check(sm.stat_view == "STATS" and sm.view_rect is not None, "stats view first")
sm.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=sm.view_rect.center)])
check(sm.stat_view == "IVS", "SHOW IVs switches to the IVs")
check(0 < sm.stat_rating("ATTACK", a.stat_value("ATTACK")) <= 1, "a stat's rating is a share")

from src.ui.theme import pokemon_word
check(pokemon_word("CATCH WILD PKMN") == "CATCH WILD POKéMON" and pokemon_word("All your PKMN are ours!")
      == "All your Pokémon are ours!", "PKMN is written out")

print("Kanto's own soundtrack (from Pokemon Journeys)")
import os
from src.core.music import MusicManager
mm = MusicManager(g)
story.current_area_key = "PALLET_TOWN"
check(str(mm.kanto_track("town", "KANTO")).endswith("pallet_town.mp3"), "Pallet Town plays its theme")
story.current_area_key = "KANTO_ROUTE_5"
check(str(mm.kanto_track("route", "KANTO")).endswith("route_3.mp3"), "Route 5 shares Route 3's theme")
check(str(mm.kanto_track("wild", "KANTO")).endswith("wild_pokemon_battle.mp3"), "Kanto wild battle theme")
check(str(mm.kanto_track("title", "JOHTO")).endswith("hall_of_fame.mp3"), "the title screen theme")
check(mm.kanto_track("town", "JOHTO") is None, "other regions keep their own music")
from src.states.menus import RegionSelectionState
check("Sevii Islands" in RegionSelectionState.SUB_REGIONS["KANTO"], "the region cards list their sub-regions")

print("Journal (the Quest Book, 11-22): a list and the picked row in full")
from src.states.systems import JournalState
jn = JournalState(g, city); g.change_state(jn); jn.set_tab("SIDE"); jn.draw()
live = [k for k in range(min(jn.ROWS, len(jn.rows) - jn.scroll_idx)) if (jn.missions[jn.scroll_idx + k] or {}).get("status") == "ACTIVE"]
if live:
    k = live[-1]
    tap(jn, jn.row_rect(k).center)
    check(jn.selected == jn.scroll_idx + k, "tapping an errand shows it")
    jn.toggle_guide()
    from src.world import guide
    check((guide.tracked_mission(g) or {}).get("id") == jn.missions[jn.selected]["id"] and jn.btn_guide.text == "GUIDING",
          "GUIDE ME follows the picked errand")
jn.draw()

print("The rest of the Kanto soundtrack: screen themes and fanfares")
from src.core import music as mus
cues = {name: [n for p, n in mus.JINGLE_CUES if p.search(name)][:1] for name in (
    "PIKACHU grew to Lv 12!", "You received the Boulder Badge!", "You received the OLD ROD!",
    "Your CHARMANDER evolved into CHARMELEON!", "YOU CAUGHT PIDGEY!", "You picked 2 Oran Berries!")}
check(cues == {"PIKACHU grew to Lv 12!": ["level_up"], "You received the Boulder Badge!": ["earn_gym_badge"],
               "You received the OLD ROD!": ["key_item"], "Your CHARMANDER evolved into CHARMELEON!": ["congrats_evolve"],
               "YOU CAUGHT PIDGEY!": ["pokemon_caught"], "You picked 2 Oran Berries!": ["picked_up_an_item"]},
      f"lines cue their fanfares {cues}")
for kind in ("center", "lab", "oak", "home", "game_corner", "evolution", "enc_male", "enc_female", "enc_rocket",
             "enc_rival", "enc_jessie"):
    check(mm.kanto_track(kind, "JOHTO") is not None, f"{kind} has its track (any region)")
class _B: pass
b1 = _B(); b1.trainer_class, b1.trainer_name = "LASS", "Lass Ann"
b2 = _B(); b2.trainer_class, b2.trainer_name = "ROCKET", "Jessie and James"
b3 = _B(); b3.trainer_class, b3.trainer_name = "GYM_LEADER", "Brock"
check((mm.encounter_kind(b1), mm.encounter_kind(b2), mm.encounter_kind(b3)) == ("enc_female", "enc_jessie", None),
      "encounter themes by trainer")
_kinds = {}
for _c in ("AROMA LADY", "SWIMMER♀", "PSYCHIC♀", "PICNIKER", "OFFICE_LADY", "POKÉFAN♂", "HIKER", "TEAM_SNAGEM"):
    _b = _B(); _b.trainer_class, _b.trainer_name = _c, "X"
    _kinds[_c] = mm.encounter_kind(_b)
check([_kinds[c] for c in _kinds] == ["enc_female"] * 5 + ["enc_male", "enc_male", "enc_rocket"],
      f"class names however a region spells them (spaces, the female sign, Picniker; Snagem a villain) {_kinds}")
check(mm.kanto_track("hall_of_fame", "HOENN").endswith("hall_of_fame.mp3"), "the Hall of Fame theme has its track (any region)")
_plays = []
_real_play = mm.play
mm.play = lambda kind, force=False: (_plays.append(kind), setattr(mm, "kind", kind))
mm.hall_of_fame()
mm.play = _real_play
check(_plays == ["hall_of_fame"] and mm.hof_until > pygame.time.get_ticks(), "a Champion win plays the Hall of Fame theme")
mm.kind = "hall_of_fame"
import pygame as _pg
_was = _pg.mixer.get_init
_pg.mixer.get_init = lambda: True
mm.play("town")
check(mm.pending == "town" and mm.kind == "hall_of_fame", "...held over the trip home (the town's music waits)")
mm.hof_until, _again = 0, []
mm.play = lambda kind, force=False: _again.append(kind)
mm.update()
mm.play = _real_play
_pg.mixer.get_init = _was
check(_again == ["town"], "...then the town's music comes back")

print("10-26 batch: Fly, gym MENU, keyboard, PC names, Hoenn opening, ribbons")
from src.states import overworld as ow
gl = walk_town("PEWTER_CITY", "KANTO_ROUTE_2", room="gym")   # (walked: inside Brock's Gym)
_hm = None
if [b.text for b in gl.hud_buttons] == ["MENU"]:
    gl.hud_buttons[0].callback(); _hm = g.current_state
check(getattr(gl, "room", None) == "gym" and _hm is not None and {"BAG", "POKEMON"} <= {t.label for t in getattr(_hm, "tiles", [])},
      "Gyms have the MENU (Bag, Pokemon...)")
g.change_state(city)
check(not any(t[2] in ("PC", "SAVE", "LOAD") for t in g.keyboard._targets()), "arrow keys skip the old hidden buttons")
check(story.PC_NAMES["HOENN"] == "Lanette's PC" and "Galar PC" == story.PC_NAMES.get("GALAR", "Galar PC"),
      "each region names its PC")
from src.ui.theme import pokemon_word
check("PC" in pokemon_word("PIKACHU was sent to BILL'S PC!"), "the text box names the region's PC")
from src.world import hms
check("AIR_BALLOON" not in story.FLY_ITEMS and hms.hm_for_badge("KANTO", "RAINBOW") is None, "Fly is HM Fly in Kanto (from the Route 16 house, not a badge)")
ms = {m["id"]: m for m in __import__("json").load(open("assets/hoenn_area_data.json", encoding="utf-8"))["JOURNAL_MISSIONS"]}
check(all(k in ms for k in ("hoenn_m1", "hoenn_m1b", "hoenn_m2", "hoenn_m2b", "hoenn_m2c", "hoenn_m3")),
      "Hoenn's opening has a mission for each step")
from src.states import contest as _ct
rc = _ct.RibbonCaseState(g, city); g.change_state(rc); rc.draw()
check(True, "the ribbon case draws")
# ---- the out-of-work Move Reminder and Move Deleter (Jordan 11-18: kept, with a pool of cheeky grumbles)
import json as _jq
from src.world import quips as _quips
from src.states.overworld import common as _cq
_found = []
for _f in ("hoenn_area_data.json", "johto_area_data.json", "orange_area_data.json", "sinnoh_area_data.json", "town_maps.json"):
    def _w(o):
        if isinstance(o, dict):
            if isinstance(o.get("event"), dict) and o["event"].get("quips"):
                _found.append((str(o.get("text")), o["event"]))
            for v in o.values():
                _w(v)
        elif isinstance(o, list):
            for v in o:
                _w(v)
    _w(_jq.load(open(os.path.join("assets", _f), encoding="utf-8")))
check(len(_found) == 9 and all(e["quips"] == ("move_reminder" if t in ("Move Reminder", "Move Maniac") else "move_deleter") for t, e in _found),
      f"all nine Move Reminders and Deleters grumble, Sinnoh's and Two Island's Move Maniac too ({sorted(t for t, _ in _found)})")
_mm = next(e for t, e in _found if t == "Move Maniac")
_said_mm = []
_cq._run_story_event(g.current_state, dict(_mm), lambda c: True, lambda ls: _said_mm.append(ls))
check(_said_mm and _said_mm[0][0].startswith("Move Maniac:"), f"Two Island: FireRed's Move Maniac says it as himself ({_said_mm[0][:1] if _said_mm else None})")
_said = []
for _ in range(12):
    _cq._run_story_event(g.current_state, dict(_found[0][1]), lambda c: True, lambda ls: _said.append(tuple(ls)))
_kind = _found[0][1]["quips"]
check(all(list(x) in _quips.POOLS[_kind] for x in _said) and len(set(_said)) >= 3,
      f"{_found[0][0]}: a line from its own pool each time, not always the same ({len(set(_said))} different in 12)")
check(all(len(l) <= 120 for pool in _quips.POOLS.values() for q in pool for l in q), "every grumble fits the text box (120 characters a line at most)")
# ---- the Name Rater (Jordan 11-18: the only way to nickname; only Pokemon you caught)
print("The Name Rater")
from src.states.systems import name_rater as _nr
_raters = []
for _f in ("hoenn_area_data.json", "johto_area_data.json", "sinnoh_area_data.json", "town_maps.json"):
    def _w2(o, where):
        if isinstance(o, dict):
            if isinstance(o.get("event"), dict) and o["event"].get("name_rater"):
                _raters.append((where, o["event"]))
            for k, v in o.items():
                _w2(v, k if k.isupper() and k != "STORY_PROGRESSION" else where)
        elif isinstance(o, list):
            for v in o:
                _w2(v, where)
    _w2(_jq.load(open(os.path.join("assets", _f), encoding="utf-8")), "")
_towns = sorted({w for w, _ in _raters})
check({"LAVENDER_TOWN", "GOLDENROD_CITY", "SLATEPORT_CITY", "ETERNA_CITY", "SUNBURST_ISLAND"} <= set(_towns),
      f"Name Raters in Lavender, Goldenrod, Slateport, Eterna and Sunburst ({_towns})")
_tm = _jq.load(open("assets/town_maps.json", encoding="utf-8"))
check(_tm["SLATEPORT_CITY"]["inside"].get("5,19") == "rater" and _tm["SLATEPORT_CITY"]["rooms"]["rater"]["people"][0]["event"].get("name_rater"),
      "Slateport: Emerald's Name Rater's house behind its own door (5,19)")
check(_tm["ETERNA_CITY"]["inside"].get("59,36") == "rater" and "Name Rater" in _tm["ETERNA_CITY"]["rooms"]["rater"]["people"],   # (11-19: the Condominiums' residents live there too)
      "Eterna: the Condominiums' ground floor, the Name Rater inside (Platinum)")
_ev = next(e for w, e in _raters if w == "LAVENDER_TOWN")
_p1, _p2, _p3 = mk(25), mk(1), mk(4)
_p2.traded = True
story.player_team = [_p1, _p2, _p3]
_said_nr = []
_say = lambda ls: _said_nr.append(list(ls))
city.show_message = lambda lines, callback=None: (_said_nr.append(list(lines)), callback and callback())
_cq._run_story_event(city, dict(_ev), lambda c: True, _say)
_pm = g.current_state
check(type(_pm).__name__ == "PokemonPartyMenuState" and _pm.context == "rename" and _said_nr and "Name Rater" in _said_nr[0][0],
      "talking to him: his lines, then the party list to pick from")
_pm.on_select(1)
check(g.current_state is city and any("trade" in l for l in _said_nr[-1]) and _p2.nickname is None,
      "a Pokemon from a trade keeps its first Trainer's name")
_cq._run_story_event(city, dict(_ev), lambda c: True, _say)
g.current_state.on_select(0)
_box = g.current_state
check(type(_box).__name__ == "NameRaterState", "picking one you caught opens the name box")
for ch in "Sparky":
    _box.handle_events([pygame.event.Event(pygame.KEYDOWN, key=0, unicode=ch)])
_box.draw()
_box.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r")])
check(_p1.nickname == "Sparky" and _p1.display_name == "Sparky" and _p1.species_name.upper() == "PIKACHU" and g.current_state is city,
      f"typing a name and OK: it's called that now ({_p1.display_name}, still a {_p1.species_name})")
_rec = story._pokemon_record(_p1)
_back = story._load_pokemon(_rec, g.loader)
check(_back.nickname == "Sparky" and _back.display_name == "Sparky", "the nickname is saved and loads back")
_back2 = story._load_pokemon(story._pokemon_record(_p2), g.loader)
check(_back2.traded, "a traded Pokemon stays marked as traded after a save")
_rai = story.change_species(_p1, 26)
check(_rai.display_name == "Sparky" and _rai.species_name.upper() == "RAICHU", "evolving keeps the nickname (Raichu called Sparky)")
from src.states.systems.evolution_scene import EvolutionState as _Evo
import inspect as _insp
check('"nickname", "traded"' in _insp.getsource(_Evo), "the evolution screen carries the nickname over too")
_dit = mk(132); _dit.nickname = "Blob"
_dit.transform_into(mk(6)); _mid = _dit.display_name
_dit.undo_transform()
check(_mid == "Blob" and _dit.display_name == "Blob" and _dit.species_name.upper() == "DITTO",
      "a nicknamed Ditto keeps its name through Transform, and is a Ditto again after")
_cq._run_story_event(city, dict(_ev), lambda c: True, _say)
g.current_state.on_select(0)
_box = g.current_state
_box.text = ""
_box.confirm()
check(_p1.nickname is None and _p1.display_name.upper() == "PIKACHU", "an empty name gives it back its species' name")
_cq._run_story_event(city, dict(_ev), lambda c: True, _say)
g.current_state.on_select(0)
g.current_state.text = "Zap"; g.current_state.cancel()
check(_p1.nickname is None and g.current_state is city, "CANCEL leaves the name as it was")
_egg = mk(172); _egg.is_egg = True; story.player_team.append(_egg)
_cq._run_story_event(city, dict(_ev), lambda c: True, _say)
g.current_state.on_select(3)
check(g.current_state is city and any("Egg" in l for l in _said_nr[-1]), "an Egg can't be named yet")
del city.show_message
check(_nr.MAX_LEN == 12, "names up to 12 letters")
print(f"##### {fails} failures")
