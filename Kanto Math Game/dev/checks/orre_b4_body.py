# Orre batch 4 played (11-20, kanto_handoff/orre_check/BATCH_4.md): Pyrite's jail and lift, The Under (Kids Grid, Silva, the
# disks, Venus), the new subway (stairway, station, train ride, the blown door), the windmill's Time Flute, the Shadow Pokemon
# Lab (shutter, keys, DNA, Skrub, Ein, the Data ROM to Nett). bash dev/checks/run_par.sh orre_b4
# Fateen, Agate Village, the Relic Cave and Skrub, purifying at the Relic Stone. bash dev/checks/run_par.sh orre_b2
import json as _json
from src.states.overworld import CityState as _CS, PlayState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.dungeon import core
from src.pokemon import catching
from src.world import shadow

fails = []
g.dungeon_routes = True
g.walk_towns = True
said = []


exec(open("dev/checks/orre_lib.py", encoding="utf-8").read())   # (meet, _fight, route, step_into_zone, town, _note, frames, check, mine, scenes_done: shared, Checks C5)


def play(n=3000):
    quiet = 0
    for _ in range(n):
        st = g.current_state
        if type(st).__name__ == "PokemonPartyMenuState" and getattr(st, "on_select", None):   # (one fainted: send in the next able)
            nxt = next((i for i, p in enumerate(story.player_team) if p and p.current_hp > 0 and p is not getattr(getattr(st, "previous_state", None), "player_pokemon", None)), 0)
            st.on_select(nxt)
            continue
        if hasattr(st, "math_ui") and hasattr(st, "phase"):
            _fight(st); quiet = 0
        elif getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))]); quiet = 0
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st); st.dialogue_box.advance(); quiet = 0
        elif getattr(getattr(st, "scenes", None), "playing", None):
            quiet = 0
        else:
            quiet += 1
            if quiet > 40:
                return
        st.update(); st.draw()


_MV = _json.load(open("assets/moves.json", encoding="utf-8"))
story.story_flags = {k: True for k in ("orre_opening_seen", "orre_beat_willie", "orre_rui_joined", "got_snag_machine", "received_starter_orre",
                                        "orre_power_on", "has_pyrite_badge", "orre_miror_cave", "met_agate_elder", "orre_beat_skrub",
                                        "orre_dakim_mt_battle", "orre_f_disk", "orre_time_flute")}
F = story.story_flags
story.badges = {"ORRE": ["PYRITE"]}
story.inventory = {"SNAG_MACHINE": 1, "POKE_BALL": 80, "F_DISK": 1}
story.player_team = [mk(196), mk(197), mk(150)]
for p in story.player_team:
    p.level = 100
    p.heal_full()
TR = _json.load(open("dev/builders/data/orre_trainers.json", encoding="utf-8"))
SP = g.loader.area_data["STORY_PROGRESSION"]
TM = _json.load(open("assets/town_maps.json", encoding="utf-8"))


def under(floor):
    p = route("THE_UNDER", "PYRITE_BUILDING", floor=floor)
    scenes_done()
    return g.current_state


def bar_met(area, floor, tile):
    p = g.current_state
    bar = next(b for b in TM[area]["floors"][floor]["barred"] if list(tile) in b["tiles"]) if tile else TM[area]["floors"][floor]["barred"][0]
    return p._until_met(bar["until"])


print("1) The disc's trainers in our data")
bad = sorted({mv for b in TR.values() for ms in b.get("team_moves", []) for mv in ms if mv not in _MV})
check(not bad, f"every move one the game knows ({bad})")
up = [t["name"] for t in SP["THE_UNDER"]["trainer_pool"]]
lp = [t["name"] for t in SP["SHADOW_PKMN_LAB"]["trainer_pool"]]
check(len(up) == 6 and "Rider Nelis" in up and len(lp) == 12 and "Researcher Kotan" in lp and "Cipher Peon Tanie" in lp,
      f"The Under's 6 and the Lab's 12 ({len(up)}, {len(lp)})")
