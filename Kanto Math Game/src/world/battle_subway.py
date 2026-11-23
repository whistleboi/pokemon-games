"""Black 2 / White 2's Battle Subway (Unova batch 4b, 11-23; Jordan: "all lines", streaks earning BP, no special rules;
"Lv 50, as Black 2"; "walk into the car").

Data: assets/b2_subway.json (dev/builders/unova_subway.py, from the game file): the 314 Subway Trainers, their Pokemon
sets, who may appear at which battle of a streak ("ranges"), the Subway Bosses and the Multi partners.

How a ride goes (maps: dev/builders/town_maps/unova.py, Gear Station's rooms):
- A line's platform: its Depot Agent boards you (event {"world": "battle_subway", "board": <line>}). The car room's
  "enter" scenes then play: the next Trainer walks in from the next car (a scene per walking look, by the condition
  "world:battle_subway:foe:<sheet>"), and their scene's "then" starts the battle ({"world": ..., "fight": true}).
- The battle is a facility battle (battle.py hands its end to after_battle here): no whiting out; healed after each.
- Won: the streak goes on. "Next car: No. n" - CONTINUE (the next Trainer walks in) or RETIRE (off at the platform,
  the streak over). After the seventh: off at the line's end (the Battle Subway's own station), with the train's BP.
- Lost: the streak ends, back on the platform.
- The Subway Bosses: Ingo (Single), Emmet (Double), both (Multi) as the 21st Trainer of the normal lines (beating them
  opens that line's Super train) and the 49th of the Super lines. The Multi lines: Nate or Rosa (the other of the two
  from you) battles beside you, with the team style you pick (attack / defence / balance: the file's three pools).
- Battle Points: WIN_BP for each win (battle_points.py), BRAIN_BP more for a Boss.
Story flags: b2_sub_<line>_streak (now), b2_sub_<line>_best, b2_sub_<line>_boss (its Boss beaten); b2_sub_riding (the
line on board), b2_sub_foe (the next Trainer's id), b2_sub_partner_pool."""
import json
import os
import random

LINES = {
    # line: (its name, battle kind, the file's "normal"/"super" ranges, the Boss key, the line whose Boss opens it)
    "single": ("Single Train", "single", "normal", "single", None),
    "double": ("Double Train", "double", "normal", "double", None),
    "multi": ("Multi Train", "multi", "normal", "multi", None),
    "super_single": ("Super Single Train", "single", "super", "single", "single"),
    "super_double": ("Super Double Train", "double", "super", "double", "double"),
    "super_multi": ("Super Multi Train", "multi", "super", "multi", "multi"),
}
TRAIN = 7
BOSS_AT = {"normal": 21, "super": 49}
AREA = "NIMBASA_CITY"
CAR = (8, 4)            # (where you stand in the car; the Trainer walks in from the next car's door)
CAR_ROOM, STOP_ROOM = "car", "subway_stop"
STOP_AT = (20, 12)
_DATA = None


def data(game=None):
    global _DATA
    if _DATA is None:
        base = getattr(getattr(game, "assets", None), "assets_dir", None) or os.path.join(os.path.dirname(__file__), "..", "..", "assets")
        with open(os.path.join(base, "b2_subway.json"), encoding="utf-8") as f:
            _DATA = json.load(f)
    return _DATA


def _flags(game):
    return game.story_manager.story_flags


def streak(game, line):
    return int(_flags(game).get(f"b2_sub_{line}_streak", 0) or 0)


def is_open(game, line):
    need = LINES[line][4]
    return not need or bool(_flags(game).get(f"b2_sub_{need}_boss"))


def platform_room(line):
    return "plat_" + line


# ------------------------------------------------------------------------------------------------ who's next
def _pick(game, line, n):
    """The Trainer id for battle n of the streak (1-based): the line's ranges, never the same Trainer twice in a train."""
    rows = data(game)["ranges"][LINES[line][2]]
    spans = next((sp for lo, hi, sp in rows if lo <= n <= hi), rows[-1][2])
    ids = [i for a, b in spans for i in range(a, b + 1) if str(i) in data(game)["trainers"]]
    seen = set(_flags(game).get("b2_sub_seen") or [])
    ids = [i for i in ids if i not in seen] or ids
    return random.choice(ids)


def boss_next(game, line):
    return streak(game, line) + 1 == BOSS_AT[LINES[line][2]]


