"""Shadow Pokemon (Orre: Colosseum and XD; Jordan's answers 11-20, kanto_handoff/orre_check/DECISIONS.md 6-10).

A Shadow Pokemon is one of the "shadow" forms in Orre's FORM_MAP (an id like 9406 = Shadow Makuhita; Jordan's own
Shadow Pokemon are in there too and are kept as they are). This module holds their rules, XD's core:

- Snagging: with the SNAG_MACHINE, a Ball can be thrown at a trainer's Shadow Pokemon mid-battle (src/states/
  battle_shadow.py); at anything else the trainer blocks it.
- The Heart Gauge (mon.shadow = {"gauge", "max", "hidden", "seen"}): it opens (goes down) as the Pokemon battles,
  walks with you, stays at the Day Care, is calmed out of Hyper Mode, or is given a cologne. Five bars; the gauge's max
  comes from the disc's own Shadow data (SHADOW_DATA in orre_area_data.json) or, failing that, from its level.
- Moves: a snagged Pokemon knows SHADOW-RUSH and its own moves are hidden ("????"); one is revealed for each bar the
  gauge drops, all four by the last bar (XD).
- Hyper Mode: in battle a Shadow Pokemon may lose control (more often the fuller its gauge); then it may ignore what you
  ask and use a Shadow move. CALL (in place of RUN) calms it, which opens the gauge a little too.
- At 0 the heart is open: it can be purified (the Relic Stone, the Purify Chamber: StoryManager.purify_shadow).
- The dark aura (the Aura Reader, Q10) shows only once Rui (or the Aura Reader) is with you: flag "aura_reader".
Stored Exp. (XD) is not used: Shadow Pokemon level as before, so Jordan's Shadow evolutions still happen (asked 11-20).
"""
import math
import random

SHADOW_RUSH = "SHADOW-RUSH"
BARS = 5
SNAG_MACHINE = "SNAG_MACHINE"
AURA_FLAG = "aura_reader"

# How much of the gauge each thing opens (shares of its max). XD varies these by nature; ours are one size.
OPEN_BATTLE = 0.05      # each battle it takes part in
OPEN_STEPS = (64, 0.01)  # every 64 steps in the party
OPEN_CALL = 0.03        # calmed out of Hyper Mode by a call
OPEN_DAYCARE = (100, 0.02)
COLOGNES = {"JOY_SCENT": 0.10, "EXCITE_SCENT": 0.15, "VIVID_SCENT": 0.25, "TIME_FLUTE": 1.0}
HYPER_CHANCE = 0.12      # at a full gauge, per action (less as it opens)


def _form(game, mon_or_id):
    pid = getattr(mon_or_id, "id", mon_or_id)
    return (game.loader.area_data.get("FORM_MAP", {}).get(str(pid)) or {})


def is_shadow_id(game, pid):
    return _form(game, pid).get("form") == "shadow"


def is_shadow(game, mon):
    return mon is not None and is_shadow_id(game, mon.id)


def base_id(game, mon):
    """The ordinary species a Shadow form purifies into."""
    m = _form(game, mon)
    return int(m.get("id") or mon.id)


def data_for(game, mon):
    """The disc's Shadow data for this form (heart gauge, catch rate, its Shadow moves), or {}."""
    return (game.loader.area_data.get("SHADOW_DATA") or {}).get(str(getattr(mon, "id", mon))) or {}


def can_snag(game, mon):
    story = game.story_manager
    return is_shadow(game, mon) and story.inventory.get(SNAG_MACHINE, 0) > 0


def aura_visible(game):
    """Shadow Pokemon are marked (their dark aura) once Rui or the Aura Reader is with you (Q10)."""
    flags = game.story_manager.story_flags
    return (bool(flags.get(AURA_FLAG) or flags.get("orre_rui_joined") or flags.get("got_snag_machine"))   # (older saves: met Rui the old way)
            or game.story_manager.get_current_region() != "ORRE")


def snag_flag(game, mon):
    """The story flag a snag sets: the shadow_pool entry for this form, else snagged_<name>."""
    prog = game.loader.area_data.get("STORY_PROGRESSION", {})
    for a in prog.values():
        for s in (a.get("shadow_pool") or []) if isinstance(a, dict) else []:
            if int(s.get("id", 0)) == int(mon.id):
                return s.get("flag")
    name = (_form(game, mon).get("name") or str(mon.id)).lower().replace(" ", "_").replace(".", "")
    return f"snagged_{name}"


# ------------------------------------------------------------------ the heart gauge
def make_shadow(game, mon):
    """A Shadow Pokemon just snagged: its gauge full, its moves hidden behind SHADOW-RUSH."""
    if getattr(mon, "shadow", None):
        return mon
    d = data_for(game, mon)
    full = int(d.get("heart") or max(1000, 120 * int(mon.level)))
    if not getattr(mon, "moves", None):   # (a Pokemon made for a battle gets its moves when it first fights)
        from src.pokemon import moves as movelib
        movelib.ensure_moves(game, mon)
    moves = [m for m in (getattr(mon, "moves", None) or []) if m != SHADOW_RUSH]
    mon.shadow = {"gauge": full, "max": full, "hidden": moves[:4], "hyper": False}
    _refresh_moves(mon)
    return mon


def bars(mon):
    s = getattr(mon, "shadow", None)
    if not s:
        return 0
    return int(math.ceil(BARS * max(0, s["gauge"]) / max(1, s["max"])))


