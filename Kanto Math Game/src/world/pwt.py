"""The Pokemon World Tournament (Black 2 / White 2; Unova batch 5b, 11-24), through main's region hook ({"world": "pwt"}).
Data: assets/b2_pwt.json (dev/builders/unova_pwt.py, from Black 2's own file: the Leaders' and Champions' teams, the
Driftveil Tournament's; rosters and BP from Bulbapedia). Jordan's calls: every tournament, Black 2's levels; no special
rules (Rental / Mix / Type Expert are ordinary tournaments with their rosters); Triple and Rotation Battles as Doubles.

A tournament: pick it at a desk (left: Driftveil, Rental, Mix; right: the specialty ones, as they open), then Single or
Double; eight entrants, three rounds: each round a facility battle (no whiting out), healed between, at the tournament's
level (Driftveil 25, the rest 50; your Pokemon above it battle at it). Win all three: BP (Black 2's by tournament and
style) and the title; lose: a Shard as a consolation prize. The story's first Driftveil Tournament (Clay's invitation): Hugh,
Cheren, Colress in turn, your Pokemon at their own levels; winning it sets b2_pwt_driftveil_won.
Flags: b2_pwt_run (the tournament now: key, style, round, opponents), b2_pwt_won_<key> (wins), b2_pwt_driftveil_won."""
import json
import os
import random

AREA = "PWT"
LOBBY, STADIUM = "lobby", "stadium"
LOBBY_AT, STADIUM_AT = (15, 8), (24, 15)   # (the hall: before the stadium's doors; the stadium: your end of the field)
SHARDS = ["RED_SHARD", "BLUE_SHARD", "YELLOW_SHARD", "GREEN_SHARD"]
THEMES = {"KANTO": "unova/vs_rg_leader", "JOHTO": "unova/vs_gs_leader", "HOENN": "unova/vs_rs_leader",
          "SINNOH": "unova/vs_dp_leader", "UNOVA": "unova/vs_gymleader"}
CHAMP_THEMES = {"Blue": "unova/vs_rg_champ", "Red": "unova/vs_rg_champ", "Lance": "unova/vs_gs_champ",
                "Steven": "unova/vs_rs_champ", "Wallace": "unova/vs_rs_champ", "Cynthia": "unova/vs_dp_champ",
                "Alder": "unova/vs_bw_champ"}
_DATA = None


def data(game=None):
    global _DATA
    if _DATA is None:
        base = getattr(getattr(game, "assets", None), "assets_dir", None) or os.path.join(os.path.dirname(__file__), "..", "..", "assets")
        with open(os.path.join(base, "b2_pwt.json"), encoding="utf-8") as f:
            _DATA = json.load(f)
    return _DATA


def _flags(game):
    return game.story_manager.story_flags


def wins(game, key):
    return int(_flags(game).get("b2_pwt_won_" + key, 0) or 0)


def _region_of(name):
    for key in ("kanto", "johto", "hoenn", "sinnoh"):
        if name in tournament(key)["roster"]:
            return key.upper()
    return "UNOVA"


def tournament(key):
    return next((t for t in data()["tournaments"] if t["key"] == key), None)


def is_open(game, t):
    story = game.story_manager
    for need in t["opens"]:
        if need.startswith("won10:"):
            if wins(game, need[6:]) < 10:
                return False
        elif need.startswith("won:"):
            if wins(game, need[4:]) < 1:
                return False
        elif need == "beat_unova_champion":
            try:
                if not story.is_region_champion("UNOVA"):
                    return False
            except Exception:
                if not story.story_flags.get(need):
                    return False
        elif not story.story_flags.get(need):
            return False
    return True


def first_visit(game):
    return not _flags(game).get("b2_pwt_driftveil_won")


def _roster(game, t, kind=None):
    d = data(game)
    if t["roster"] == "driftveil":
        return list(d["drift"])
    if t["roster"] == "type":
        return [n for n, x in d["trainers"].items() if x.get("type") == kind]
    return list(t["roster"])


def opponents(game, t, kind=None):
    """The three you'll meet: the story's first visit Hugh, Cheren, Colress; the Driftveil Tournament after that one of
    its regulars, then two of its notable Trainers (Black 2: "two notable Trainers ... the second round and the final")."""
    if t["key"] == "driftveil" and first_visit(game):
        return ["Hugh", "Cheren", "Colress"]
    pool = _roster(game, t, kind)
    if t["roster"] == "driftveil":
        notable = [n for n in pool if n in ("Cheren", "Roxie", "Burgh", "Elesa", "Clay")]
        regular = [n for n in pool if n not in notable]
        picks = random.sample(notable, 2)
        return [random.choice(regular)] + picks
    return random.sample(pool, min(3, len(pool)))


