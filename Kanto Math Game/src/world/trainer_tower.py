"""FireRed's Trainer Tower on Seven Island (11-23, Kanto K2; Jordan: "Full tower, FireRed's", levels "FireRed's exactly",
"Clock on screen + record"). The maps: area TRAINER_TOWER (kanto_rom_tools/k_batch37.py): the lobby (floor 0), 1F-8F
(floors 1-8) and the roof (floor 9); its "story_maps" swap in the climb the receptionist signs you up for.
The trainers: assets/trainer_tower.json (FireRed's built-in sets: kanto_rom_tools/tt/tt_parse.py from pokefirered's
src/trainer_tower_sets.c).

FireRed's rules, kept:
- Four climbs: Single, Double, Knockout, Mixed (each floor one of the first three). Double and Mixed want two Pokemon.
- Every tower Pokemon is at your highest party level (BuildEnemyParty); which of a trainer's six it sends out is set by
  the floor ("pick": FireRed's sSingle/Double/KnockoutBattleChallengeMonIdxs).
- A floor's stairs up open once its trainers are beaten (one Single trainer, a Double pair, three Knockout trainers
  with one Pokemon each).
- Lose: your team is healed and you're back in the lobby; the climb is over.
- The clock (src/ui/challenge_clock.py) runs from signing up till you talk to the owner on the roof; he gives the
  climb's prize once (its 1F's prize, GiveChallengePrize) and keeps your best time for each climb.
Area options (sevii_area_data.json TRAINER_TOWER): {"world": "trainer_tower", "tt": "desk" | "trainer" | "owner"}."""
import json
import os

CLIMBS = ["SINGLE", "DOUBLE", "KNOCKOUT", "MIXED"]
WORDS = {"SINGLE": "Single Battle", "DOUBLE": "Double Battle", "KNOCKOUT": "Knockout", "MIXED": "Mixed"}
AREA = "TRAINER_TOWER"
LOBBY_SPOT = [9, 7]   # (FireRed's warp back to the lobby: 9,7, before the counter)
# FireRed's trainer classes: our battle picture
SPRITES = {"SAILOR": "sailor.png", "BUG_CATCHER": "bug_catcher.png", "JUGGLER": "juggler.png", "YOUNGSTER": "youngster.png",
           "CAMPER": "camper.png", "SWIMMER_M": "swimmer_m.png", "SWIMMER_F": "swimmer_f.png", "BURGLAR": "burglar.png",
           "PKMN_BREEDER": "pokefan_f.png", "TWINS": "twins.png", "CRUSH_KIN": "battle_girl.png", "COOL_COUPLE": "acetrainer_m.png",
           "YOUNG_COUPLE": "pt_young_couple.png", "SIS_AND_BRO": "pt_sis_and_bro.png", "BIKER": "biker.png", "CUE_BALL": "cueball.png",
           "HIKER": "hiker.png", "CRUSH_GIRL": "battle_girl.png", "BLACK_BELT": "blackbelt.png", "PICNICKER": "picnicker.png",
           "AROMA_LADY": "pt_aroma_lady.png", "COOLTRAINER_F": "acetrainer_f.png", "COOLTRAINER_M": "acetrainer_m.png",
           "FISHERMAN": "fisherman.png", "GENTLEMAN": "gentleman.png", "BEAUTY": "beauty.png", "LASS": "lass.png",
           "ENGINEER": "engineer.png", "ROCKER": "rocker.png", "SCIENTIST": "scientist.png", "TUBER": "tuber_f.png",
           "LADY": "lady.png", "PKMN_RANGER_F": "ranger_f.png", "PKMN_RANGER_M": "ranger_m.png", "PSYCHIC_M": "psychic_m.png",
           "PSYCHIC_F": "psychic_f.png", "SUPER_NERD": "supernerd.png"}
_DATA = None


def data():
    global _DATA
    if _DATA is None:
        _DATA = json.load(open(os.path.join("assets", "trainer_tower.json"), encoding="utf-8"))
    return _DATA


