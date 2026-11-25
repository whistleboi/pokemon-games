"""The Ribbon Syndicate in the Resort Area (Pokemon Platinum, 11-24, Sinnoh S7b; built by kanto_handoff/sinnoh_map_tools/
s_s7_resort.py; Jordan: "Build it as Platinum"): members only - ten kinds of Ribbon on the Pokemon in your party between
them (Platinum's rule); upstairs by the lift, the spa (a Pokemon grows friendlier, once a day: common.py's "salon"); on
1F the shop's Ribbons, sold to your lead Pokemon (Platinum's three: Gorgeous $10,000, Royal $100,000, Gorgeous Royal
$999,999).

Conditions ("world:ribbon_syndicate:<arg>"): "member". Event {"world": "ribbon_syndicate", "shop": true} (the clerk's
list) or {"buy": key}."""
from src.pokemon.contest import SPECIAL_RIBBONS

MEMBER = 10
SHOP = [("GORGEOUS", 10000), ("ROYAL", 100000), ("GORGEOUS_ROYAL", 999999)]


def _team(story):
    return [p for p in story.player_team if p and not getattr(p, "is_egg", False)]


def kinds(story):
    """The different Ribbons the Pokemon in your party have between them."""
    return {str(r) for p in _team(story) for r in (getattr(p, "ribbons", None) or [])}


def condition(story, arg):
    if arg == "member":
        return len(kinds(story)) >= MEMBER
    return False


def event(state_, ev, lines, show):
    story = state_.game.story_manager
    lead = next(iter(_team(story)), None)
    if ev.get("buy"):
        key = ev["buy"]
        price = dict(SHOP).get(key)
        if lead is None or price is None:
            show(["Clerk: Please come back with a Pokemon to wear it."])
            return
        if key in (getattr(lead, "ribbons", None) or []):
            show([f"Clerk: {lead.display_name} already wears the {SPECIAL_RIBBONS[key]}."])
            return
        if story.money < price:
            show([f"Clerk: I'm terribly sorry, but the {SPECIAL_RIBBONS[key]} is ${price:,}."])
            return
        story.money -= price
        lead.ribbons.append(key)
        show([f"You bought the {SPECIAL_RIBBONS[key]} for ${price:,}.", f"{lead.display_name} put on the {SPECIAL_RIBBONS[key]}!"])
        return
    if ev.get("shop"):
        if lead is None:
            show(lines or ["Clerk: Our Ribbons are for your Pokemon to wear."])
            return
        have = set(getattr(lead, "ribbons", None) or [])
        opts = [{"text": f"{SPECIAL_RIBBONS[k]} ${p:,}", "action": "EVENT", "event": {"world": "ribbon_syndicate", "buy": k}}
                for k, p in SHOP if k not in have]
        if not opts:
            show([f"Clerk: {lead.display_name} wears every Ribbon we offer. Splendid!"])
            return
        opts.append({"text": "No, thank you", "action": "EVENT", "event": {"lines": ["Clerk: Do come again."]}})
        ask = (lines or []) + [f"Clerk: Which Ribbon would you like for {lead.display_name}?"]
        say = getattr(state_, "show_message", None)
        if say is None or not hasattr(state_, "_create_hover_menu"):
            show(ask)
            return
        say(ask, callback=lambda: state_._create_hover_menu(opts, None))
        return
    show(lines or ["..."])