ven = next(o for o in SP["THE_UNDER"]["route_menu"] if o["text"] == "SHUT DOWN THE UNDER")["event"]["battle"]
ein = next(o for o in SP["SHADOW_PKMN_LAB"]["route_menu"] if o["text"] == "SHADOW POKEMON LAB: EIN")["event"]["battle"]
check(ven["team"][0] == 9398 and ven["levels"] == [25, 26, 26, 26, 26], f"Venus: Shadow Suicune 25, then Lv 26 - stage levels, L1 11-24 ({ven['levels']})")
check(ein["team"][0] == 9396 and ein["levels"] == [26, 28, 28, 28, 28], f"Ein: Shadow Raikou 26, then Lv 28 - stage levels, L1 11-24 ({ein['levels']})")
kanto = {s["id"] for s in SP["SHADOW_PKMN_LAB"]["shadow_pool"]}
check({9432, 9438, 9435} <= kanto, "Jordan's Shadow Bulbasaur, Charmander and Squirtle still in the Lab")

print("2) Pyrite: the jail, Reath's Elevator Key, Kai at the lift")
t = town("PYRITE_TOWN", "AGATE_VILLAGE")
said_r = meet(t, "Miror B. Peon Reath (asleep)") or []
check(not F.get("orre_elevator_key") and any("locked" in ln for ln in said_r), "the cell's locked without the Jail Key")
F["orre_got_jail_key"] = True
story.inventory["JAIL_KEY"] = 1
t = town("PYRITE_TOWN", "AGATE_VILLAGE")
meet(t, "Miror B. Peon Reath (asleep)")
check(F.get("orre_elevator_key") and story.inventory.get("ELEVATOR_KEY") == 1, "Reath's Elevator Key, lifted while she sleeps")
p = route("PYRITE_BUILDING", "PYRITE_TOWN")
check(not bar_met("PYRITE_BUILDING", 0, None), "the lift won't go while Kai guards it")
meet(g.current_state, "CHASER KAI AT THE LIFT")
p = route("PYRITE_BUILDING", "PYRITE_TOWN")
check(F.get("orre_kai_lift") and bar_met("PYRITE_BUILDING", 0, None), "Kai beaten: the lift goes down")

print("3) The Under: the Kids Grid, Silva, the disks, Venus")
under(0)
check(F.get("orre_under_spies"), "arriving: Venus's broadcast about spies plays")
under(5)
meet(g.current_state, "BOY WITH A PART")
check(story.inventory.get("POWER_UP_PART") == 1, "the boy in the Junk Shop gives the Power Up Part")
under(8)
meet(g.current_state, "NETT")
check(F.get("orre_kids_grid") and not story.inventory.get("POWER_UP_PART"), "Nett takes it: the Kids Grid is back on")
under(0)
meet(g.current_state, "CIPHER PEON KLOAK")
meet(g.current_state, "CIPHER PEON DAGUR")
check(F.get("orre_under_kloak") and F.get("orre_under_dagur") and F.get("snagged_shadow_ledian"), "Silva's guards beaten, Shadow Ledian snagged")
under(0)
meet(g.current_state, "SILVA")
check(F.get("orre_r_disk") and story.inventory.get("R_DISK") == 1, "Silva passes the R-Disk through the bars")
p = under(0)
studio = TM["THE_UNDER"]["floors"][0]["barred"][0]
check(p._until_met(studio["until"]), "F and R: the floating platform reaches the studio")
under(1)
meet(g.current_state, "SHUT DOWN THE UNDER")
check(F.get("cleared_the_under") and F.get("snagged_shadow_suicune"), "Venus beaten, Shadow Suicune snagged")
for it, inv, n in (("RARE CANDIES", "RARE_CANDY", 3), ("EIN FILE F", "EIN_FILE_F", 1)):
    under(1)
    before = story.inventory.get(inv, 0)
    meet(g.current_state, it)
    check(story.inventory.get(inv, 0) == before + n, f"{it} picked up")