def climb(story):
    """The climb you're signed up for now (None: none)."""
    flags = story.story_flags
    if not flags.get("tt_on"):
        return None
    return next((c for c in CLIMBS if flags.get(f"tt_climb_{c}")), "SINGLE" if flags.get("tt_climb_SINGLE_on") else None)


def floor_data(story, n):
    c = climb(story)
    if not c or not 1 <= n <= 8:
        return None
    return data()["floors"][data()["climbs"][c][n - 1]]


def _top_level(story):
    return max([int(getattr(p, "level", 1)) for p in story.player_team if p and not getattr(p, "is_egg", False)] or [5])


def _able(story):
    return [p for p in story.player_team if p and not getattr(p, "is_egg", False) and getattr(p, "current_hp", 0) > 0]


def _clear_run(story):
    for c in CLIMBS:
        story.story_flags.pop(f"tt_climb_{c}", None)
    story.story_flags.pop("tt_climb_SINGLE_on", None)
    for k in [k for k in story.story_flags if k.startswith(("tt_floor_", "tt_ko_", "tt_here_"))]:
        story.story_flags.pop(k, None)
    story.story_flags.pop("tt_on", None)


def _to_lobby(game, lines):
    from src.states.overworld import AreaTransitionState
    game.arrive_floor = (AREA, 0, list(LOBBY_SPOT))
    game.change_state(AreaTransitionState(game, AREA, initial_message=list(lines)))


def event(state, ev, lines, show):
    kind = ev.get("tt")
    if kind == "desk":
        return _desk(state, show)
    if kind == "trainer":
        return _trainer(state, ev, show)
    if kind == "owner":
        return _owner(state, show)
    show(lines or ["..."])


# ---------------------------------------------------------------- the receptionist
def _desk(state, show):
    from src.states.systems.pick_list import PickListState
    game = state.game
    story = game.story_manager
    if story.story_flags.get("tt_on"):
        def quit_(yes):
            game.change_state(state)
            if yes:
                from src.ui import challenge_clock
                challenge_clock.stop(story)
                _clear_run(story)
                show(["Receptionist: Your challenge has been cancelled. Please come again!"])
            else:
                show(["Receptionist: Good luck! The owner is waiting on the roof."])
        state_say(state, ["Receptionist: You're in the middle of a challenge. Would you like to give it up?"],
                  lambda: game.change_state(PickListState(game, state, "GIVE UP THE CHALLENGE?", [("Yes, give up", True), ("No", False)], quit_)))
        return

    def picked(c):
        game.change_state(state)
        if c is None:
            show(["Receptionist: Please come again!"])
            return
        if c == "INFO":
            show(["Receptionist: The Trainer Tower has eight floors, with Trainers waiting on each one.",
                  "Beat a floor's Trainers and the stairs up open. Lose, and your challenge ends.",
                  "Their Pokemon will be as strong as your strongest. Climb to the roof as fast as you can!",
                  "Single Battle, Double Battle, Knockout, or Mixed: which will you take on?"])
            return
        if c in ("DOUBLE", "MIXED") and len(_able(story)) < 2:
            show(["Receptionist: I'm sorry, you need at least two Pokemon that can battle for that challenge."])
            return
        from src.ui import challenge_clock
        _clear_run(story)
        story.story_flags["tt_on"] = True
        if c == "SINGLE":
            story.story_flags["tt_climb_SINGLE_on"] = True
        else:
            story.story_flags[f"tt_climb_{c}"] = True
        for nm in on_climb(c):   # (who stands in the tower on this climb: their options' "condition" flag)
            story.story_flags["tt_here_" + nm.strip().replace(" ", "_")] = True
        challenge_clock.start(story, "TRAINER TOWER")
        _to_lobby(game, [f"Receptionist: {WORDS[c]}! The clock is running. Please go up the stairs, and good luck!"])
    state_say(state, ["Receptionist: Welcome to the Trainer Tower! Trainers from all over are waiting, up to the eighth floor.",
                      "Would you like to challenge them?"],
              lambda: game.change_state(PickListState(game, state, "WHICH CHALLENGE?",
                                                      [(WORDS[c], c) for c in CLIMBS] + [("What's this?", "INFO")], picked)))


