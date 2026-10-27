
import random as _r
from src.pokemon import affection
from src.states.overworld import CityState, PlayState
from src.states.battle import TrainerBattleState, WildBattleState
from src.states.amie import AmieState
from src.states.camp import CampState, curry_class
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


prog = g.loader.area_data["STORY_PROGRESSION"]


def town(area):
    story.current_area_key = area
    s = CityState(g); g.states["city"] = s; g.current_state = s
    return s


def route(area):
    story.current_area_key = area
    s = PlayState(g); g.states["play"] = s; g.current_state = s
    return s


def answer_all(st, right=True):
    """Answer the minigame's questions instantly until it's done."""
    for _ in range(40):
        if st.phase in ("PLAY", "STIR"):
            idx = st.options.index(st.answer) if right else next(i for i, o in enumerate(st.options) if o != st.answer)
            st.on_answer(idx)
        elif st.dialogue_box.visible and st.dialogue_box.callback:
            cb, st.dialogue_box.callback = st.dialogue_box.callback, None
            st.dialogue_box.set_visibility(False)
            cb()
        else:
            break


print("1) Pokemon-Amie")
k = [a for a, d in prog.items() if d.get("region") == "KALOS" and any(o.get("action") == "AMIE" for o in d.get("explore_options", []))]
check(len(k) >= 10, f"Amie button in {len(k)} Kalos towns")
t = town(k[0])
opt = next(o for o in prog[k[0]]["explore_options"] if o["action"] == "AMIE")
cb = t._get_callback_for_option(opt)
check(cb is not None, "AMIE option has a handler")
mon = mk(25); story.player_team = [mon]
cb()
am = g.current_state
check(isinstance(am, AmieState), f"opens {type(am).__name__}")
am.start(); answer_all(am)
am.pick(mon); am.pet()
check(affection.get(mon) == 4, f"petting: affection {affection.get(mon)}")
answer_all(am)
am.play(); answer_all(am)
check(affection.get(mon) == 4 + 36, f"three quick right answers: affection {affection.get(mon)}")
for _ in range(30):
    am.pet(); answer_all(am)
check(affection.gain_today(mon) == affection.DAILY_CAP and affection.get(mon) == affection.DAILY_CAP,
      f"daily cap {affection.DAILY_CAP}: {affection.get(mon)}")
mon.affection = 255
check(affection.hearts(mon) == 5 and affection.xp_mult(mon) == 1.2, "5 hearts, 1.2x XP")
rec = story._pokemon_record(mon)
check(rec.get("affection") == 255, "affection is saved")

# Battle perks with max affection.
_r.seed(3)
endured = evaded = 0
for _ in range(400):
    me = mk(25); me.affection = 255; me.level = 5; me.current_hp = me.get_max_hp()
    story.player_team = [me]
    foe = mk(76); foe.level = 60
    b = WildBattleState(g, foe, "KALOS_ROUTE_1"); g.change_state(b)
    b._foe_next_move = "EARTHQUAKE"
    b.opponent_attack()
    lines = b.dialogue_box.text_lines
    endured += any("toughed it out" in l for l in lines)
    evaded += any("avoided the attack" in l for l in lines)
check(40 <= endured <= 110 and 40 <= evaded <= 120, f"5 hearts: endured {endured}/400, dodged {evaded}/400")
me = mk(25); story.player_team = [me]
b = WildBattleState(g, mk(76), "KALOS_ROUTE_1"); g.change_state(b)
b._foe_next_move = "EARTHQUAKE"; b.player_hp = 1
b.opponent_attack()
check(not any("toughed" in l or "avoided" in l for l in b.dialogue_box.text_lines), "no perks at 0 hearts")

print("2) Galar camping")
gr = [a for a, d in prog.items() if d.get("region") == "GALAR" and any(m.get("action") == "CAMP" for m in d.get("route_menu", []))]
check(len(gr) >= 10, f"camp on {len(gr)} Galar areas")
p = route(gr[0])
item = next(m for m in prog[gr[0]]["route_menu"] if m["action"] == "CAMP")
team = [mk(810), mk(813)]
for x in team:
    x.level = 10; x.current_hp = 1; x.status = "burn"
story.player_team = team
p._get_route_callback(item)()
camp = g.current_state
check(isinstance(camp, CampState), f"opens {type(camp).__name__}")
camp.start(); answer_all(camp)
camp.rest(); answer_all(camp)
check(all(x.current_hp == x.get_max_hp() and not x.status for x in team), "rest heals and cures")
for x in team:
    x.current_hp = 1
camp.rest(); answer_all(camp)
check(all(x.current_hp == 1 for x in team), "rest once per day per spot")
story.inventory["ORAN_BERRY"] = 3; story.inventory["PECHA_BERRY"] = 1
camp.show_berries(); camp.toggle("ORAN_BERRY"); camp.toggle("PECHA_BERRY")
lv0 = [x.level for x in team]
camp.begin(); answer_all(camp)
check(all(x.current_hp == x.get_max_hp() for x in team), "curry heals")
check(all(x.level > l for x, l in zip(team, lv0)), f"perfect curry gives a level: {lv0} -> {[x.level for x in team]}")
check(story.inventory.get("ORAN_BERRY") == 2 and "PECHA_BERRY" not in story.inventory, "berries used")
check(curry_class(0)[0] == "Koffing" and curry_class(8)[0] == "Charizard", "curry classes")
camp.leave()
check(g.current_state is p and p.is_resuming is False or g.current_state is p, "pack up returns to the route")