print("4) The subway")
under(2)
check(F.get("orre_venus_fled"), "the studio basement: Venus runs for the stairs")
p = under(10)
on = {m.payload[1].get("name") for m in p.run.floor.movers if m.kind == "trainer"}
check({"Hunter Frena", "Chaser Liaks", "Bodybuilder Lonia", "Rider Nelis"} <= on, f"the four on the stairway ({sorted(on)})")
for who in ("Hunter Frena", "Chaser Liaks", "Bodybuilder Lonia", "Rider Nelis"):
    under(10)
    meet(g.current_state, who)
check(all(F.get(f"snagged_shadow_{n}") for n in ("gligar", "stantler", "piloswine", "sneasel")), "Shadow Gligar, Stantler, Piloswine, Sneasel snagged")
under(10)
meet(g.current_state, "ULTRA BALLS")
check(story.inventory.get("ULTRA_BALL", 0) >= 4, "4 Ultra Balls on the last landing")
under(11)
check(F.get("orre_venus_station"), "the station: Venus and a peon run off over the tracks")
said_t = meet(g.current_state, "SUBWAY TRAIN") or []
check(any("locked" in ln for ln in said_t), "the train won't go without its key")
under(11)
meet(g.current_state, "SUBWAY KEY")
check(story.inventory.get("SUBWAY_KEY") == 1, "the Subway Key outside the station")
under(11)
meet(g.current_state, "SUBWAY TRAIN")
for _ in range(400):
    st = g.current_state
    if hasattr(st, "run") and getattr(st, "area_key", "") == "THE_UNDER" and st.run.index == 12:
        break
    if getattr(st, "dialogue_box", None) is not None and st.dialogue_box.visible:
        st.dialogue_box.advance()
    st.update(); st.draw()
st = g.current_state
check(getattr(getattr(st, "run", None), "index", None) == 12, f"the train ride to the far station ({getattr(getattr(st, 'run', None), 'index', None)})")
scenes_done()
check(F.get("orre_subway_bomb"), "the far station: the peons' trap blows the door open")
p = under(12)
check(bar_met("THE_UNDER", 12, None), "...and the way through is open")
for it, inv in (("MAINGATE KEY", "MAINGATE_KEY"), ("U-DISK", "U_DISK")):
    under(12)
    meet(g.current_state, it)
    check(story.inventory.get(inv) == 1, f"{it} found")
under(0)
before = story.inventory.get("TIME_FLUTE", 0)
meet(g.current_state, "FLOATING PLATFORM")
check(F.get("orre_windmill_flute") and story.inventory.get("TIME_FLUTE", 0) == before + 1, "the U-Disk lifts the platform into Pyrite's windmill: another Time Flute")

print("5) The Shadow Pokemon Lab")
story.badges["ORRE"].append("UNDER")
p = route("SHADOW_PKMN_LAB", "THE_UNDER")
check(bar_met("SHADOW_PKMN_LAB", 0, None), "the Maingate Key opens the main gate")
F_pre = dict(F)
p = route("SHADOW_PKMN_LAB", "THE_UNDER", floor=1)
check(not p._until_met(TM["SHADOW_PKMN_LAB"]["floors"][1]["barred"][1]["until"]), "the left door's shutter is down")
meet(g.current_state, "SHUTTER SWITCH")
check(F.get("orre_lab_shutter"), "the Shutter Switch raises it")
for who in lp:
    route("SHADOW_PKMN_LAB", "THE_UNDER")
    meet(g.current_state, who)
check(all(F.get(f"snagged_shadow_{n}") for n in ("aipom", "murkrow", "forretress", "granbull", "vibrava", "ariados")),
      "the lab's six Shadows snagged (Aipom, Murkrow, Forretress, Granbull, Vibrava, Ariados)")
for it in ("CARD KEY", "DOWN ST. KEY", "DNA SAMPLE (1)", "DNA SAMPLE (2)", "DNA SAMPLE (3)", "REVIVES", "FULL HEALS", "PP UPS", "ELIXIRS", "FULL RESTORE"):
    route("SHADOW_PKMN_LAB", "THE_UNDER")
    meet(g.current_state, it)
