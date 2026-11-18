# TMs and entry hazards (Jordan, 11-17): one TM list in every region on Scarlet/Violet's numbers (every TM ever, all
# on sale by the League), one of each in a Bag, an owned TM unlocks its move, older saves converted; Stealth Rock,
# Spikes, Toxic Spikes and Sticky Web in every battle, cleared by Rapid Spin, Defog, Tidy Up, Court Change.
import json, os, random, shutil, subprocess, sys, tempfile
from src.pokemon import tms, moves as movelib
from src.states.battle import TrainerBattleState, WildBattleState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.data.save = lambda *a, **k: None
random.seed(7)


def lv(pid, level, moves=None):
    p = mk(pid)
    p.level = level
    p.heal_full() if hasattr(p, "heal_full") else None
    p.current_hp = p.get_max_hp()
    if moves:
        p.moves = list(moves)
    return p


print("1) one TM list for every region")
T = json.load(open("assets/tms.json", encoding="utf-8"))
legacy = json.load(open("assets/tm_legacy.json", encoding="utf-8"))
check(list(sorted(T)) == [f"TM{i:03d}" for i in range(1, len(T) + 1)] and len(T) >= 229,
      f"TM001-TM{len(T):03d}, nothing else ({len(T)} TMs)")
check(T["TM116"]["move"] == "STEALTH-ROCK" and T["TM001"]["move"] == "TAKE-DOWN" and T["TM229"]["move"] == "UPPER-HAND",
      "Scarlet/Violet's numbers: TM001 Take Down, TM116 Stealth Rock, TM229 Upper Hand (its DLC's last)")
check(all(T[f"TM{i:03d}"]["from"].startswith("Scarlet/Violet") for i in range(1, 230))
      and not any(T[k]["from"].startswith("Scarlet/Violet") for k in T if int(k[2:]) > 229),
      "TM230 on: the older games' TMs Scarlet/Violet never had")
_za = [k for k in sorted(T) if T[k]["from"].startswith("Legends: Z-A")]
_zan = [int(T[k]["from"].split("TM")[-1]) for k in _za]
check(_za and _za == sorted(T)[-len(_za):] and _zan == sorted(_zan) and T["TM230"]["from"].startswith("Brilliant Diamond"),
      f"Legends: Z-A's own TMs last, in Z-A's order: {_za[0]}-{_za[-1]} ({len(_za)}); TM230 = {T['TM230']['from']}")
check(T[_za[0]]["move"] == "NIGHT-SLASH" and T[_za[-1]]["move"] == "SHEER-COLD", "...Night Slash (Z-A TM34) to Sheer Cold (TM155)")
check(set(legacy.values()) <= {d["move"] for d in T.values()}, "every old TM's move is in the list (Sword/Shield's, the story's, Hoenn's)")
check(not os.path.exists("assets/tms_hoenn.json") and not hasattr(tms, "is_hoenn"), "no region list of its own (Hoenn's is gone)")
check(tms.is_tm("TM116") and not tms.is_tm("HTM24") and not tms.is_tm("TM24") and tms.label(g, "TM116") == "TM116 Stealth Rock",
      f"keys TM001...: {tms.label(g, 'TM116')}")
check(all(0 <= d["tier"] <= 8 and not d.get("gift") and not d.get("shop_only") for d in T.values()),
      "every TM on a tier the Marts sell by (none held back)")
_l = json.load(open("assets/tm_learners.json", encoding="utf-8"))
_none = sorted(d["move"] for d in T.values() if not _l.get(d["move"]))
check(len(_l.get("STEALTH-ROCK", [])) > 100 and 74 in _l["STEALTH-ROCK"], f"Stealth Rock has learners ({len(_l['STEALTH-ROCK'])}, Geodude among them)")
check(not _none, f"every TM has learners, Z-A's too (Serebii's lists): {_none}")
check(52 in _l["FAKE-OUT"] and 39 in _l["SING"],
      "...Meowth learns Fake Out, Jigglypuff Sing, by TM")
