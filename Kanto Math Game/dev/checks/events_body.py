
import json, glob
from src.world import story_events
from src.states.overworld import CityState, PlayState
from src.states.battle import TrainerBattleState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


where = {}
prog = g.loader.area_data["STORY_PROGRESSION"]
for area, a in prog.items():
    def walk(o):
        if isinstance(o, dict):
            if o.get("action") == "NPC" and o.get("target") in story_events.EVENTS:
                where.setdefault(o["target"], area)
            if o.get("type") == "event" and o.get("event") in story_events.EVENTS:  # on arrival
                where.setdefault(o["event"], area)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(a)
import json as _json, re as _re   # (a story scene on a walked map runs its event too: "then": "event:<key>", Johto's opening, Oak's Potions)
_scene_events = set(_re.findall(r'"then": "event:([a-z0-9_]+)"', open("assets/town_maps.json", encoding="utf-8").read()))
from src.world import mystery_dungeon as _md   # (and the scenes laid over the maps in code: the Giant Volcano's walk)
_scene_events |= set(_re.findall(r'"then": "event:([a-z0-9_]+)"', _json.dumps(_md.CAST)))
missing = [k for k in story_events.EVENTS if k not in where and k not in _scene_events]
check(not missing, f"every event has a button: missing {missing}")


def make_state(area):
    story.current_area_key = area
    if prog[area].get("area_type") == "town":
        s = CityState(g)
        g.states["city"] = s
    else:
        s = PlayState(g)
        g.states["play"] = s
    g.current_state = s
    return s


def shown(s):
    box = getattr(s, "npc_dialogue", None) or getattr(s, "dialogue_box", None)
    return list(getattr(box, "text_lines", []) or [])


story.player_team = [mk(25)]
# A requirement blocks the event and says why.
s = make_state(where["galactic_lake_verity"])
story.story_flags.pop("galactic_lake_verity_cleared", None)
s.story_event("galactic_lake_verity")
check(not isinstance(g.current_state, type(None)) and g.current_state is s, "Lake Verity is locked without the Fen Badge")

# Everything else: requirements met by patching the condition checks.
CityState._check_menu_condition = lambda self, c: True
PlayState._check_route_condition = lambda self, c, t=None, i=None: True
for key, ev in story_events.EVENTS.items():
    area = where.get(key)
    if not area:
        continue
    flag = ev.get("flag")
    if flag:
        story.story_flags.pop(flag, None)
    team_before = len(story.player_team) + sum(1 for p in story.pc_pokemon if p)
    s = make_state(area)
    try:
        s.story_event(key)
    except Exception as e:
        check(False, f"{key} @ {area}: crashed {type(e).__name__}: {e}")
        continue
    cur = g.current_state
    if ev.get("battle"):
        nxt = getattr(cur, "next_state", None)
        ok = isinstance(nxt, TrainerBattleState) and nxt.victory_flag == flag and len(nxt.opponent_team) >= 1
        lv = [p.level for p in nxt.opponent_team] if ok else None
        check(ok, f"{key} @ {area}: battle vs {getattr(nxt, 'trainer_name', None)} "
                  f"{[p.name for p in nxt.opponent_team] if ok else ''} lv {lv}")
        if ok:
            nxt.player_won = True
            try:
                nxt.exit_battle()
            except Exception as e:
                check(False, f"{key}: exit_battle crashed {type(e).__name__}: {e}")
                continue
            check(story.story_flags.get(flag), f"{key}: win sets {flag}")
            for item in (ev["battle"].get("rewards") or {}):
                if item.startswith("POKEMON_"):
                    after = len(story.player_team) + sum(1 for p in story.pc_pokemon if p)
                    check(after == team_before + 1, f"{key}: gift Pokemon {item} received")
                elif item != "balls":
                    check(story.inventory.get(item, 0) > 0, f"{key}: reward {item}")
    elif ev.get("scene"):  # a scene that plays itself (Wally's Ralts), then the event finishes
        box = getattr(cur, "npc_dialogue", None) or getattr(cur, "dialogue_box", None)
        if box is not None and box.callback:  # the lines before it, then the scene
            box.callback()
        scene = g.current_state
        for _ in range(3000):
            if g.current_state is not scene:
                break
            scene.update()
        check(g.current_state is not scene and story.story_flags.get(flag), f"{key}: the scene ends and sets {flag}")
    else:
        lines = shown(cur)
        check(bool(lines) and all("{" not in l for l in lines), f"{key} @ {area}: {lines[:1]}")
        if flag:
            check(story.story_flags.get(flag), f"{key}: sets {flag}")
        if ev.get("gift_pokemon"):
            after = len(story.player_team) + sum(1 for p in story.pc_pokemon if p)
            check(after == team_before + 1, f"{key}: gift Pokemon received")
        # Clicking again shows the 'done' text, no second gift.
        if flag:
            s2 = make_state(area)
            n = len(story.player_team)
            s2.story_event(key)
            check(len(story.player_team) == n, f"{key}: no repeat gift")
print("a gift with a set Ability (Route 6's Deerling: Serene Grace, its hidden one; Black 2; 11-24)")
from src.world import story_events as _se
from src.pokemon import abilities as _abl
story.player_team = story.player_team[:1]
_se.gift_pokemon(g, 585, 20, None, "SERENE-GRACE", True)
_d = story.player_team[-1]
check(_d.id == 585 and _d.ability_slot == _abl.HIDDEN_SLOT and not _d.is_shiny, f"Deerling: Serene Grace, not Shiny (slot {_d.ability_slot})")
check(_se.gift_ability_slot(g, 585, "hidden") == 2 and _se.gift_ability_slot(g, 585, "Sap Sipper") == 1 and _se.gift_ability_slot(g, 585, 0) == 0,
      "the Ability by 'hidden', by name or by slot")
print("an in-game trade with no flag of its own happens once (the encyclopedia's nine, 11-24)")
from src.states.overworld.common import _run_story_event as _rse
from src.pokemon.data import Pokemon as _Pk
story.current_area_key = "OLIVINE_CITY"
story.player_team = [_Pk(g.loader.fetch_specific(19), g.assets), _Pk(g.loader.fetch_specific(19), g.assets)]
_said = []
_tev = {"lines": ["Trade your Rattata for my Pidgey?"], "trade": {"want": 19, "give": 16}}
class _S: pass
_st = _S(); _st.game = g
_rse(_st, _tev, lambda c: True, lambda l: _said.append(l))
check(sum(1 for p in story.player_team if p.id == 16) == 1, "the first time: traded")
_rse(_st, _tev, lambda c: True, lambda l: _said.append(l))
check(sum(1 for p in story.player_team if p.id == 16) == 1 and "Thanks again" in str(_said[-1]), f"the second time: no second trade ({_said[-1]})")
print(f"##### {fails} failures")
