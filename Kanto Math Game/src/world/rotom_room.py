"""Rotom's room in the Galactic Eterna Building (Pokemon Platinum, 11-24, Sinnoh S7b; built by kanto_handoff/sinnoh_map_tools/
s_s7_rotom.py): five appliances - a microwave, a washer, a fridge, a fan, a mower (Platinum's order: forms 1-5). Bring a
Rotom and it slips into the motor of the one you check: its form changes (src/pokemon/forms.py rotom_change: types, stats,
the form's own move). Checking the one it's already in brings it back out as normal Rotom.
Event {"world": "rotom_room", "form": "heat" | "wash" | "frost" | "fan" | "mow"}."""
from src.pokemon import forms

NAMES = {"heat": "microwave", "wash": "washing machine", "frost": "refrigerator", "fan": "electric fan", "mow": "lawn mower"}


def event(state_, ev, lines, show):
    game = state_.game
    story = game.story_manager
    form = ev.get("form")
    party = story.player_team
    slot = next((i for i, p in enumerate(party) if p and not getattr(p, "is_egg", False) and int(getattr(p, "id", 0) or 0) == forms.ROTOM), None)
    what = NAMES.get(form, "appliance")
    if slot is None:
        show([f"It's a {what}. There's a strange motor inside it.", "It looks as if something could slip right into it..."])
        return
    p = party[slot]
    now = story._pokemon_record(p).get("form") or "normal"
    to = "normal" if now == form else form
    out = forms.rotom_change(game, slot, to) or []
    head = [f"{p.display_name} emerged from the motor!"] if to == "normal" else [f"{p.display_name} slipped into the {what}'s motor!"]
    show(head + list(out))