_gifts = []
for f in ("pokemon_area_data", "johto_area_data", "sevii_area_data", "hoenn_area_data"):
    raw = open(f"assets/{f}.json", encoding="utf-8").read()
    _gifts += [k for k in __import__("re").findall(r'"(H?TM\d+)"', raw)]
check(_gifts and all(k in T for k in _gifts), f"every TM the regions' places name is in the list ({len(_gifts)})")
check(T["TM179"]["move"] == "SMACK-DOWN" and "TM179" in open("src/world/story_events.py", encoding="utf-8").read(),
      "Professor Cozmo's thanks: Smack Down, as TM179")

print("2) the builder makes these files again")
tmp = tempfile.mkdtemp(dir=S)
for rel in ("assets/moves.json", "assets/tm_learners.json", "assets/tm_legacy.json", "assets/sprites/items/hm-cut.png"):
    os.makedirs(os.path.join(tmp, os.path.dirname(rel)), exist_ok=True)
    shutil.copyfile(rel, os.path.join(tmp, rel))
out = subprocess.run([sys.executable, os.path.abspath("dev/builders/build_tms.py"),
                      os.path.abspath("dev/builders/out/pokeapi_csv"), os.path.join(tmp, "no_icons")],
                     cwd=tmp, capture_output=True, text=True)
check(out.returncode == 0, f"build_tms.py runs ({out.stdout.splitlines()[0] if out.stdout else out.stderr[-300:]})")
check(json.load(open(os.path.join(tmp, "assets/tms.json"), encoding="utf-8")) == T, "...tms.json rebuilt = the installed one")
check(json.load(open(os.path.join(tmp, "assets/tm_learners.json"), encoding="utf-8")) == _l, "...tm_learners.json too")

print("3) one of each in a Bag; an owned TM unlocks its move")
story.current_area_key = "PALLET_TOWN"
story.inventory.pop("TM116", None)
geo = lv(74, 20, ["TACKLE"])
story.player_team = [geo]
check("STEALTH-ROCK" not in movelib.move_pool(g, geo), "no TM: Geodude can't pick Stealth Rock")
check(story.add_item("TM116") == 1 and story.add_item("TM116") == 0 and story.inventory["TM116"] == 1, "a second TM116: nothing extra")
story.inventory["TM116"] = story.inventory.get("TM116", 0) + 3
check(story.inventory["TM116"] == 1, "...however it's added (gift_item, rewards): still one")
pc_mon = lv(75, 30, ["TACKLE"])
check("STEALTH-ROCK" in movelib.move_pool(g, geo) and "STEALTH-ROCK" in movelib.move_pool(g, pc_mon),
      "owned: in the move pool of every Pokemon that can learn it, party or PC, without teaching")
check(tms.works_on(g, geo, "TM116") and tms.teach(g, geo, "TM116")[0].endswith("learned Stealth Rock!")
      and "STEALTH-ROCK" in geo.moves and story.inventory["TM116"] == 1, "taught from the Bag: learned, and the TM stays (reusable)")
check(tms.mart_stock(g, 8) and "TM116" not in tms.mart_stock(g, 8)
      and len(tms.mart_stock(g, 8)) == len(T) - len(tms.owned(story)), "by the League the Mart has every TM you don't own")

print("4) an old save's TMs become the new numbers")
data = story.serialize()
data["story_flags"] = dict(data["story_flags"])
data["story_flags"].pop(story.TM_NUMBERS_FLAG, None)
data["story_flags"]["coop_ledgers"] = {"1": {"money": 0, "balls": 5, "items": {"TM24": 2, "POTION": 1}}}
for k, st in data["region_stores"].items():
    st["bag"] = {"POTION": 3, "TM05": 1, "TM100": 1, "HTM24": 2, "TM24": 1}
from src.world.story import StoryManager
old = StoryManager()
old.game = g
old.deserialize(json.loads(json.dumps(data)), g.loader)
_bags = [st["bag"] for st in old.region_stores.values()]
_want = {tms.key_for_move(g, m) for m in ("THUNDER-PUNCH", "SMACK-DOWN", "THUNDERBOLT", "SNORE")}
check(all({k for k in b if tms.is_tm(k)} == _want and b["POTION"] == 3 for b in _bags) and not any(
      k in b for b in _bags for k in ("TM05", "TM100", "HTM24", "TM24")),
      f"by move: TM05 Thunder Punch, TM100 Smack Down, Hoenn's TM24 Thunderbolt, TM24 Snore -> {sorted(_want)}")
