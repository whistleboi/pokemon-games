# Every species in one playthrough: Orre's stones and Plusle (split from canon_species 11-23).
#   bash dev/checks/run.sh canon_species_orre
exec(open("dev/checks/canon_species_lib.py", encoding="utf-8").read())

print("3) Orre: XD's stones and Colosseum's Plusle")
story.enter_region("ORRE")
story.current_area_key, story.last_area_key = "GATEON_PORT", None   # (in Gateon Port, where the Eevee expert lives)
g.walk_town_pos = g.walk_town_room = None
_said = []
_show = lambda ls: _said.extend(ls)
gp = next(p for p in _TM["GATEON_PORT"]["rooms"]["house_west"]["people"] if isinstance(p, dict) and p.get("text") == "Eevee expert")
st = _CS(g); g.change_state(st)
for f in [k for k in story.story_flags if k.startswith("xd_eevee_stone")]:
    story.story_flags.pop(f)
_before = {k: story.inventory.get(k, 0) for k in ("WATER_STONE", "THUNDER_STONE", "FIRE_STONE")}
_run_story_event(st, gp["event"], lambda c: True, _show)
for _ in range(60):
    if type(g.current_state).__name__ == "PickListState":
        break
    cur = g.current_state
    if getattr(cur, "dialogue_box", None) is not None and getattr(cur.dialogue_box, "visible", False):
        cur.dialogue_box.advance()
    elif getattr(cur, "npc_active", False):
        cur.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
    frames()
pl = g.current_state
picked = type(pl).__name__ == "PickListState"
if picked:
    pl.pick("WATER_STONE")
again = []
_run_story_event(st, gp["event"], lambda c: True, lambda ls: again.extend(ls))
check(picked and story.inventory.get("WATER_STONE", 0) == _before["WATER_STONE"] + 1 and any("tomorrow" in x for x in again)
      and type(g.current_state).__name__ != "PickListState",
      f"Gateon Port's Eevee expert: pick a stone (Water/Thunder/Fire), then another tomorrow ({again[:1]})")
lab = [o for o in _P["XD_CIPHER_LAB"]["route_menu"] if o.get("text") == "LEAF STONE"]
lib = [o for o in _P["SS_LIBRA"]["route_menu"] if o.get("text") == "FIRE STONE"]
check(lab and lab[0]["event"]["gift_item"] == {"LEAF_STONE": 1} and _TM["XD_CIPHER_LAB"]["figure_floors"].get("LEAF STONE") == 3
      and lib and lib[0]["event"]["gift_item"] == {"FIRE_STONE": 1} and _TM["SS_LIBRA"]["figure_floors"].get("FIRE STONE") == 5,
      "the Cipher Lab's Leaf Stone (B2F) and the S.S. Libra's Fire Stone (Hold 3) lie on their floors")
ch = [o for o in _P["KAMINKO_HOUSE"]["route_menu"] if "CHOBIN" in o["text"]]   # (11-21: XD's third Chobin battle gives it - Orre batch 5b)
check(any(o["event"]["battle"]["rewards"].get("SUN_STONE") == 1 for o in ch), "Chobin hands over his Sun Stone when you beat him")
du = next(p for p in _TM["PYRITE_TOWN"]["rooms"]["duking"]["people"] if isinstance(p, dict) and p.get("text") == "Duking")
story.story_flags.pop("orre_miror_cave", None); story.story_flags.pop("orre_duking_plusle", None)
_said.clear()
_n = len(story.player_team)
_run_story_event(st, du["event"], lambda c: story.story_flags.get(c) if not c.startswith("party") else True, _show)
early = len(story.player_team) == _n
story.story_flags["orre_miror_cave"] = True
_run_story_event(st, du["event"], lambda c: story.story_flags.get(c) if not c.startswith("party") else True, _show)
check(early and len(story.player_team) == _n + 1 and story.player_team[-1].id == 311,
      "Duking gives you Plusle once Miror B. is beaten at Pyrite Cave (not before)")
story.player_team = story.player_team[:_n]


print(f"##### {fails} failures")