def _entry(game, name, t):
    d = data(game)
    if t["key"] == "driftveil" and first_visit(game) and name in d["story"]:
        return d["story"][name], "drift"
    if t["roster"] == "driftveil":
        return d["drift"][name], "drift"
    return d["trainers"][name], "main"


def battle_info(game, run):
    t = tournament(run["key"])
    name = run["opponents"][run["round"] - 1]
    e, pool = _entry(game, name, t)
    sets = data(game)["sets"][pool]
    ids = list(e["sets"])
    if e.get("by_starter"):   # (Hugh's starter: the one that beats yours)
        from src.states.overworld.common import _region_starter_id
        ids = e["by_starter"].get(str(_region_starter_id(game)), ids[:3])
    if run["style"] == "single":   # (Black 2: the first two, and one of the other four)
        ids = ids[:2] + ([random.choice(ids[2:])] if len(ids) > 2 else [])
    else:
        ids = ids[:4]
    mons = [sets[str(s)] for s in ids if str(s) in sets]
    level = t["level"]
    info = {"name": e["name"], "class": e["class"], "sprite": e["sprite"], "team": [m["species"] for m in mons],
            "levels": [level] * len(mons), "team_moves": [m["moves"] for m in mons], "held": [m.get("item") for m in mons],
            "rewards": {"balls": 3}, "is_boss_battle": e["class"] in ("GYM_LEADER", "CHAMPION")}
    music = CHAMP_THEMES.get(name) if e["class"] == "CHAMPION" else THEMES.get(_region_of(name)) if e["class"] == "GYM_LEADER" \
        else "unova/vs_wcs"
    opts = {"music": music}
    if not (t["key"] == "driftveil" and first_visit(game)):
        opts["level_cap"] = level   # (yours above the tournament's level battle at it)
    if run["style"] == "double":
        opts["double"] = True
    info["battle_options"] = opts
    info["facility"] = {"world": "pwt", "key": run["key"]}
    return info


def start_battle(game, run, said=()):
    from src.states.battle import TrainerBattleState, TrainerIntroState
    from src.states.battle_double import battle_options
    from src.states.overworld.common import _trainer_sprite, _fill_names
    from src.states.overworld.common import Pokemon
    from src.pokemon import forms
    from src.world import levels
    story = game.story_manager
    info = battle_info(game, run)
    team = [Pokemon(game.loader.fetch_specific(s), game.assets, size_mult=3.125) for s in info["team"]]
    forms.mark_trainer_team(team, info)
    levels.set_team(team, list(info["levels"]), exact=True)
    sprite = _trainer_sprite(game, info["sprite"])
    name = _fill_names(game, info["name"])
    battle = TrainerBattleState(game, team, trainer_sprite=sprite, trainer_class=info["class"], trainer_name=name,
                                rewards=dict(info["rewards"]), battle_type="event", is_boss_battle=info.get("is_boss_battle", False),
                                area_name=story.current_area_key, victory_flag=None, options=battle_options(info))
    battle.facility = info["facility"]
    rnd = ["the first round", "the semifinal", "the final"][run["round"] - 1]
    intro = list(said) + [f"Announcer: {tournament(run['key'])['name']}, {rnd}! {game.player_name} versus {name}!",
             f"{name}: " + random.choice(["Let's give the crowd a show!", "I won't hold back!", "This is what I came for!"])]
    game.change_state(TrainerIntroState(game, sprite, intro, battle))


def _put(game, room, at, face=(0, -1), lines=None):
    """Into one of the PWT's rooms (the hall, the stadium), at a spot, saying lines (as the Battle Subway moves you)."""
    from src.states.overworld import CityState
    story = game.story_manager
    story.current_area_key = AREA
    game.walk_town_pos = (AREA, tuple(at), face)
    game.walk_town_room = (AREA, room)
    st = CityState(game)
    game.change_state(st)
    if lines:
        if hasattr(st, "npc_say"):
            st.npc_say(list(lines), lambda: None)
        else:
            st.show_message(list(lines))
    return st


def to_stadium(game, run, said=()):
    """Out onto the field, and the round's battle starts (its announcer first)."""
    _put(game, STADIUM, STADIUM_AT, (-1, 0))
    start_battle(game, run, said)