check(all(b[k] == 1 for b in _bags for k in _want), "...one of each")
check(old.story_flags["coop_ledgers"]["1"]["items"] == {tms.key_for_move(g, "SNORE"): 1, "POTION": 1}, "...a friend's co-op ledger too")
old.deserialize(json.loads(json.dumps(old.serialize())), g.loader)
check({k for k in old.inventory if tms.is_tm(k)} == _want, "...once only (a reload doesn't convert TM100 again)")

print("4b) a save on the first list (Z-A's TMs first) moves to today's, by move, once")
data = story.serialize()
data["story_flags"] = dict(data["story_flags"])
data["story_flags"][story.TM_NUMBERS_FLAG] = True
data["story_flags"].pop(story.TM_NUMBERS_V2_FLAG, None)
data["story_flags"]["coop_ledgers"] = {"1": {"money": 0, "balls": 5, "items": {"TM230": 1}}}
for k, st in data["region_stores"].items():   # (first list: TM230 Headbutt, TM234 Night Slash, TM337 Nightmare)
    st["bag"] = {"POTION": 2, "TM116": 1, "TM230": 1, "TM234": 1, "TM337": 1}
v1 = StoryManager()
v1.game = g
v1.deserialize(json.loads(json.dumps(data)), g.loader)
_want = {"TM116"} | {tms.key_for_move(g, m) for m in ("HEADBUTT", "NIGHT-SLASH", "NIGHTMARE")}
_bags = [st["bag"] for st in v1.region_stores.values()]
check(all({k for k in b if tms.is_tm(k)} == _want and b["POTION"] == 2 for b in _bags) and tms.key_for_move(g, "NIGHT-SLASH") == "TM330",
      f"TM230 Headbutt, TM234 Night Slash, TM337 Nightmare -> {sorted(_want)} (TM001-TM229 stay)")
check(v1.story_flags["coop_ledgers"]["1"]["items"] == {tms.key_for_move(g, "HEADBUTT"): 1}, "...a friend's co-op ledger too")
v1.deserialize(json.loads(json.dumps(v1.serialize())), g.loader)
check({k for k in v1.inventory if tms.is_tm(k)} == _want and v1.story_flags.get(story.TM_NUMBERS_V2_FLAG), "...once only")
check(all(tms.legacy_key(g, "v1:" + k) for k in ("TM230", "TM269", "TM348")) and tms.legacy_key(g, "TM24") == tms.key_for_move(g, "SNORE"),
      "tm_legacy.json: both old schemes")

print("5) merged Bags (two Champion titles) show one of each TM")
starts = g.loader.area_data.get("REGION_START", {})
m = StoryManager()
m.game = g
m.region_stores = {"KANTO": {"team": [], "pc": [None] * 300, "bag": {"TM116": 1, "POTION": 2}},
                   "JOHTO": {"team": [], "pc": [None] * 300, "bag": {"TM116": 1, "POTION": 3}}}
m.linked_regions = set()
m.is_region_champion = lambda r: r in ("KANTO", "JOHTO")
m.current_area_key = "PALLET_TOWN"
m.link_champion_regions()
check(m.region_stores[m.LINKED]["bag"]["TM116"] == 1 and m.region_stores[m.LINKED]["bag"]["POTION"] == 5,
      "linked: TM116 x1 (Potions add up)")

print("6) entry hazards in a trainer battle")


def trainer(team, mine, cls="YOUNGSTER"):
    story.current_area_key = "KANTO_ROUTE_3"
    story.player_team = mine
    b = TrainerBattleState(g, team, trainer_class=cls, trainer_name="T", area_name="KANTO_ROUTE_3")
    g.change_state(b)
    return b


def use(b, name, foe=False):
    me, them = (b.opponent_pokemon, b.player_pokemon) if foe else (b.player_pokemon, b.opponent_pokemon)
    return b._use_move(me, them, name, "ME", "FOE", b.player_max_hp if foe else b.opp_max_hp,
                       b.player_hp if foe else b.opponent_hp)