def is_open(mon):
    s = getattr(mon, "shadow", None)
    return bool(s) and s["gauge"] <= 0


def _refresh_moves(mon):
    """SHADOW-RUSH plus the hidden moves this gauge has revealed (one per bar gone, all at the last bar)."""
    s = mon.shadow
    shown = max(0, min(len(s["hidden"]), BARS - bars(mon) if bars(mon) > 1 else len(s["hidden"])))
    mon.moves = [SHADOW_RUSH] + s["hidden"][:shown][:3]


def open_heart(game, mon, share, why=""):
    """Opens the gauge by a share of its max. Returns lines to show (a move remembered, the heart opened)."""
    s = getattr(mon, "shadow", None)
    if not s or s["gauge"] <= 0:
        return []
    before, shown = bars(mon), len(mon.moves)
    s["gauge"] = max(0, s["gauge"] - max(1, int(s["max"] * share)))
    lines = []
    if bars(mon) != before:
        _refresh_moves(mon)
        if len(mon.moves) > shown:
            lines.append(f"{mon.display_name.upper()} remembered {mon.moves[-1].replace('-', ' ')}!")
    if s["gauge"] <= 0:
        lines.append(f"{mon.display_name.upper()}'s heart is open! It can be purified now.")
    return lines


def after_battle(game, team, fought):
    """Every Shadow Pokemon that took part in a battle opens a little."""
    lines = []
    for mon in team:
        if mon is not None and getattr(mon, "shadow", None) and id(mon) in {id(m) for m in fought}:
            mon.shadow["hyper"] = False
            lines += open_heart(game, mon, OPEN_BATTLE)
    return lines


def walked(game, steps=1):
    """Steps with Shadow Pokemon in the party (called from the maps' step counter)."""
    story = game.story_manager
    n = story.story_flags.get("_shadow_steps", 0) + steps
    every, share = OPEN_STEPS
    lines = []
    while n >= every:
        n -= every
        for mon in story.player_team:
            if mon is not None and getattr(mon, "shadow", None):
                lines += open_heart(game, mon, share)
    story.story_flags["_shadow_steps"] = n
    return lines


def cologne(game, mon, item):
    if item not in COLOGNES or not getattr(mon, "shadow", None):
        return []
    return [f"{mon.display_name.upper()} enjoyed the scent!"] + open_heart(game, mon, COLOGNES[item])


# ------------------------------------------------------------------ Hyper Mode (in battle)
def maybe_hyper(game, mon):
    """At its action: does it lose control? (Lines, or [].)"""
    s = getattr(mon, "shadow", None)
    if not s or s["hyper"] or s["gauge"] <= 0:
        return []
    if random.random() < HYPER_CHANCE * s["gauge"] / max(1, s["max"]):
        s["hyper"] = True
        return [f"{mon.display_name.upper()} went into Hyper Mode!"]
    return []


def hyper_override(mon):
    """In Hyper Mode, half the time it ignores you: the move it uses instead (SHADOW-RUSH), else None."""
    s = getattr(mon, "shadow", None)
    if s and s["hyper"] and random.random() < 0.5:
        return SHADOW_RUSH
    return None


def call(game, mon):
    """CALL: calms a Pokemon in Hyper Mode (and opens its heart a little); else it just perks up."""
    name = mon.display_name.upper()
    s = getattr(mon, "shadow", None)
    if s and s["hyper"]:
        s["hyper"] = False
        return [f"{game.player_name} called out to {name}!", f"{name} came to its senses!"] + open_heart(game, mon, OPEN_CALL)
    return [f"{game.player_name} called out to {name}!", f"{name} is paying attention!"]


def damage_mult(game, attacker, defender, move_type):
    """Shadow moves (XD): twice as strong on ordinary Pokemon, half on Shadow ones."""
    if move_type != "SHADOW":
        return 1.0
    return 0.5 if is_shadow(game, defender) else 2.0


# ------------------------------------------------------------------ saving
def to_record(mon):
    s = getattr(mon, "shadow", None)
    return dict(s) if s else None


def from_record(mon, rec):
    if rec:
        mon.shadow = {"gauge": int(rec.get("gauge", 0)), "max": int(rec.get("max", 1)),
                      "hidden": list(rec.get("hidden") or []), "hyper": False}


def purified(mon):
    """Purified: the Shadow record goes, its own moves come back."""
    s = getattr(mon, "shadow", None)
    if s:
        mon.moves = list(s["hidden"]) or [m for m in mon.moves if m != SHADOW_RUSH]
        mon.shadow = None
    return mon


def receive_snagged(game, mon):
    """A snagged Pokemon joins you (party, or the PC when it's full). Returns the lines."""
    story = game.story_manager
    make_shadow(game, mon)
    mon.current_hp = max(1, mon.current_hp)
    mon.caught_region = story.get_current_region()
    mon.caught_level = mon.level
    mon.caught_ball = getattr(story, "selected_ball", None) or "POKE_BALL"
    flag = snag_flag(game, mon)
    if flag:
        story.story_flags[flag] = True
    story.catch_counts[str(mon.id)] = story.catch_counts.get(str(mon.id), 0) + 1
    name = mon.display_name.upper()
    lines = [f"Gotcha! {name} was snagged!"]
    if len([p for p in story.player_team if p]) < 6:
        story.player_team.append(mon)
    else:
        story.deposit_to_pc(mon)
        lines.append(f"{name} was sent to the PC.")
    try:
        game.data.add_pokemon(mon)
        game.update_save_data()
    except Exception:
        pass
    return lines
