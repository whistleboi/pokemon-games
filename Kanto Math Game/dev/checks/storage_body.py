
from src.world.story import StoryManager
from src.states.systems import PokedexState, dex_regions


def go(area):
    """Travel like the game does; returns where you actually arrived and the extra lines."""
    t = ow.AreaTransitionState(g, area)
    return t.next_area_key, " ".join(t.dialogue_box.text_lines)


def ids(lst):
    return [p.id for p in lst if p]


print("1) A Kanto game")
story.region_stores, story.linked_regions = {}, set()
story.starting_region = "KANTO"
story.use_region_store("KANTO")
story.current_area_key = "VERMILLION_CITY"
story.story_flags = {"received_starter_kanto": True, "beat_champion": True}
story.badges = {"KANTO": ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"], "JOHTO": []}
story.visited_region_set = {"KANTO"}
story.player_team = [mk(6), mk(25)]
story.deposit_to_pc(mk(143))
story.inventory = {"POTION": 5, "SS_TICKET": 1, "SILPH_SCOPE": 1}
story.current_area_key = "VERMILLION_CITY"
check(story.active_store == "KANTO", "Kanto storage")

print("2) First trip to Johto")
arrived, said = go("OLIVINE_CITY")
check(arrived == "NEW_BARK_TOWN" and "professor" in said.lower(), f"no Johto starter yet: off to New Bark ({arrived})")
story.current_area_key = arrived
check(story.active_store == "JOHTO" and story.player_team == [] and ids(story.pc_pokemon) == [], "Johto: empty party and PC")
check(story.inventory == {"SS_TICKET": 1, "POKE_BALLS": 5},
      f"new Bag: the S.S. Ticket comes along, plus the region's own 5 Poke Balls {story.inventory}")
story.sync_key_items()
check("SILPH_SCOPE" not in story.inventory and "HM_FLY" not in story.inventory, "Kanto key items stay in Kanto")
check(ids(story.region_stores["KANTO"]["team"]) == [6, 25], "Kanto party waits in Kanto")
story.player_team.append(mk(155))
story.story_flags["received_starter_johto"] = True
arrived, said = go("JOHTO_ROUTE_29" if "JOHTO_ROUTE_29" in prog else "CHERRYGROVE_CITY")
check(story.active_store == "JOHTO" and ids(story.player_team) == [155], "inside Johto: same storage")

print("3) Back to Kanto and again")
story.current_area_key = "OLIVINE_CITY"
arrived, said = go("VERMILLION_CITY")
story.current_area_key = arrived
check(arrived == "VERMILLION_CITY" and ids(story.player_team) == [6, 25] and story.inventory.get("POTION") == 5,
      "Kanto party and Bag are back")
arrived, said = go("OLIVINE_CITY")
story.current_area_key = arrived
check(arrived == "OLIVINE_CITY" and ids(story.player_team) == [155], "Johto party again (no redirect now)")
story.current_area_key = arrived
story.inventory["SUPER_POTION"] = 3

print("4) The second title links Kanto and Johto")
story.story_flags["beat_johto_champion"] = True
story.badges["JOHTO"] = ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER", "RISING"]
story.current_area_key = "NEW_BARK_TOWN"
city = ow.CityState(g)
shown = []
city.show_message = lambda lines, callback=None: shown.append(lines)
city._offer_move = lambda *a, **k: shown.append(["MOVE OFFER"])
g.change_state(city)
city.start()
text = " ".join(" ".join(x) for x in shown)
check("PCs are now linked" in text, "Professor: your PCs are linked")
check(story.active_store == "LINKED" and story.linked_regions == {"KANTO", "JOHTO"}, "one linked storage")
check(ids(story.player_team) == [155] and set(ids(story.pc_pokemon)) == {6, 25, 143}, "Johto party stays; Kanto's go to the PC")
check(story.inventory.get("POTION") == 5 and story.inventory.get("SUPER_POTION") == 3
      and story.inventory.get("SS_TICKET") == 1, f"Bags combined {story.inventory}")
story.current_area_key = "NEW_BARK_TOWN"
arrived, _ = go("PALLET_TOWN")
check(story.active_store == "LINKED" and ids(story.player_team) == [155], "linked regions share everything")

print("5) A third region")
story.current_area_key = "PALLET_TOWN"
story.move_to_region("HOENN")
check(story.active_store == "HOENN" and story.player_team == [], "Hoenn: its own storage")
story.player_team.append(mk(255))
story.story_flags["received_starter_hoenn"] = True
story.current_area_key = "VALENCIA_ISLAND"
check(story.store_key("ORRE") == "HOENN", "Orre uses Hoenn's storage (Orange has its own since 10-27)")
story.current_area_key = "LITTLEROOT_TOWN"
story.story_flags["beat_hoenn_champion"] = True
story.badges["HOENN"] = ["x"] * 8
added = story.link_champion_regions()
check(added == ["HOENN"] and story.active_store == "LINKED" and 255 in ids(story.player_team)
      and {6, 25, 143, 155} <= set(ids(story.pc_pokemon) + ids(story.player_team)), "third title joins the link")

print("6) Saving and loading")
data = story.serialize()
s2 = StoryManager()
s2.game = g
s2.deserialize(data, g.loader)
check(s2.active_store == "LINKED" and s2.linked_regions == {"KANTO", "JOHTO", "HOENN"}
      and ids(s2.player_team) == ids(story.player_team), "regional storage survives a save")
old = dict(data)
for k in ("region_stores", "linked_regions", "active_store"):
    old.pop(k)
old["visited_regions"] = ["KANTO", "JOHTO"]
old["current_area_key"] = "PALLET_TOWN"
s3 = StoryManager()
s3.game = g
s3.deserialize(old, g.loader)
check(s3.active_store == "LINKED" and ids(s3.player_team) == ids(story.player_team), "old saves: everything visited stays together")

print("7) Regional Pokedexes")
story.starting_region = "KANTO"
story.story_flags = {"received_starter_kanto": True}
story.visited_region_set = {"KANTO", "JOHTO"}
story.story_flags["unlocked_johto_badges"] = True
check(dex_regions(story) == ["KANTO"], "arriving in Johto doesn't add its dex")
story.story_flags["received_starter_johto"] = True
check(dex_regions(story) == ["KANTO", "JOHTO"], "the Johto starter brings the Johto Dex")
story.current_area_key = "NEW_BARK_TOWN"
dx = PokedexState(g, ow.CityState(g))
check(dx.dex_view == "JOHTO" and dx.dex_views() == ["KANTO", "JOHTO", "NATIONAL"], f"opens on the Johto Dex: {dx.dex_views()}")
check([e["id"] for e in dx.full_dex][:2] == [152, 153] and len(dx.full_dex) >= 100, "Johto Dex starts at Chikorita")
dx.cycle_dex_view()
dx.cycle_dex_view()
check(dx.dex_view == "KANTO" and dx.full_dex[0]["id"] == 1 and len([e for e in dx.full_dex if e["id"] <= 151]) == 151,
      "Kanto Dex: #1-151")
dx.cycle_dex_view()
dx.cycle_dex_view()
check(dx.dex_view == "NATIONAL" and len(dx.full_dex) >= 251, f"National: both ({len(dx.full_dex)})")
dx.draw()

print("8) Arriving with no starter")
from src.states.menus import StarterSelectionState
story.region_stores, story.linked_regions = {}, set()
story.current_area_key = "VERMILLION_CITY"
story.game_started = True
story.story_flags = {"received_starter_kanto": True, "beat_champion": True}
story.player_team = [mk(6)]
t = ow.AreaTransitionState(g, "OLIVINE_CITY")
story.current_area_key = t.next_area_key
g.change_state(ow.CityState(g))
st = g.current_state
check(isinstance(st, StarterSelectionState) and st.region == "JOHTO", f"arrival opens the Johto starter choice ({type(st).__name__})")
story.player_team = [mk(155)]
story.story_flags["received_starter_johto"] = True
check(story.pending_starter() is None and "pending_starter" not in story.story_flags, "nothing pending once you have a starter")
g.change_state(ow.CityState(g))
check(isinstance(g.current_state, ow.CityState), "New Bark as normal afterwards")
print("FAILURES:", fails)