def send_next(b, mon):
    """The trainer's next Pokemon comes out (as the battle does it)."""
    b.opponent_team.append(mon)
    b.current_opponent_idx = len(b.opponent_team) - 1
    b.opponent_pokemon = mon
    b._form_msgs = []
    b.setup_battle_matchup()
    return list(b._form_msgs)


geo = lv(74, 40, ["STEALTH-ROCK", "TACKLE"])
b = trainer([lv(19, 30)], [geo])
b._answer_mode = None
_, lines, _ = use(b, "STEALTH-ROCK")
check(b.side(b.opponent_pokemon).get("stealth_rock") == 1 and any("Pointed stones float" in l and "foe's team" in l for l in lines),
      f"the TM's Stealth Rock, used: {lines[-1]}")
check(use(b, "STEALTH-ROCK")[1][-1] == "But it failed!", "...only once")
for i in range(3):
    use(b, "SPIKES")
check(b.side(b.opponent_pokemon)["spikes"] == 3 and use(b, "SPIKES")[1][-1] == "But it failed!", "Spikes: 3 layers, no more")
use(b, "TOXIC-SPIKES"); use(b, "TOXIC-SPIKES")
check(b.side(b.opponent_pokemon)["toxic_spikes"] == 2 and use(b, "TOXIC-SPIKES")[1][-1] == "But it failed!", "Toxic Spikes: 2 layers")
use(b, "STICKY-WEB")
check(b.side(b.opponent_pokemon)["sticky_web"] == 1 and use(b, "STICKY-WEB")[1][-1] == "But it failed!", "Sticky Web: once")
check(not b.side(b.player_pokemon), "...all on the foe's side, none on yours")

zard = lv(6, 30)   # Fire/Flying: Rock x4, above the spikes
lines = send_next(b, zard)
check(b.opponent_hp == b.opp_max_hp - b.opp_max_hp // 2 and any("Pointed stones dug" in l for l in lines)
      and not any("spikes" in l.lower() or "web" in l for l in lines),
      f"Charizard: Stealth Rock takes half (Rock x4), flying over spikes and web ({b.opponent_hp}/{b.opp_max_hp})")
rat = lv(19, 30)
lines = send_next(b, rat)
mx = b.opp_max_hp
check(b.opponent_hp == mx - mx // 8 - mx // 4 and rat.status == "toxic" and b.stages(rat)["SPEED"] == -1,
      f"Rattata: 1/8 rocks + 1/4 (3 spikes), badly poisoned, Speed -1 ({lines})")
gas = lv(109, 30)  # Koffing: Levitate
gas.ability_slot = 0
b.vol(gas)["ability"] = "LEVITATE"
lines = send_next(b, gas)
check(b.opp_max_hp - b.opponent_hp == b.opp_max_hp // 8 and not gas.status and b.side(gas).get("toxic_spikes"),
      f"Levitate: only the rocks ({lines})")
grimer = lv(88, 30)  # grounded Poison type
lines = send_next(b, grimer)
check(not b.side(grimer).get("toxic_spikes") and any("poison spikes disappeared" in l for l in lines) and not grimer.status,
      "a grounded Poison type soaks up the Toxic Spikes")
clef = lv(35, 30)
b.vol(clef)["ability"] = "MAGICGUARD"
lines = send_next(b, clef)
check(b.opponent_hp == b.opp_max_hp and b.stages(clef)["SPEED"] == -1, f"Magic Guard: no damage (the web still slows) ({lines})")
check(not hasattr(b, "held_heavy_duty_boots"), "(Heavy-Duty Boots / Air Balloon: not items in this game)")

print("7) clearing")
b.player_pokemon.moves = ["RAPID-SPIN"]
b.side(b.player_pokemon)["stealth_rock"] = 1
b.side(b.player_pokemon)["spikes"] = 2
random.seed(1)
dmg, lines, _ = use(b, "RAPID-SPIN")
check(dmg and not b.side(b.player_pokemon).get("stealth_rock") and not b.side(b.player_pokemon).get("spikes")
      and b.side(b.opponent_pokemon).get("stealth_rock"), f"Rapid Spin clears your side only: {lines[-2:]}")
