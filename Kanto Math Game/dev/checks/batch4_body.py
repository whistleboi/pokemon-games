
from src.states import overworld as ow
from src.states.systems import (EvolutionState, PokeMartState, BagState, PokemonDetailState,
                                PokemonPartyMenuState)
from src.states.battle import TrainerBattleState, WildBattleState
from src.states.menus import MainMenuState
fails = 0
out = sys.argv[1] + "/shots4"
os.makedirs(out, exist_ok=True)


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def shot(name):
    g.current_state.draw()
    g.keyboard.draw(g.screen)
    pygame.image.save(g.screen, f"{out}/{name}.png")


def key(k):
    ev = pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")
    if not g.keyboard.handle(ev):
        g.current_state.handle_events([ev])


prog = g.loader.area_data["STORY_PROGRESSION"]
g.data.save = lambda *a, **k: None

print("1) two evolutions after one gym win")
story.current_area_key = "PEWTER_CITY"
a, b = mk(4), mk(7)
for p in (a, b):
    p.level = 16
    p.current_hp = p.get_max_hp()
story.player_team = [a, b]
bt = TrainerBattleState(g, [mk(74)], trainer_class="GYM_LEADER", trainer_name="Brock", area_name="PEWTER_CITY",
                        battle_type="gym", badge_reward="BOULDER")
g.change_state(bt)
bt.player_won = True
bt.exit_battle()
seen = []
for _ in range(4):
    st = g.current_state
    if not isinstance(st, EvolutionState):
        break
    seen.append(st.pokemon.name)
    st.evolve_yes()
    for _ in range(2000):
        if g.current_state is not st:
            break
        st.update()
check(len(seen) == 2 and isinstance(g.current_state, ow.GymLobbyState),
      f"both evolve, then the lobby: {seen} -> {type(g.current_state).__name__}")
check([p.name.upper() for p in story.player_team] == ["CHARMELEON", "WARTORTLE"],
      f"team now {[p.name for p in story.player_team]}")
# declining one must not loop
a, b = mk(4), mk(7)
for p in (a, b):
    p.level = 16
story.player_team = [a, b]
lobby = ow.GymLobbyState(g, None)
ow.evolve_ready_party(g, lobby)
g.current_state.evolve_no()
st = g.current_state
check(isinstance(st, EvolutionState) and st.pokemon is b, "after NO, the next Pokémon is asked")
st.evolve_no()
check(isinstance(g.current_state, ow.GymLobbyState), "after both NO, back to the lobby (no loop)")

print("2) hearts and summary")
p = mk(25)
p.level = 30
p.affection = 160
p.current_hp = p.get_max_hp()
story.player_team = [p, mk(1)]
story.current_area_key = "VIRIDIAN_CITY"
city = ow.CityState(g)
g.change_state(city)
g.change_state(PokemonPartyMenuState(g, city))
shot("party")
d = PokemonDetailState(g, p, city)
g.change_state(d)
shot("summary_info")
d.show_tab("STATS")
shot("summary_stats")
check(d.tab == "STATS" and p.moves, f"stats page with moves {p.moves}")

print("3) music")
m = g.music
check(m.tracks("town") == ["music_town.wav"], f"town: {m.tracks('town')}")
check(set(m.tracks("gym", "KANTO")) == {"music_gym.wav", "kanto_battle1.mp3"}, f"gym: {m.tracks('gym', 'KANTO')}")
check(all("wild" in t for t in m.tracks("wild", "JOHTO")) and m.tracks("wild", "JOHTO"), f"wild: {m.tracks('wild', 'JOHTO')}")
check(m.tracks("victory") == ["music_victory.wav"], "victory jingle")
played = []
m.play = lambda kind, force=False: played.append(kind)
m.for_state(ow.CityState(g))
m.for_state(TrainerBattleState(g, [mk(74)], trainer_class="GYM_LEADER", trainer_name="Brock",
                               area_name="PEWTER_CITY", battle_type="gym"))
m.for_state(TrainerBattleState(g, [mk(19)], trainer_class="YOUNGSTER", trainer_name="Joey", area_name="ROUTE_1"))
m.for_state(WildBattleState(g, mk(16), "KANTO_ROUTE_1"))
story.current_area_key = "KANTO_ROUTE_1"
m.for_state(ow.PlayState(g))
check(played == ["town", "gym", "trainer", "wild", "route"], f"per screen: {played}")
del m.play

