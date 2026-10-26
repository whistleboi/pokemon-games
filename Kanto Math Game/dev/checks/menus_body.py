import pygame
from src.states.overworld import CityState
from src.states.systems import PCState, PokedexState, JournalState, BagState
fails = 0
def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m); fails += 0 if c else 1
def tap(st, pos):
    st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)])
story.current_area_key = "PALLET_TOWN"
a, b, c = mk(6), mk(25), mk(1)
story.player_team = [a, b, c]
story.pc_pokemon[:] = [None] * 300
story.pc_pokemon[0] = mk(16)
city = CityState(g); g.change_state(city)

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
check(len(dx.dex_btns) >= 1 and dx.PER_PAGE == 18, "Pokedex: 18 entries a page")
tap(dx, dx.btn_next.center)
check(dx.page == 1, "the > arrow turns the page")

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

print("Journal: a list and the picked mission in full")
from src.states.systems import JournalState
jn = JournalState(g, city); g.change_state(jn); jn.draw()
if len(jn.missions) > 1:
    tap(jn, jn.row_rect(1).center)
    check(jn.selected == 1, "tapping a mission shows it")
    jn.toggle_guide()
    from src.world import guide
    check((guide.tracked_mission(g) or {}).get("id") == jn.missions[1]["id"] and jn.btn_guide.text == "GUIDING",
          "GUIDE ME follows the picked mission")
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
print(f"##### menus: {fails} fails")