def state_say(state, lines, then):
    say = getattr(state, "show_message", None) or getattr(state, "say", None) or getattr(state, "show_dialogue", None)
    try:
        say(lines, callback=then)
    except TypeError:
        say(lines, then=then)


# ---------------------------------------------------------------- the floors' trainers
def _floor_here(state):
    return int(getattr(getattr(state, "run", None), "index", 0) or 0)


def _trainer(state, ev, show):
    game = state.game
    story = game.story_manager
    n = _floor_here(state)
    f = floor_data(story, n)
    if not f:
        show(["..."])
        return
    kind = f["type"]
    who = str(ev.get("name") or ev.get("text") or "").strip()
    if kind == "KNOCKOUT":
        k = next((i for i, t in enumerate(f["trainers"]) if t["name"] == who), 0)
        done = story.story_flags.get(f"tt_ko_{n}_{k}")
    else:
        k = 0
        done = story.story_flags.get(f"tt_floor_{n}")
    t = f["trainers"][k]
    if done:
        show([t.get("after") or "..."])
        return
    if kind == "DOUBLE" and len(_able(story)) < 2:
        show(["You need two Pokemon that can battle for a Double Battle!"])
        return
    game.change_state(_battle(game, n, f, k))


def _team(game, mons, level):
    from src.pokemon.data import Pokemon
    from src.world import levels
    team = []
    for m in mons:
        p = Pokemon(game.loader.fetch_specific(int(m["id"])), game.assets, size_mult=3.125)
        team.append(p)
    levels.set_team(team, [level] * len(team), exact=True)
    for p, m in zip(team, mons):
        if m.get("moves"):
            p.preset_moves = list(m["moves"])
            p.moves = []
        if m.get("item"):
            p.held_item = m["item"]
        if m.get("nature") and hasattr(p, "nature"):
            p.nature = m["nature"]
    return team


def _battle(game, n, f, k):
    from src.states.battle import TrainerBattleState, TrainerIntroState
    from src.states.battle_double import battle_options
    from src.states.overworld.common import _trainer_sprite
    story = game.story_manager
    d = data()
    kind = f["type"]
    pick = d["pick"][kind][n - 1]
    lv = _top_level(story)
    if kind == "SINGLE":
        t = f["trainers"][0]
        mons = [t["mons"][i] for i in pick]
        name = t["name"]
    elif kind == "DOUBLE":
        t = f["trainers"][0]
        mons = [f["trainers"][0]["mons"][pick[0]], f["trainers"][1]["mons"][pick[1]]]
        name = t["name"]
    else:
        t = f["trainers"][k]
        mons = [t["mons"][pick[k]]]
        name = t["name"]
    team = _team(game, mons, lv)
    from src.pokemon import moves as _mv
    for p in team:   # (their own moves now: the preset set)
        if hasattr(_mv, "ensure_moves"):
            _mv.ensure_moves(game, p)
    info = {"double": kind == "DOUBLE"}
    sprite = _trainer_sprite(game, SPRITES.get(t.get("fr_class"), "youngster.png"))
    battle = TrainerBattleState(game, team, trainer_sprite=sprite, trainer_class=t.get("class", "TRAINER"), trainer_name=name,
                                custom_dialogue={"player_won": [t.get("lose") or "..."], "player_lost": [t.get("win") or "..."]},
                                rewards={}, battle_type="event", is_boss_battle=False, area_name=AREA, victory_flag=None,
                                options=battle_options(info))
    battle.facility = {"world": "trainer_tower", "floor": n, "kind": kind, "k": k}
    return TrainerIntroState(game, sprite, [t.get("before") or "..."], battle)