b.side(b.player_pokemon)["sticky_web"] = 1
_, lines, _ = use(b, "DEFOG")
check(not any(b.side(b.player_pokemon).get(k) for k in ("sticky_web",)) and not b.side(b.opponent_pokemon).get("stealth_rock")
      and not b.side(b.opponent_pokemon).get("spikes"), f"Defog clears both sides: {lines[1:]}")
b.side(b.player_pokemon)["spikes"] = 1
b.side(b.opponent_pokemon)["reflect"] = 3
use(b, "COURT-CHANGE")
check(b.side(b.opponent_pokemon).get("spikes") == 1 and b.side(b.player_pokemon).get("reflect") == 3
      and not b.side(b.player_pokemon).get("spikes"), "Court Change swaps the two sides")
b.side(b.player_pokemon)["stealth_rock"] = 1
use(b, "TIDY-UP")
check(not b.side(b.player_pokemon) .get("stealth_rock") and not b.side(b.opponent_pokemon).get("spikes"), "Tidy Up clears both")

print("8) a whole trainer battle: rocks hurt the next Pokemon, and a hazard knock-out faints")
random.seed(3)
geo = lv(74, 50, ["STEALTH-ROCK", "ROCK-THROW"])
spare = lv(19, 50, ["TACKLE"])
b = trainer([lv(19, 10), lv(16, 10)], [geo, spare])
log = []
for _ in range(2000):
    if b.dialogue_box.visible:
        for line in b.dialogue_box.text_lines:
            if not log or log[-1] != line:
                log.append(line)
        b.dialogue_box.is_finished = True
        if b.phase == "MESSAGE" and b.dialogue_box.callback:
            cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
    if b.phase == "SWITCH_PROMPT":
        b.on_switch_no()
    if b.phase == "MENU" and not b.dialogue_box.visible and not b.turn_actions:
        if b.opponent_pokemon is b.opponent_team[1] and not b._form_msgs:
            break
        b.open_move_menu()
        b.choose_move("STEALTH-ROCK" if not b.side(b.opponent_pokemon).get("stealth_rock") else "ROCK-THROW")
        b.math_ui.on_click(b.options.index(b.correct_ans))
    b.feedback_timer = 0
    b.update()
check(any("Pointed stones float" in l for l in log) and any("Pointed stones dug into Foe PIDGEY" in l for l in log),
      f"Stealth Rock, then the foe's Pidgey hurt coming out ({[l for l in log if 'stones' in l]})")
check(b.opponent_hp < b.opp_max_hp, f"...its HP: {b.opponent_hp}/{b.opp_max_hp}")
# your own side: a hurt Pokemon switched in onto the foe's Spikes faints from them
geo = lv(74, 50, ["TACKLE"])
spare = lv(19, 50, ["TACKLE"])
b = trainer([lv(19, 10)], [geo, spare])
b.side(b.player_pokemon)["spikes"] = 3
spare.current_hp = 1
b.perform_switch(1)
log = []
for _ in range(800):
    if g.current_state is not b:
        break   # (the party list: send out another)
    if b.dialogue_box.visible:
        for line in b.dialogue_box.text_lines:
            if not log or log[-1] != line:
                log.append(line)
        b.dialogue_box.is_finished = True
        if b.phase == "MESSAGE" and b.dialogue_box.callback:
            cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
    b.feedback_timer = 0
    b.update()
check(spare.current_hp == 0 and any("hurt by the spikes" in l for l in log) and any("RATTATA FAINTED" in l.upper() for l in log),
      f"switched in at 1 HP: hurt by the spikes, then it faints ({[l for l in log if 'spikes' in l or 'fainted' in l]})")
check(g.current_state is not b and type(g.current_state).__name__ == "PokemonPartyMenuState",
      "...and you pick the next one (the battle doesn't go on with a fainted Pokemon)")