check(story.inventory.get("LAB_CARD_KEY") == 1 and story.inventory.get("DOWN_ST_KEY") == 1 and story.inventory.get("PP_UP", 0) >= 3
      and all(F.get(f"orre_dna_{i}") for i in (1, 2, 3)), "the keys, the three DNA samples and the items")
p = route("SHADOW_PKMN_LAB", "THE_UNDER", floor=3)
check(p._until_met(TM["SHADOW_PKMN_LAB"]["floors"][3]["barred"][0]["until"]), "the analyzer's door opens for the three samples")
meet(g.current_state, "CIPHER PEON SKRUB")
check(F.get("orre_lab_skrub"), "Skrub's rematch")
F["orre_under_colosseum_won"] = True   # (Ein waits for the Under Colosseum: story rework 11-24)
route("SHADOW_PKMN_LAB", "THE_UNDER", floor=3)
meet(g.current_state, "SHADOW POKEMON LAB: EIN")
check(F.get("orre_ein_lab") and F.get("snagged_shadow_raikou"), "Ein beaten, Shadow Raikou snagged")
route("SHADOW_PKMN_LAB", "THE_UNDER", floor=3)
meet(g.current_state, "DATA ROM")
under(8)
meet(g.current_state, "NETT")
check(F.get("orre_data_rom_given"), "the Data ROM to Nett: it points to Realgam Tower")

print("6) The Journal")
jm = [m["id"] for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"].startswith("orre_m")]
check(jm.index("orre_m7c") < jm.index("orre_m8") < jm.index("orre_m8b") < jm.index("orre_m8c") < jm.index("orre_m8d") < jm.index("orre_m9"),
      "the steps in order: Elevator Key, the Under, Silva, Venus, after Venus, Under Colosseum")

print("7) R1 (11-23): the walked way into the Lab - the Far Station's stairs")
_saved = {k: F.get(k) for k in ("orre_subway_bomb", "cleared_the_under", "orre_venus_station")}
_badges = list(story.badges.get("ORRE", []))
F.update({"orre_subway_bomb": True, "cleared_the_under": True, "orre_venus_station": True})
story.badges["ORRE"] = [b_ for b_ in _badges if b_ != "UNDER"]
_won = F.pop("orre_under_colosseum_won", None)   # (the Lab waits for the Under Colosseum now, not an Under Badge: 11-24)
p = route("THE_UNDER", "PYRITE_BUILDING", floor=12)
check("SHADOW_PKMN_LAB" in p.run.floor.exits.values(), "the Far Station has a way out to the Lab")
_said = []
p.say = lambda lines, *a, **k: _said.extend(lines if isinstance(lines, list) else [lines])
p._try_exit("SHADOW_PKMN_LAB"); frames(3)
check(getattr(g.current_state, "area_key", None) == "THE_UNDER" and any("blocks the way" in s_ for s_ in _said),
      f"the stairs wait for the Under Colosseum ({_said[:1]})")
F["orre_under_colosseum_won"] = True
p = route("THE_UNDER", "PYRITE_BUILDING", floor=12)
p._try_exit("SHADOW_PKMN_LAB")
for _ in range(400):
    st = g.current_state
    if getattr(st, "area_key", None) == "SHADOW_PKMN_LAB" and hasattr(st, "run"):
        break
    st.update(); st.draw()
st = g.current_state
lab_exit = [xy for xy, v in st.run.floor.exits.items() if v == "THE_UNDER"] if hasattr(st, "run") else []
check(getattr(st, "area_key", None) == "SHADOW_PKMN_LAB" and st.run.index == 0 and lab_exit
      and abs(st.run.player[0] - lab_exit[0][0]) + abs(st.run.player[1] - lab_exit[0][1]) <= 1,
      "up the stairs: the Lab's yard, beside the way back")
p = route("THE_UNDER", "SHADOW_PKMN_LAB")
check(p.run.index == 12, "and back down: the Far Station")
F.update(_saved)

print(f"##### {len(fails)} failures")
for f_ in fails:
    print("  ", f_)