def after_battle(game, info, won):
    story = game.story_manager
    n, kind, k = int(info.get("floor", 0)), info.get("kind"), int(info.get("k", 0))
    if not won:
        from src.ui import challenge_clock
        challenge_clock.stop(story)
        _clear_run(story)
        return lambda: _to_lobby(game, ["Receptionist: Too bad! Your Pokemon have been healed. Please come back and try again!"])
    if kind == "KNOCKOUT":
        story.story_flags[f"tt_ko_{n}_{k}"] = True
        if all(story.story_flags.get(f"tt_ko_{n}_{i}") for i in range(3)):
            story.story_flags[f"tt_floor_{n}"] = True
            return ["The stairs up are open!"]
        left = 3 - sum(1 for i in range(3) if story.story_flags.get(f"tt_ko_{n}_{i}"))
        return [f"{left} more Trainer{'s' if left > 1 else ''} to beat on this floor!"]
    story.story_flags[f"tt_floor_{n}"] = True
    return ["The stairs up are open!"]


# ---------------------------------------------------------------- the owner on the roof
def _owner(state, show):
    from src.ui import challenge_clock
    game = state.game
    story = game.story_manager
    c = climb(story)
    if not c or not story.story_flags.get("tt_floor_8"):
        best = {x: story.story_flags.get(f"tt_best_{x}") for x in CLIMBS}
        rec = [f"{WORDS[x]}: {challenge_clock.text(v)}" for x, v in best.items() if v]
        show(["Owner: I'm the owner of the Trainer Tower. I'd like to see you climb it in record time!"]
             + (["Your best times: " + ", ".join(rec) + "."] if rec else []))
        return
    t = challenge_clock.stop(story)
    out = ["Owner: I'm the owner of the Trainer Tower. You battled perfectly to get here!",
           f"Your time: {challenge_clock.text(t)}."]
    prize = {"UP_GRADE": "UPGRADE"}.get(data()["prizes"].get(c), data()["prizes"].get(c))   # (FireRed's item names: ours)
    from src.states.systems import has_national_dex
    if prize == "UPGRADE" and not story.story_flags.get(f"tt_prize_{c}") and not has_national_dex(story):
        # (Jordan 11-23: no Up-Grade in Kanto before the National Pokedex - a Kanto-first player gets no Porygon2 there)
        out += ["I have a prize for this climb, but it's a part made for Pokemon from far away.",
                "Come back with the National Pokedex and climb it again, and it's yours!"]
        prize = None
    if prize and not story.story_flags.get(f"tt_prize_{c}"):
        story.story_flags[f"tt_prize_{c}"] = True
        story.add_item(prize, 1)
        from src.pokemon import forms
        out += ["This is for you.", f"{getattr(game, 'player_name', 'You')} received the {forms.item_label(prize).upper()}!"]
    best = story.story_flags.get(f"tt_best_{c}")
    if best is None or t < float(best):
        story.story_flags[f"tt_best_{c}"] = round(t, 2)
        out.append("You've done it in record time!")
    else:
        out.append(f"You took your sweet time getting here. The record is {challenge_clock.text(best)}.")
    out.append("I'd like to see you do it in a better time next time. The lift goes down to the lobby.")
    _clear_run(story)
    story.story_flags[f"tt_beaten_{c}"] = True
    show(out)


def on_climb(c):
    """The figures standing in the tower on a climb (a Double pair as its two people)."""
    out = []
    for fl in data()["climbs"][c]:
        f = data()["floors"][fl]
        for t in f["trainers"]:
            parts = [x.strip() for x in t["name"].replace("&", " & ").split("&")] if f["type"] == "DOUBLE" else [t["name"]]
            out += parts if len(parts) in (1, 2) else [t["name"]]
    return out


def condition(story, arg):
    """"world:trainer_tower:on:<name>": that trainer stands in the tower now (on the climb you're signed up for)."""
    what, _, name = str(arg).partition(":")
    if what == "on":
        c = climb(story)
        if not c:
            return False
        for fl in data()["climbs"][c]:
            f = data()["floors"][fl]
            for t in f["trainers"]:
                if t["name"] == name or (f["type"] == "DOUBLE" and name in [x.strip() for x in t["name"].replace("&", " & ").split("&")]):
                    return True
        return False
    return False