print("4) mart")
story.current_area_key = "CELADON_CITY"
story.money = 5000
story.inventory.pop("POTION", None)
city = ow.CityState(g)
mart = PokeMartState(g, city)
g.change_state(mart)
mart.on_welcome_dialogue_end() if mart.phase == "DIALOGUE" else None
check("EVERSTONE" in mart._shop_items(), "Everstone on the shelf")
mart.init_purchase("POTION")
mart.change_qty(2)
shot("mart_qty")
mart.confirm_purchase()
check(story.inventory.get("POTION") == 3 and story.money == 4400, f"bought 3 potions ($200 each): {story.inventory.get('POTION')}, ${story.money}")
shot("mart_buy")
mart.set_mode("SELL")
check("POTION" in mart._sellable() and "TOWN_MAP" not in mart._sellable(), f"sell list {mart._sellable()[:6]}")
shot("mart_sell")
mart.init_purchase("POTION")
mart.max_qty()
mart.confirm_purchase()
check(story.inventory.get("POTION") == 0 and story.money == 4400 + 300, f"sold 3 for $300: ${story.money}")
story.inventory["POTION"] = 998
story.money = 10 ** 6
mart.set_mode("BUY")
mart.init_purchase("POTION")
mart.max_qty()
check(mart.qty == 1, f"max is 1 below the 999 cap: {mart.qty}")
mart.change_qty(5)
mart.confirm_purchase()
check(story.inventory["POTION"] == 999, "999 cap")

print("5) everstone")
c = mk(4)
c.level = 20
story.player_team = [c]
story.inventory["EVERSTONE"] = 1
bag = BagState(g, city)
g.change_state(bag)
bag.on_pokemon_select_everstone(0)
from src.pokemon import evolution
check(c.everstone and not evolution.ready_evolutions(g, c), "holding it blocks evolution")
rec = story._pokemon_record(c)
check(rec.get("everstone") is True, "saved with the Pokémon")
bag.on_pokemon_select_everstone(0)
check(not c.everstone and story.inventory["EVERSTONE"] == 1 and evolution.ready_evolutions(g, c), "taken back")

print("6) keyboard")
g.change_state(MainMenuState(g))
key(pygame.K_DOWN)
check(g.keyboard.active and g.keyboard.focus, "arrow shows a highlight")
shot("kb_title")
story.current_area_key = "VIRIDIAN_CITY"
city = ow.CityState(g)
g.change_state(city)
bag = BagState(g, city)
g.change_state(bag)
key(pygame.K_ESCAPE)
check(g.current_state is city, f"Esc leaves the Bag ({type(g.current_state).__name__})")
# a battle, by keyboard only
story.current_area_key = "KANTO_ROUTE_1"
pk = mk(25)
pk.level = 30
pk.current_hp = pk.get_max_hp()
story.player_team = [pk]
wb = WildBattleState(g, mk(16), "KANTO_ROUTE_1")
g.change_state(wb)
for _ in range(400):
    if wb.phase == "MENU" and not wb.dialogue_box.visible:
        break
    if wb.dialogue_box.visible:
        key(pygame.K_RETURN)
    wb.update()
check(wb.phase == "MENU", f"intro advanced with Enter ({wb.phase})")
g.keyboard.active = False
key(pygame.K_RIGHT)  # highlight the first button
cur = g.keyboard._current(g.keyboard._targets())
shot("kb_battle")
key(pygame.K_RETURN)
check(wb.phase == "MOVE_SELECT", f"Enter on MATH/FIGHT opens the moves ({wb.phase})")

print("7) Paldea")
sp = prog
check("EAST_PROVINCE_AREA_3" in sp and any(o.get("text") == "LURKING STEEL TITAN" for o in sp["EAST_PROVINCE_AREA_3"]["route_menu"]),
      "Orthworm lives in East Province Area 3")
check(not any(o.get("text") == "LURKING STEEL TITAN" for o in sp["EAST_PROVINCE_AREA_2"]["route_menu"]), "not Area 2")
check(any(t["target_area"] == "EAST_PROVINCE_AREA_3" for t in sp["LEVINCIA"]["travel_options"]), "Levincia leads there")
story.current_area_key = "EAST_PROVINCE_AREA_3"
check(story.get_current_region() == "PALDEA", "tagged Paldea")
ps = ow.PlayState(g)
g.change_state(ps)
check(ps.area_data.get("wild_pool_percentages") == "EAST_PROVINCE_AREA_3_PERCENTAGES", "has wild Pokémon")
names = set()
for _ in range(30):
    story.story_flags.pop("paldea_version", None)
    story.current_area_key = "ASADO_DESERT"
    ps = ow.PlayState(g)
    g.change_state(ps)
    boss = next(o for o in prog["ASADO_DESERT"]["route_menu"] if o.get("text") == "QUAKING EARTH TITAN")["boss"]
    ps.action_challenge_boss(dict(boss))
    if g.current_state is ps:  # the Titan's intro lines first
        intro = list(ps.dialogue_box.text_lines)
        cb = ps.dialogue_box.callback
        ps.dialogue_box.callback = None
        cb()
    st = g.current_state
    opp = getattr(st, "opponent_pokemon", None) or getattr(getattr(st, "next_state", None), "opponent_pokemon", None)
    names.add((story.story_flags.get("paldea_version"), opp.id if opp else type(st).__name__))
check(names == {("SCARLET", 984), ("VIOLET", 990)}, f"both versions happen: {names}")
bg = g.assets.get_random_battle_background("water", "CASSEROYA_LAKE")
check(bg is not None, "Casseroya Lake has a battle backdrop")
print("FAILURES:", fails)