def next_foe(game, line):
    """Choose the next opponent (kept in b2_sub_foe so the car's scene shows who walks in)."""
    f = _flags(game)
    n = streak(game, line) + 1
    f["b2_sub_foe"] = "boss" if boss_next(game, line) else _pick(game, line, n)
    return f["b2_sub_foe"]


def foe_sheet(game):
    """The walking look of the one who walks into the car next (the car scenes' condition)."""
    f = _flags(game)
    foe = f.get("b2_sub_foe")
    if foe == "boss":
        kind = LINES.get(f.get("b2_sub_riding") or "single", LINES["single"])[1]
        return "b2_c107.png" if kind == "double" else "b2_c207.png"   # (Emmet for the doubles; Ingo leads otherwise: Nimbasa's own looks)
    t = data(game)["trainers"].get(str(foe)) or {}
    return t.get("walk") or "b2_c68.png"


def condition(story, arg):
    """"foe:<sheet>": the next one into the car looks like that; "riding": a train is running; "open:<line>"."""
    game = getattr(story, "game", None)
    f = story.story_flags
    if arg == "riding":
        return bool(f.get("b2_sub_riding"))
    if arg.startswith("foe:"):   # (not while you're choosing CONTINUE / RETIRE between cars)
        return bool(f.get("b2_sub_riding")) and not f.get("b2_sub_wait") and game is not None and foe_sheet(game) == arg[4:]
    if arg.startswith("open:"):
        return game is not None and is_open(game, arg[5:])
    return False


# ------------------------------------------------------------------------------------------------ the battle
def _mon(game, sid):
    s = data(game)["sets"].get(str(sid)) or {}
    return s


def _team(game, pool, n):
    pool = list(pool)
    random.shuffle(pool)
    out, species = [], set()
    for sid in pool:
        s = _mon(game, sid)
        if s and s["species"] not in species:   # (Black 2: no two of the same species on a team)
            out.append(s)
            species.add(s["species"])
        if len(out) == n:
            break
    return out


def _info(game, tid, n):
    t = data(game)["trainers"][str(tid)]
    mons = _team(game, t["pool"], n)
    return {"name": t["name"], "class": t["class"], "sprite": t["sprite"], "team": [m["species"] for m in mons],
            "levels": [data(game)["level"]] * len(mons), "team_moves": [m["moves"] for m in mons],
            "held": [m.get("item") for m in mons], "rewards": {"balls": 3}}


def _boss_infos(game, line):
    kind, tier = LINES[line][1], LINES[line][2]
    b = data(game)["bosses"]
    sup = 1 if tier == "super" else 0
    ids = [b["single"][sup]] if kind == "single" else [b["double"][sup]] if kind == "double" else list(b["multi"][sup])
    out = []
    for tid in ids:
        t = data(game)["trainers"][str(tid)]
        mons = [_mon(game, s) for s in t["pool"] if _mon(game, s)]
        out.append({"name": t["name"], "class": "SUBWAY_BOSS", "sprite": t["sprite"], "team": [m["species"] for m in mons],
                    "levels": [data(game)["level"]] * len(mons), "team_moves": [m["moves"] for m in mons],
                    "held": [m.get("item") for m in mons], "rewards": {"balls": 5}, "is_boss_battle": True})
    return out


def partner_name(game):
    """Your Multi Train partner: Nate for a girl, Rosa for a boy (as at Gear Station's door)."""
    from src.world import unova_story
    return "nate" if unova_story.female(game.story_manager) else "rosa"


def _partner(game):
    who = partner_name(game)
    pools = data(game)["partners"][who]
    k = int(_flags(game).get("b2_sub_partner_pool", 2) or 0)
    t = data(game)["trainers"][str(pools[max(0, min(2, k))])]
    mons = _team(game, t["pool"], 2)
    return {"name": who.title(), "class": "POKEMON_TRAINER", "sprite": f"b2_{who}.png", "team": [m["species"] for m in mons],
            "levels": [data(game)["level"]] * len(mons), "team_moves": [m["moves"] for m in mons],
            "held": [m.get("item") for m in mons]}


