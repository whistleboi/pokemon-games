"""Mega Evolution on the map (Jordan, 11-06/07, as in Legends: Z-A): the map's MEGA button Mega Evolves the
Pokemon following you for SECONDS of walking (it stays a Mega in the party menu, and goes into battles that
way, classic or overworld: that's the battle's one Mega), then it goes back and the Key Stone needs COOLDOWN
seconds before the next one. The clock runs on every screen but battles (Game.run ticks it). A Mega made in
a battle (its own MEGA button) still lasts that battle.

game.rt_mega = {"mon": the Pokemon, "form": its form, "left": frames as a Mega, "cool": frames to wait}"""
from src.config import FPS
from src.pokemon import forms

SECONDS = 60
COOLDOWN = 30


def state(game):
    return getattr(game, "rt_mega", None) or {}


def active(game):
    m = state(game)
    return m.get("left", 0) > 0 and forms.is_changed(m["mon"])


def cooling(game):
    return not active(game) and state(game).get("cool", 0) > 0


def start(game, mon, form):
    lines = forms.apply_form(game.assets, mon, form)
    game.rt_mega = {"mon": mon, "form": form, "left": SECONDS * FPS, "cool": 0}
    return lines


def _end(game, say=True):
    m = state(game)
    mon = m.get("mon")
    if mon is not None and forms.is_changed(mon):
        forms.revert_form(mon)
        st = getattr(game, "current_state", None)
        if say and hasattr(st, "flash"):
            st.flash(f"{mon.display_name.upper()} went back to normal.", 90)
    game.rt_mega = {"mon": mon, "form": None, "left": 0, "cool": COOLDOWN * FPS}


def tick(game):
    """Once a frame (any screen)."""
    m = getattr(game, "rt_mega", None)
    if not m:
        return
    from src.states.battle import TrainerBattleState
    if isinstance(getattr(game, "current_state", None), TrainerBattleState):
        return  # (the minute waits while you battle)
    if m.get("left", 0) > 0:
        if not forms.is_changed(m["mon"]):  # (a traditional battle's end put it back)
            return _end(game, say=False)
        m["left"] -= 1
        if m["left"] <= 0:
            _end(game)
    elif m.get("cool", 0) > 0:
        m["cool"] -= 1
        if m["cool"] <= 0:
            game.rt_mega = None


def keep_through(game, fn):
    """Run fn (a battle's exit_battle, which puts every form back) and keep the real-time Mega on."""
    m = state(game)
    keep = active(game) and m.get("form")
    fn()
    if keep and not forms.is_changed(m["mon"]):
        forms.apply_form(game.assets, m["mon"], m["form"])