print("9) the foe's AI lays hazards when it has reason to")
b = trainer([lv(74, 30, ["STEALTH-ROCK", "TACKLE"])], [lv(19, 30), lv(16, 30)])
check(b._status_score("STEALTH-ROCK", movelib.info(g, "STEALTH-ROCK"), b.opponent_pokemon, b.player_pokemon) > 0,
      "you have Pokemon to send out: worth it")
b.side(b.player_pokemon)["stealth_rock"] = 1
check(b._status_score("STEALTH-ROCK", movelib.info(g, "STEALTH-ROCK"), b.opponent_pokemon, b.player_pokemon) == 0, "already down: no")

print("10) a wild battle with hazards")
story.current_area_key = "KANTO_ROUTE_1"
story.player_team = [lv(74, 20, ["TACKLE"]), lv(16, 20, ["TACKLE"])]
w = WildBattleState(g, lv(19, 5, ["SPIKES"]), "KANTO_ROUTE_1")
g.change_state(w)
_, lines, _ = w._use_move(w.opponent_pokemon, w.player_pokemon, "SPIKES", "FOE", "ME", w.player_max_hp, w.player_hp)
check(w.side(w.player_pokemon).get("spikes") == 1 and "your team" in lines[-1], f"a wild Pokemon's Spikes, on your side: {lines[-1]}")
w._form_msgs = []
w.player_pokemon = story.player_team[1]
w.setup_battle_matchup(reset_opponent_hp=False)
check(w.player_hp == w.player_max_hp and not any("spikes" in l for l in w._form_msgs), "your Pidgey flies over them")
w.player_pokemon = story.player_team[0]
w.setup_battle_matchup(reset_opponent_hp=False)
check(w.player_hp < w.player_max_hp and any("spikes" in l for l in w._form_msgs), f"your Geodude doesn't ({w.player_hp}/{w.player_max_hp})")
for _ in range(300):
    if w.dialogue_box.visible:
        w.dialogue_box.is_finished = True
        if w.phase == "MESSAGE" and w.dialogue_box.callback:
            cb = w.dialogue_box.callback; w.dialogue_box.callback = None; cb()
    w.feedback_timer = 0
    w.update()
check(True, "...and the battle runs on (no crash)")

print("11) an OVERWORLD-style trainer battle with hazards")
from src.states.overworld import PlayState
from src.states.battle import TrainerIntroState
g.dungeon_routes = True
story.battle_style = "OVERWORLD"
story.current_area_key, story.last_area_key = "KANTO_ROUTE_3", "PEWTER_CITY"
_ace = lv(6, 100, ["FLAMETHROWER"])
story.player_team = [_ace]
p = PlayState(g)
g.states["play"] = p
g.change_state(p)
_t = next((m for f in p.run.floors for m in f.movers if m.kind == "trainer"), None)
p._battle_trainer(_t)
while p.dialogue_box.visible:
    p.dialogue_box.advance()
    p.update()
ob = g.current_state
check(isinstance(ob, TrainerBattleState) and getattr(ob, "overworld", None) is not None, "the battle is drawn on the map")
ob.side(ob.opponent_pokemon).update({"stealth_rock": 1, "spikes": 2, "sticky_web": 1})
asked = 0
for _ in range(6000):
    if g.current_state is not ob:
        break
    if ob.phase == "SWITCH_PROMPT" and ob.btn_no.visible:
        ob.btn_no.callback()
    elif ob.phase == "MENU" and not ob.dialogue_box.visible:
        ob.open_move_menu()
        ob.choose_move(ob.move_buttons[0].text.replace(" ", "-"))
        ob.math_ui.on_click(ob.options.index(ob.correct_ans))
        asked += 1
    elif ob.dialogue_box.visible:
        ob.dialogue_box.is_finished = True
        if ob.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
            ob.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif ob.dialogue_box.callback:
            cb = ob.dialogue_box.callback; ob.dialogue_box.callback = None; cb()
        else:
            ob.dialogue_box.advance()
    ob.feedback_timer = 0
    if g.current_state is ob:
        ob.update()
        ob.draw()
check(g.current_state is not ob and asked >= 1, f"won on the map with the foe's side full of hazards ({asked} questions)")
g.dungeon_routes = False
story.battle_style = "TRADITIONAL"

print(f"##### {fails} failures")