def battle_info(game, line):
    """The next battle's trainer info (with "battle_options" for doubles, the Multi partner and Lv 50)."""
    f = _flags(game)
    kind = LINES[line][1]
    n = 2 if kind == "multi" else 4 if kind == "double" else 3
    if f.get("b2_sub_foe") == "boss":
        infos = _boss_infos(game, line)
    else:
        first = int(f.get("b2_sub_foe") or next_foe(game, line))
        infos = [_info(game, first, n)]
        if kind == "multi":   # (a second Trainer from the same span)
            infos.append(_info(game, _pick(game, line, streak(game, line) + 1), n))
    info = dict(infos[0])
    opts = {"level_cap": data(game)["level"],   # (yours above Lv 50 battle at 50: main's battle option, when it's there)
            "music": "unova/vs_subway_trainer"}  # (Black 2's own Subway battle theme, SEQ_BGM_VS_SUBWAY_TRAINER)
    if kind in ("double", "multi"):
        opts["double"] = True
    if kind == "multi":
        opts["second_trainer"] = infos[1]
        opts["partner"] = _partner(game)
    info["battle_options"] = opts
    info["facility"] = {"world": "battle_subway", "line": line}
    return info


def start_battle(game, line):
    """The battle with whoever just walked in: built as an event battle, Lv 50 kept even after the title."""
    from src.states.battle import TrainerBattleState, TrainerIntroState
    from src.states.battle_double import battle_options
    from src.states.overworld.common import _trainer_sprite
    from src.states.overworld.common import Pokemon
    from src.pokemon import forms
    from src.world import levels
    story = game.story_manager
    info = battle_info(game, line)
    team = [Pokemon(game.loader.fetch_specific(s), game.assets, size_mult=3.125) for s in info["team"]]
    forms.mark_trainer_team(team, info)
    levels.set_team(team, list(info["levels"]), exact=True)
    sprite = _trainer_sprite(game, info["sprite"])
    battle = TrainerBattleState(game, team, trainer_sprite=sprite, trainer_class=info["class"], trainer_name=info["name"],
                                rewards=dict(info["rewards"]), battle_type="event", is_boss_battle=info.get("is_boss_battle", False),
                                area_name=story.current_area_key, victory_flag=None, options=battle_options(info))
    battle.facility = info["facility"]
    n = streak(game, line) + 1
    intro = [f"{info['name']}: " + random.choice(["Let's battle!", "Here I come!", "Show me what you've got!", "All aboard for a battle!"])]
    if _flags(game).get("b2_sub_foe") == "boss":
        intro = [f"{info['name']}: Welcome to the Battle Subway's final stop... battle number {n}! Let's go!"]
    game.change_state(TrainerIntroState(game, sprite, intro, battle))


# ------------------------------------------------------------------------------------------------ moving you
def _put(game, room, at, face=(0, -1), lines=None):
    from src.states.overworld import CityState
    story = game.story_manager
    story.current_area_key = AREA
    game.walk_town_pos = (AREA, tuple(at), face)
    game.walk_town_room = (AREA, room)
    st = CityState(game)
    game.change_state(st)
    if lines:
        if hasattr(st, "npc_say"):   # (a walked town or room: its own speech box)
            st.npc_say(list(lines), lambda: None)
        else:
            st.show_message(list(lines))
    return st


def into_car(game):
    _put(game, CAR_ROOM, CAR, (1, 0))


def end_ride(game, line, lines, to_stop):
    f = _flags(game)
    f.pop("b2_sub_riding", None)
    f.pop("b2_sub_foe", None)
    f.pop("b2_sub_seen", None)
    if to_stop:
        f["b2_sub_stop_line"] = line
        _put(game, STOP_ROOM, STOP_AT, (0, 1), lines)
    else:
        _put(game, platform_room(line), (11, 13), (0, 1), lines)


