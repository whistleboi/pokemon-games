"""Pastoria City's own conditions (Sinnoh S4, 11-24).

"world:pastoria:combee_pair": a male and a female Combee are both with you - Platinum's boy in the house north of the
Mart (C06R0301) wants to see them together, and gives a Macho Brace (Diamond and Pearl asked for Burmy's three cloaks)."""
COMBEE = 415


def condition(story, arg):
    if str(arg) == "combee_pair":
        seen = {getattr(p, "gender", None) for p in story.player_team if p and getattr(p, "id", None) == COMBEE}
        return {"M", "F"} <= seen
    return False
