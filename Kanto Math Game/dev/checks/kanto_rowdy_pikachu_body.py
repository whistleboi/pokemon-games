# The rowdy Pikachu (Pokemon Yellow, Jordan 11-16; src/pokemon/rowdy.py): played the way a player meets it.
#   bash dev/checks/run.sh kanto_rowdy_pikachu
from src.states import overworld as ow
from src.pokemon import rowdy, evolution
from src.states.systems.pick_list import PickListState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m); fails += 0 if c else 1


g.data.save = lambda *a, **k: None
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())   # (Pallet and Littleroot are walked: Oak and Mom met on the map, 11-24)


def finish(city, limit=12):
    """Tap through the talk on screen (each line, then its callback), until nothing more is said."""
    said = []
    for _ in range(limit):
        d = getattr(city, "npc_dialogue", None)
        if d is None or not getattr(city, "npc_active", False):
            break
        said += list(getattr(d, "text_lines", None) or getattr(d, "lines", None) or [])
        cb = getattr(d, "callback", None)
        city.npc_dialogue = None
        if cb:
            cb()
        if g.current_state is not city:
            break
    return said


print("1) Oak holds it back until Lt. Surge is beaten")
story.current_area_key = "PALLET_TOWN"
story.starting_region = "KANTO"
story.story_flags.update({"received_starter_kanto": True, "mew_spotted_mt_moon": True})
story.story_flags.pop(rowdy.GIVEN, None)
story.badges["KANTO"] = ["BOULDER", "CASCADE"]
story.badges["JOHTO"] = []
story.player_team[:] = story.player_team[:1]
check(not rowdy.can_get(story), "two badges: no Pikachu yet")
_side = [m.get("id") for m in story.get_active_missions()]
check("s_rowdy_pikachu" not in _side, "...and nothing in the Journal")
story.badges["KANTO"].append("THUNDER")
check(rowdy.can_get(story), "the Thunder Badge: Oak has one for you")
_side = [m.get("id") for m in story.get_active_missions()]
check("s_rowdy_pikachu" in _side, f"the Journal's side mission sends you to Oak ({_side[:4]})")
city = walk_town("PALLET_TOWN", "KANTO_ROUTE_1")
said = walk_meet(city, npc("professor_oak"), choose="Professor Oak") or []   # (into the lab, walk up to Oak)
pk = rowdy.in_party(story)
check(pk is not None, "Oak gives the Pikachu (it joins the party)")
check(any("PIKACHU" in l for l in said), f"he says so ({len(said)} lines)")
check(pk is not None and pk.level == 5 and pk.id == 25, "Lv 5 Pikachu")
check(pk is not None and all(v == 31 for v in pk.ivs.values()), "perfect IVs")
check(pk is not None and "VOLT-TACKLE" in pk.moves, f"knows Volt Tackle ({pk.moves if pk else None})")
check(not rowdy.can_get(story), "only once")
check("s_rowdy_pikachu" not in [m.get("id") for m in story.get_active_missions()], "the side mission is done")

print("2) it never evolves")
check(evolution.evolution_options(g, pk) == [], "nothing to evolve into")
check(evolution.item_evolution(g, pk, "THUNDER_STONE") in (None, [], False), "a Thunder Stone does nothing")
pk.level = 60
check(evolution.ready_evolutions(g, pk) == [], "not at Lv 60 either")
pk.level = 5

print("3) it always walks behind you")
other = mk(6); story.player_team.insert(0, other)   # (a Charizard leads the party)
dn = ow.dungeon.DungeonState.__new__(ow.dungeon.DungeonState); dn.game = g
check(dn.lead() is other and dn.follower() is pk, "Charizard leads, Pikachu follows")
from src.states.overworld.walk_town import WalkTownState
check(WalkTownState.follower(dn) is pk, "in towns too (the same rule)")

print("4) the PC, the Day Care and trades turn it away")
from src.states.systems.pc import PCState
pc = PCState(g, city)
i = story.player_team.index(pk)
pc.selected_party_idx = i
empty = next(k for k, p in enumerate(pc.pc) if p is None)
pc.handle_click("pc", empty)
check(rowdy.in_party(story) is pk and pc.pc[empty] is None, "it can't be put in a box")
check(story.deposit_to_pc(pk) is None and rowdy.at_mom(story), "an automatic deposit sends it home to Mom instead")
story.story_flags.pop(rowdy.LOCKER, None)
from src.states.daycare import DaycareState
dc = DaycareState(g, city); before = len(story.player_team)
dc.leave(story.player_team.index(pk))
check(len(story.player_team) == before and rowdy.in_party(story), "the Day Care can't take it")

print("5) Mom keeps it, in any region")
story.starting_region = "KANTO"   # (a Kanto player: Mom lives in Pallet Town; from Hoenn on, in every start town)
city = walk_town("PALLET_TOWN", "KANTO_ROUTE_1")
w = walk_meet(city, npc("mom"), picks=["leave"])   # (home, walk up to Mom: she offers to keep it; leave it)
check(w is not None, "Kanto Mom offers to keep Pikachu")
check(rowdy.in_party(story) is None and rowdy.at_mom(story), "left with Mom")
city = walk_town("LITTLEROOT_TOWN", "HOENN_ROUTE_101")
w = walk_meet(city, npc("mom"), picks=["take"])
check(w is not None, f"Hoenn Mom has it too ({(w or [])[:1]})")
pk = rowdy.in_party(story)
check(pk is not None and not rowdy.at_mom(story), "picked up in Hoenn")
check(pk is not None and pk.moves and "VOLT-TACKLE" in pk.moves and all(v == 31 for v in pk.ivs.values()), "still the same Pikachu")

print("6) a save keeps it")
rec = story._pokemon_record(pk)
back = story._load_pokemon(rec, g.loader)
check(rowdy.is_rowdy(back), "saved and loaded: still the rowdy Pikachu")
check(evolution.evolution_options(g, back) == [], "and still won't evolve")

print(f"##### {fails} failures")
