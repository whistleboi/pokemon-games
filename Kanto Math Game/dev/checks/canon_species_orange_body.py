# Every species in one playthrough: Orange's Linking Cord, Tauros, its Gen 2 species and dex (split from canon_species 11-23).
#   bash dev/checks/run.sh canon_species_orange
exec(open("dev/checks/canon_species_lib.py", encoding="utf-8").read())

print("4) Orange: the Linking Cord and Tauros")
tro = next(o for o in _P["TROVITOPOLIS"]["explore_options"] if o.get("text") == "Gift clerk")
r60 = _AD[_P["ORANGE_ROUTE_60"]["wild_pool_percentages"]]
check("LINKING_CORD" in tro["stock"] and r60.get("128") and sum(r60.values()) == 100,
      "Trovitopolis's Dept. Store sells the Linking Cord (Alakazam, Machamp, Golem, Gengar); Tauros grazes on Route 60")


print("8) Orange: the old pokeorange hack's Gen 2 species back; the dex is only what Orange gives (11-19)")
story.enter_region("ORANGE")
_ost = _AD["REGION_START"]["ORANGE"]
_odex = set(_ost["dex_list"]) | set(_ost["dex_extra"])
check(len(_odex) == 192 and 152 not in _odex and 151 not in _odex and {18, 137, 143, 150, 171, 176, 186, 222, 227, 233, 250, 251} <= _odex,
      f"Orange's dex: everything Orange gives, 192 (Jordan 11-23; no Chikorita or Mew; Pidgeot, Porygon, Snorlax, Mewtwo, Lanturn, Togetic, Politoed, Corsola, Skarmory, Porygon2, Ho-Oh, Celebi in) ({len(_odex)})")
_pm = next(o for o in _P["TROVITOPOLIS"]["explore_options"] if o.get("text") == "Porygon man")
for _f in ("got_porygon_trovitopolis", "got_upgrade_trovitopolis", "beat_orange_champion"):
    story.story_flags.pop(_f, None)
story.inventory.pop("UPGRADE", None)
story.player_team = [mk(25)]
_okp = lambda c: bool(story.story_flags.get(c))
_run_story_event(g.current_state, _pm["event"], _okp, lambda ls: None)
_got_pory = story.player_team[-1].id == 137
_run_story_event(g.current_state, _pm["event"], _okp, lambda ls: None)
_early = story.inventory.get("UPGRADE", 0) == 0
story.story_flags["beat_orange_champion"] = True
_run_story_event(g.current_state, _pm["event"], _okp, lambda ls: None)
check(_got_pory and _early and story.inventory.get("UPGRADE") == 1,
      "Trovitopolis's Porygon man: his Porygon first, then the Up-Grade once you're the Orange Champion (11-19)")
story.player_team = [mk(25)]
_wild_new = {"ORANGE_ROUTE_69": "179", "FIRE_ISLAND": "218", "ORANGE_ROUTE_62": "227", "ORANGE_ROUTE_64": "192"}
check(all(_AD[_P[a]["wild_pool_percentages"]].get(s) and sum(_AD[_P[a]["wild_pool_percentages"]].values()) == 100 for a, s in _wild_new.items())
      and _AD[_P["ORANGE_ROUTE_70"]["surf_pool_percentages"]].get("171"),
      "...wild where the hack had them: Mareep (Route 69), Slugma (Fire Island), Skarmory (Route 62), Sunflora (Route 64), Lanturn (Route 70's water)")
seller = next(p for p in _TM["TROVITOPOLIS"]["rooms"]["roof"]["people"] if isinstance(p, dict) and p.get("text") == "Egg seller")
story.player_team = [mk(25)]
story.money = 1000
story.current_area_key, story.last_area_key = "TROVITOPOLIS", "ORANGE_ROUTE_64"
g.walk_town_pos = None
st = _CS(g); g.change_state(st)


def roof_pick(value):
    said = []
    _run_story_event(st, seller["event"], lambda c: True, lambda ls: said.extend(ls))
    for _ in range(60):
        if type(g.current_state).__name__ == "PickListState":
            break
        cur = g.current_state
        if getattr(cur, "dialogue_box", None) is not None and getattr(cur.dialogue_box, "visible", False):
            cur.dialogue_box.advance()
        elif getattr(cur, "npc_active", False):
            cur.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        frames()
    if type(g.current_state).__name__ == "PickListState":
        g.current_state.pick(value)
    g.change_state(st)
    return said


roof_pick(175)
poor = len(story.player_team) == 1 and story.money == 1000
story.money = 5000
roof_pick(175)
roof_pick(239)
check(poor and [p.id for p in story.player_team][1:] == [175, 239] and story.money == 1000,
      "the Trovitopolis rooftop Egg seller: $2,000 an Egg of your choice, as often as you like (not without the money)")
story.player_team = [mk(25)]
_old = next(p for p in _TM["MIKAN_ISLAND"]["rooms"]["house"]["people"] if isinstance(p, dict) and p.get("text") == "Old man")
story.story_flags.pop("orange_got_tyrogue", None)
_run_story_event(st, _old["event"], lambda c: True, lambda ls: None)
check(story.player_team[-1].id == 236 and getattr(story.player_team[-1], "held_item", None) == "BLACK_BELT",
      "Mikan's old man gives you his Tyrogue (holding a Black Belt), as the hack")
_b = {a: [o for o in _P[a]["route_menu"] if o.get("action") == "BOSS" and o.get("boss", {}).get("id") == s]
      for a, s in (("ORANGE_ROUTE_68", 186), ("ORANGE_ROUTE_50", 250), ("ORANGE_ROUTE_73", 251))}
_on_map = lambda a, txt: any(txt in [p if isinstance(p, str) else p.get("text") for p in (f.get("people") or [])] for f in (_TM[a].get("floors") or [_TM[a]]))
check(all(_b.values()) and _b["ORANGE_ROUTE_50"][0].get("flag_condition") == "beat_orange_champion"
      and _b["ORANGE_ROUTE_73"][0].get("flag_condition") == "beat_orange_champion" and not _b["ORANGE_ROUTE_68"][0].get("flag_condition")
      and _on_map("ORANGE_ROUTE_68", "POLITOED") and _on_map("ORANGE_ROUTE_50", "HO-OH") and _on_map("ORANGE_ROUTE_73", "CELEBI"),
      "Politoed waits on Route 68's shore; Ho-Oh (Routes 50-51) and Celebi (by Tarroco) once you're the Orange Champion")
story.player_team = [mk(25)]


print(f"##### {fails} failures")