def begin(game, key, style, kind=None):
    t = tournament(key)
    run = {"key": key, "style": style, "round": 1, "opponents": opponents(game, t, kind), "kind": kind}
    _flags(game)["b2_pwt_run"] = run
    to_stadium(game, run, [f"Announcer: Welcome to the {t['name']}! Eight Trainers, three rounds: win three in a row to take the title!"])


def event(state, ev, lines, show):
    """{"desk": "left" | "right"}: pick a tournament and a battle style; {"fight": true}: the stadium's next battle."""
    game = state.game
    from src.states.overworld.common import _say_then
    from src.states.systems.pick_list import PickListState
    f = _flags(game)
    if ev.get("desk"):
        desk = ev["desk"]
        if not f.get("b2_drift_clay_out") and desk == "left":
            show(lines or ["Receptionist: The Pokemon World Tournament is about to open! Please come back soon."])
            return
        opts = [t for t in data(game)["tournaments"] if t["desk"] == desk and is_open(game, t)]
        if not opts:
            show(["Receptionist: These tournaments open once you've proved yourself: first the Pokemon League, then the "
                  "Unova Leaders Tournament!"])
            return
        if desk == "left" and first_visit(game):
            said = list(lines or []) + ["Receptionist: Welcome to the Driftveil Tournament! Clay entered you himself. Good luck!"]
            _say_then(state, said, lambda: begin(game, "driftveil", "single"))
            return
        rows = [(t["name"].upper(), t["key"]) for t in opts]

        def chose(key):
            if key is None:
                show(["Receptionist: Come back any time!"])
                return
            if key == "type":
                types = sorted({x.get("type") for x in data(game)["trainers"].values() if x.get("type")})
                game.change_state(PickListState(game, state, "WHICH TYPE?", [(ty.title(), ty) for ty in types],
                                                lambda ty: style(key, ty) if ty else show(["Receptionist: Come back any time!"])))
                return
            style(key, None)

        def style(key, kind):
            game.change_state(PickListState(game, state, "BATTLE STYLE?", [("SINGLE", "single"), ("DOUBLE", "double")],
                                            lambda s: begin(game, key, s, kind) if s else show(["Receptionist: Come back any time!"])))
        game.change_state(PickListState(game, state, "WHICH TOURNAMENT?", rows, chose))
        return
    if ev.get("fight"):
        run = f.get("b2_pwt_run")
        if run:
            start_battle(game, run)
        else:
            show(lines or ["(The stadium is empty.)"])
        return
    show(lines or ["..."])


def after_battle(game, info, won):
    """battle.py at a tournament battle's end: lines to say, or a function that goes on itself."""
    from src.world import battle_points as bp
    from src.states.overworld.area_transition import heal_team
    f = _flags(game)
    run = dict(f.get("b2_pwt_run") or {})
    heal_team(game)
    if not run:
        return ["..."]
    t = tournament(run["key"])
    if not won:
        f.pop("b2_pwt_run", None)
        shard = random.choice(SHARDS)
        game.story_manager.inventory[shard] = game.story_manager.inventory.get(shard, 0) + 1
        return lambda: _put(game, LOBBY, LOBBY_AT, (0, 1), ["Announcer: What a battle! But that's the end of the road this time.",
                                                            f"Receptionist: Thanks for taking part. Please take this: a "
                                                            f"{shard.replace('_', ' ').title()}!"])
    if run["round"] < 3:
        run["round"] += 1
        f["b2_pwt_run"] = run
        return lambda: to_stadium(game, run, ["Announcer: What a win! On to the %s!" % ("semifinal" if run["round"] == 2 else "final"),
                                              "Your Pokemon were healed."])
    f.pop("b2_pwt_run", None)
    f["b2_pwt_won_" + run["key"]] = wins(game, run["key"]) + 1
    got = bp.add_bp(game.story_manager, t["bp"][0 if run["style"] == "single" else 1])
    said = [f"Announcer: And the winner of the {t['name']} is... {game.player_name}!",
            f"You earned {got} BP! You have {bp.bp(game.story_manager)} BP."]
    if run["key"] == "driftveil" and not f.get("b2_pwt_driftveil_won"):
        f["b2_pwt_driftveil_won"] = True
    from src.world import feats
    feats.note(game.story_manager, "pwt")
    return lambda: _put(game, LOBBY, LOBBY_AT, (0, 1), said)