# ------------------------------------------------------------------------------------------------ the map's events
def event(state, ev, lines, show):
    """{"board": line}: the platform's Depot Agent; {"fight": true}: the car's scene ends in the battle;
    {"stop": true}: the end station's agent (the next train, or back to Gear Station); {"partner": true}: the Multi pick."""
    game = state.game
    f = _flags(game)
    from src.states.overworld.common import _say_then
    from src.states.systems.pick_list import PickListState
    if ev.get("board"):
        line = ev["board"]
        name = LINES[line][0]
        if not is_open(game, line):
            show(lines or [f"Depot Agent: The {name} is for Trainers who've beaten a Subway Boss on its line.",
                           f"Win 21 battles in a row on the {LINES[LINES[line][4]][0]} first!"])
            return
        if not [p for p in game.story_manager.player_team if p and p.current_hp > 0]:
            show(["Depot Agent: Your Pokemon can't battle. Please heal them first!"])
            return
        said = list(lines or []) + [f"Depot Agent: Welcome to the {name}! Seven Trainers ride each train. Your Pokemon battle "
                                    f"at Lv 50, and they're healed after every battle.",
                                    f"Your streak on this line: {streak(game, line)}. All aboard!"]

        def board():
            f["b2_sub_riding"] = line
            f["b2_sub_seen"] = []
            next_foe(game, line)
            into_car(game)
        if LINES[line][1] == "multi":
            who = partner_name(game).title()
            rows = [("ATTACK", 0), ("DEFENCE", 1), ("BALANCE", 2)]

            def chose(k):
                if k is None:
                    show(["Depot Agent: Come back when you're ready!"])
                    return
                f["b2_sub_partner_pool"] = k
                board()
            said.append(f"{who}: I'll ride with you! What kind of team should I bring?")
            _say_then(state, said, lambda: game.change_state(PickListState(game, state, f"{who.upper()}'S TEAM?", rows, chose)))
            return
        _say_then(state, said, board)
        return
    if ev.get("fight"):
        line = f.get("b2_sub_riding")
        if line in LINES:
            start_battle(game, line)
        else:
            show(lines or ["..."])
        return
    if ev.get("stop"):
        line = f.get("b2_sub_stop_line") or "single"
        rows = [("NEXT TRAIN", "go"), ("BACK TO GEAR STATION", "back")]

        def picked(k):
            if k == "go":
                f["b2_sub_riding"] = line
                f["b2_sub_seen"] = []
                next_foe(game, line)
                into_car(game)
            else:
                _put(game, "gear", (16, 32), (0, -1), ["You rode back to Gear Station."])
        said = list(lines or []) + [f"Depot Agent: Your streak on the {LINES[line][0]}: {streak(game, line)}. "
                                    "Ride on, or back to Gear Station?"]
        _say_then(state, said, lambda: game.change_state(PickListState(game, state, "WHERE TO?", rows, picked)))
        return
    show(lines or ["..."])


def after_battle(game, info, won):
    """battle.py at a Subway battle's end: lines to say, or a function that goes on itself."""
    from src.world import battle_points as bp
    from src.states.overworld.area_transition import heal_team
    f = _flags(game)
    line = info.get("line") or f.get("b2_sub_riding") or "single"
    name = LINES[line][0]
    heal_team(game)
    was_boss = f.get("b2_sub_foe") == "boss"
    if not won:
        n = streak(game, line)
        f[f"b2_sub_{line}_streak"] = 0
        return lambda: end_ride(game, line, [f"Your streak on the {name} ended at {n}.", "Your Pokemon were healed."], False)
    seen = list(f.get("b2_sub_seen") or [])
    if str(f.get("b2_sub_foe")).isdigit():
        seen.append(int(f["b2_sub_foe"]))
    f["b2_sub_seen"] = seen
    n = streak(game, line) + 1
    f[f"b2_sub_{line}_streak"] = n
    f[f"b2_sub_{line}_best"] = max(n, int(f.get(f"b2_sub_{line}_best", 0) or 0))
    from src.world import feats
    feats.note_best(game.story_manager, "subway", n)   # (the Quest Book's Subway Regular: the best streak)
    got = bp.add_bp(game.story_manager, bp.WIN_BP + (bp.BRAIN_BP if was_boss else 0))
    said = [f"You earned {got} BP! You have {bp.bp(game.story_manager)} BP."]
    if was_boss and LINES[line][2] == "normal" and not f.get(f"b2_sub_{LINES[line][3]}_boss"):
        f[f"b2_sub_{LINES[line][3]}_boss"] = True
        said.append(f"You beat the Subway Boss! The Super {name.split()[0]} Train is open to you now!")
    elif was_boss:
        f[f"b2_sub_{LINES[line][3]}_super_boss"] = True
        said.append("You beat the Subway Bosses on the Super line! A trophy is waiting for you at home.")
    if n % TRAIN == 0:
        from src.world import anville   # (Anville's lost-and-found finds something each time a train is won)
        anville.found_item(game.story_manager)
        return lambda: end_ride(game, line, [f"This is the end of the {name} line. {n} wins in a row!"] + said, True)
    next_foe(game, line)

    def ask():
        from src.states.systems.pick_list import PickListState
        f["b2_sub_wait"] = True
        st = _put(game, CAR_ROOM, CAR, (1, 0))

        def picked(k):
            f.pop("b2_sub_wait", None)
            if k == "retire":
                f[f"b2_sub_{line}_streak"] = 0
                end_ride(game, line, [f"You got off the {name}. Your streak ends at {n}."], False)
            else:
                into_car(game)
        game.change_state(PickListState(game, st, f"{n} WINS! NEXT CAR: No. {n % TRAIN + 1}",
                                        [("CONTINUE", "go"), ("RETIRE", "retire")], picked))
    return ask