print("3) Paldea paths")
titans = [(a, m) for a, d in prog.items() for m in d.get("route_menu", []) if d.get("region") == "PALDEA" and m.get("action") == "BOSS" and (m.get("boss") or {}).get("no_catch") and m["boss"].get("id") != 10501]
check(len(titans) == 5, f"5 Titans: {[m['boss']['name'] for a, m in titans]}")
stars = [(a, m) for a, d in prog.items() for m in d.get("route_menu", []) if m.get("action") == "EVENT" and "battle" in (m.get("event") or {}) and d.get("region") == "PALDEA" and not a.startswith("KITAKAMI")
         and m["event"]["battle"].get("team", [None])[-1] == 966]  # the crews end with Revavroom (other Paldea battle buttons aren't Team Star)
check(len(stars) == 5, f"5 Team Star bases: {[m['event']['battle']['name'] for a, m in stars]}")
story.player_team = [mk(906)]
# Hidden until Arven / Team Star are met.
story.story_flags.pop("met_arven", None); story.story_flags.pop("met_team_star", None)
a, m = titans[0]
p = route(a); p.show_progression_menu()
check(m["text"] not in [b.text for b in p.route_buttons], f"{m['text']} hidden before meeting Arven")
story.story_flags["met_arven"] = True; story.story_flags["met_team_star"] = True
for a, m in titans:
    p = route(a); p.show_progression_menu()
    btn = next((b for b in p.route_buttons if b.text == m["text"]), None)
    check(btn is not None, f"{a}: {m['text']} shown")
    btn.callback()
    for _ in range(3):
        if p.dialogue_box.visible and p.dialogue_box.callback:
            cb2, p.dialogue_box.callback = p.dialogue_box.callback, None
            cb2()
    b = g.current_state
    check(isinstance(b, WildBattleState) and b.no_catch and b.opponent_pokemon.level == m["boss"]["level"],
          f"  battle vs {b.opponent_pokemon.name} Lv {b.opponent_pokemon.level}")
    b.trigger_outro(True)
    check(story.story_flags.get(m["boss"]["victory_flag"]) and b.phase == "OUTRO", "  win sets the flag, no catch prompt")
check(story.inventory.get("HERBA_MYSTICA") == 5, f"Herba Mystica x{story.inventory.get('HERBA_MYSTICA')}")
p = route(titans[0][0]); p.show_progression_menu()
check(titans[0][1]["text"] not in [b.text for b in p.route_buttons], "Titan button gone after the win")
for a, m in stars:
    p = route(a)
    p._get_route_callback(m)()
    nxt = getattr(g.current_state, "next_state", None)
    ok = isinstance(nxt, TrainerBattleState)
    check(ok and nxt.opponent_team[-1].name == "REVAVROOM" and nxt.opponent_team[-1].level == m["event"]["battle"]["level"],
          f"{a}: {m['event']['battle']['name']} {[x.name for x in nxt.opponent_team] if ok else ''} lv {nxt.opponent_team[-1].level if ok else ''}")
    if ok:
        nxt.player_won = True; nxt.exit_battle()
        check(story.story_flags.get(m["event"]["flag"]), f"  sets {m['event']['flag']}")
for area, label, flag in (("MESAGOZA", "Arven's Battle", "path_of_legends_complete"),
                          ("NARANJA_ACADEMY", "Confront Cassiopeia", "starfall_street_complete")):
    t = town(area)
    opt = next(o for o in prog[area]["explore_options"] if o["text"] == label)
    check(t._check_menu_condition(opt["condition"]), f"{label} unlocked")
    t._get_callback_for_option(opt)()
    nxt = getattr(g.current_state, "next_state", None)
    check(isinstance(nxt, TrainerBattleState), f"  battle vs {getattr(nxt, 'trainer_name', None)} {[x.name for x in nxt.opponent_team] if nxt else ''}")
    nxt.player_won = True; nxt.exit_battle()
    check(story.story_flags.get(flag), f"  sets {flag}")
zero = next(o for o in prog["NARANJA_ACADEMY"]["travel_options"] if o["target_area"] == "AREA_ZERO")
t = town("NARANJA_ACADEMY")
story.story_flags.pop("beat_paldea_champion", None)
check(not t._check_menu_condition(zero["condition"]), "Area Zero locked without the Champion")
story.story_flags["beat_paldea_champion"] = True
check(t._check_menu_condition(zero["condition"]), "Area Zero opens after all three paths")
check(g.assets.get_trainer_image("giacomo.png") is not None and g.assets.get_trainer_image("arven.png") is not None,
      "Team Star / Arven sprites load")
print(f"##### {fails} failures")
