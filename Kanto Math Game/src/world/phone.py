"""The phone (HGSS's Pokegear; Jordan 11-15: "I like the idea of the phone for rematches since the phone comes back in later
generations"). Built region-blind: a region's phone item (PHONE_ITEM) and its trainers' "phone" data are all it needs.

A trainer with "phone" in its area's trainer_pool ({"tiers": [{"team", "levels", "gift"?}...], "call": [lines]}, written for
Johto by kanto_handoff/johto_map_tools/jphone.py from SoulSilver's own rematch teams):
  - beaten while you carry the region's phone -> asks for your number: registered (register_after_win)
  - its next team is ready when the level cap has reached that team's lowest level (tier_ready): it rings you the next time
    you arrive somewhere (ring), once a team
  - met again (route trainers come back the next day): it battles with its best ready team (rematch_info); a tier's "gift"
    comes with the win, once.
Saved in story_flags: "phone_contacts" {"AREA|name": tier rung}, "phone_gift_AREA|name|n"."""

PHONE_ITEM = {"JOHTO": "POKEGEAR", "KANTO": "POKEGEAR"}   # (later regions: the Xtransceiver, the Rotom Phone... add them here)
RING_CHANCE = 1.0   # (one call an arrival when a team is ready: HGSS rings often)


def has_phone(story):
    item = PHONE_ITEM.get(str(story.get_current_region()).upper())
    return bool(item) and story.inventory.get(item, 0) > 0


def contacts(story):
    return story.story_flags.setdefault("phone_contacts", {})


def _key(area, info):
    return f"{area}|{info.get('name')}"


def tier_ready(game, info):
    """The best rematch team ready now (index), or None: a team is ready once the level cap reaches its lowest level."""
    from src.world import levels
    tiers = (info.get("phone") or {}).get("tiers") or []
    story = game.story_manager
    cap = levels.story_level_cap(story) if levels.cap_mode(story) == "STORY" else 100
    ready = [i for i, t in enumerate(tiers) if min(t.get("levels") or [0]) <= cap]
    return ready[-1] if ready else None


def register_after_win(game, area, info):
    """Lines to show after beating a phone trainer for the first time with a phone in your bag (else [])."""
    story = game.story_manager
    if not info.get("phone") or not has_phone(story):
        return []
    c = contacts(story)
    k = _key(area, info)
    if k in c:
        return []
    c[k] = -1
    name = str(info.get("name", "")).split(" ")[-1]
    return [f"{name}: You're good! Can I have your number? I'll call you when my team's stronger.",
            f"{info.get('name')} was registered in the phone!"]


def rematch_info(game, area, index, info):
    """A registered phone trainer met again: its info with the best ready team (and that tier's gift, if not yet given).
    Else the info as it was."""
    story = game.story_manager
    if not info.get("phone") or _key(area, info) not in contacts(story) or not story.is_trainer_defeated(area, index):
        return info
    t = tier_ready(game, info)
    if t is None:
        return info
    tier = info["phone"]["tiers"][t]
    out = dict(info, team=list(tier["team"]), levels=list(tier["levels"]), _phone_tier=t)
    gift = tier.get("gift")
    if gift and not story.story_flags.get(f"phone_gift_{_key(area, info)}|{t}"):
        out["rewards"] = dict(info.get("rewards") or {}, **gift)
        out["_phone_gift"] = f"phone_gift_{_key(area, info)}|{t}"
    return out


# Calls the story makes (HGSS): (region, conditions all true, flag set once it's rung, lines - ours)
STORY_CALLS = [
    ("JOHTO", ["met_mr_pokemon", "!defeated_rival_cherrygrove"], "johto_call_elm_panic",
     ["Ring, ring! It's Professor Elm!", "Professor Elm: H-hello? It's terrible! Something awful has happened at the Lab!",
      "Professor Elm: Please, come back right away!"]),
    ("JOHTO", ["badge:ZEPHYR", "elm_received_egg", "!got_togepi_egg"], "johto_call_elm_egg",
     ["Ring, ring! It's Professor Elm!", "Professor Elm: You won the Zephyr Badge? Wonderful!",
      "Professor Elm: About that Egg... I've sent my aide to the Pokemon Center in Violet City with it. Go and see!"]),
]


def _cond(story, c):
    if c.startswith("!"):
        return not _cond(story, c[1:])
    if c.startswith("badge:"):
        return c[6:] in story.badges.get(str(story.get_current_region()).upper(), [])
    return bool(story.story_flags.get(c))


def ring(game, area_key):
    """Arriving somewhere: a story call that's due, else a registered trainer whose next team is ready calls (once a
    team). Lines, or []."""
    story = game.story_manager
    if not has_phone(story):
        return []
    for region, conds, flag, lines in STORY_CALLS:
        if region == str(story.get_current_region()).upper() and not story.story_flags.get(flag) and all(_cond(story, c) for c in conds):
            story.story_flags[flag] = True
            return list(lines)
    c = contacts(story)
    region = str(story.get_current_region()).upper()
    data = game.loader.area_data.get("STORY_PROGRESSION", {}) if isinstance(getattr(game.loader, "area_data", None), dict) else {}
    for k, rung in list(c.items()):
        area, name = k.split("|", 1)
        a = data.get(area) or {}
        if str(a.get("region", region)).upper() != region:
            continue
        info = next((t for t in a.get("trainer_pool", []) if isinstance(t, dict) and t.get("name") == name), None)
        if not info or not info.get("phone"):
            continue
        t = tier_ready(game, info)
        if t is not None and t > rung:
            c[k] = t
            call = info["phone"].get("call") or [f"{name}: Let's battle again!"]
            return ["Ring, ring! Your phone is ringing!"] + list(call)
    return []


# Who's in the phone from the start (HGSS: Mom gives you the Pokegear with her number in it; Elm adds his on Route 29). Our words.
PEOPLE = {"JOHTO": [("Mom", "New Bark Town", "Mom: Are you eating well? Don't forget to rest your Pokemon at a Pokemon Center!", None),
                    ("Prof. Elm", "New Bark Town", "Prof. Elm: Hello! How's your Pokedex coming along? Every Pokemon you meet helps my research!", "johto_elm_number"),
                    ("Prof. Oak", "Kanto", "Prof. Oak: Ah, hello! Catch lots of Pokemon. A full Pokedex is a fine thing!", "received_pokedex_johto")]}


def book(game):
    """[(name, area, line)] for the phone screen: who you can call and what they say now."""
    story = game.story_manager
    data = game.loader.area_data.get("STORY_PROGRESSION", {})
    out = [(n, w, l) for n, w, l, f in PEOPLE.get(str(story.get_current_region()).upper(), []) if not f or story.story_flags.get(f)] if has_phone(story) else []
    for k in contacts(story):
        area, name = k.split("|", 1)
        a = data.get(area) or {}
        info = next((t for t in a.get("trainer_pool", []) if isinstance(t, dict) and t.get("name") == name), None) or {}
        where = a.get("route_name") or area.replace("_", " ").title()
        t = tier_ready(game, info) if info.get("phone") else None
        line = (f"{name.split(' ')[-1]}: I'm ready for a rematch! Come find me on {where}." if t is not None
                else f"{name.split(' ')[-1]}: I'm still training on {where}. I'll call when I'm stronger!")
        out.append((name, where, line))
    return out
