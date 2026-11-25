"""Sinnoh's gifts that need a rule (Pokemon Platinum, 11-25, Sinnoh S8; placed by kanto_handoff/sinnoh_map_tools/sfolk.py's
S8 gifts block and s_s8_gifts.py):
- Julia in Sunyshore: tell her about your travels once a day and your lead Pokemon gets that weekday's Ribbon (Platinum's:
  Monday Alert, Tuesday Shock, Wednesday Downcast, Thursday Careless, Friday Relax, Saturday Snooze, Sunday Smile).
- The man on Route 221 who sees a number each day: show him a Pokemon at that level for a Black Belt, an Expert Belt or a
  Focus Sash (Platinum's three), once a day.
- Dr. Footstep on Route 213: a lead Pokemon that loves you as much as it can (friendship 255) gets the Footprint Ribbon.
Events {"world": "sinnoh_gifts", "julia" | "level_man" | "footstep": true}."""
import datetime
import hashlib
import random

WEEKDAY = ["ALERT", "SHOCK", "DOWNCAST", "CARELESS", "RELAX", "SNOOZE", "SMILE"]
BELTS = ["BLACK_BELT", "EXPERT_BELT", "FOCUS_SASH"]


def _lead(story):
    return next((p for p in story.player_team if p and not getattr(p, "is_egg", False)), None)


def _label(rib):
    from src.pokemon.contest import ribbon_label
    return ribbon_label(rib)


def todays_level(day=None):
    d = (day or datetime.date.today()).isoformat()
    return int(hashlib.md5(f"route221:{d}".encode()).hexdigest(), 16) % 100 + 1


def event(state_, ev, lines, show):
    story = state_.game.story_manager
    flags = story.story_flags
    today = datetime.date.today()
    lead = _lead(story)
    if ev.get("julia"):
        key = "sinnoh_julia_day"
        if flags.get(key) == today.isoformat():
            show(["Julia: Thank you for today's story. Come back tomorrow and tell me another!"])
            return
        rib = WEEKDAY[today.weekday()]
        if lead is None:
            show(lines or ["Julia: Hello there."])
            return
        flags[key] = today.isoformat()
        if rib in (getattr(lead, "ribbons", None) or []):
            show((lines or []) + ["Julia: What a wonderful story. Thank you, it made my day."])
            return
        lead.ribbons.append(rib)
        show((lines or []) + ["Julia: Thank you! Please give this to your Pokemon.", f"{lead.display_name} received the {_label(rib)}!"])
        return
    if ev.get("level_man"):
        key = "sinnoh_route221_level_day"
        n = todays_level(today)
        if flags.get(key) == today.isoformat():
            show([f"...Today's number was {n}. Come back tomorrow, when I'll see another!"])
            return
        hit = next((p for p in story.player_team if p and not getattr(p, "is_egg", False) and int(getattr(p, "level", 0)) == n), None)
        if hit is None:
            show([f"...I see it! Today's number is {n}! Show me a Pokemon that's Lv. {n} and I'll reward you."])
            return
        it = random.choice(BELTS)
        flags[key] = today.isoformat()
        story.inventory[it] = story.inventory.get(it, 0) + 1
        show([f"...Today's number is {n}! And your {hit.display_name} is Lv. {n}! Well, I'll be!",
              f"You received a {it.replace('_', ' ').title()}!"])
        return
    if ev.get("effort"):   # (Sunyshore Market's lady: a lead Pokemon at the full 510 effort points gets the Effort Ribbon, once)
        evs = sum(int(v or 0) for v in (getattr(lead, "evs", None) or {}).values()) if lead is not None else 0
        if lead is not None and evs >= 510 and "EFFORT" not in (getattr(lead, "ribbons", None) or []):
            lead.ribbons.append("EFFORT")
            show((lines or []) + [f"Oh? Your {lead.display_name}... It's worked so very hard, hasn't it? This is for all that effort.",
                                  f"{lead.display_name} received the {_label('EFFORT')}!"])
            return
        show(lines or ["..."])
        return
    if ev.get("footstep"):
        if lead is not None and int(getattr(lead, "friendship", 0) or 0) >= 255 and "FOOTPRINT" not in (getattr(lead, "ribbons", None) or []):
            lead.ribbons.append("FOOTPRINT")
            show((lines or []) + ["Dr. Footstep: Such love in every step! It adores you completely!",
                                  f"{lead.display_name} received the {_label('FOOTPRINT')}!"])
            return
        show(lines or ["..."])
        return
    show(lines or ["..."])
