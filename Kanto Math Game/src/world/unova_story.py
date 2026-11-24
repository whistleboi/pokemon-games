"""Unova's own story conditions (11-23, batch 4a), through main's region hook: "world:unova_story:<arg>".

- "female_player" / "male_player": Black 2 / White 2 change some people by the player's character (Nimbasa's Subway
  partner is Rosa for a boy and Nate for a girl; the Ferris wheel's trainer). Our characters, by look."""

FEMALE = {"rosa", "hilda", "dawn", "leaf", "female", "may", "girls", "lyra", "kris", "serena", "selene", "gloria",
          "juliana", "lillie"}


def female(story):
    game = getattr(story, "game", None)
    return str(getattr(game, "player_character", "") or "").lower() in FEMALE


def condition(story, arg):
    """"female_player" / "male_player"; "not_today:<flag>": the flag is set, and not today (the day it was first seen
    set is kept as <flag>_day: the Ferris wheel's second visit is another day, as Black 2)."""
    if arg.startswith("not_today:"):
        import datetime
        flag = arg[10:]
        if not story.story_flags.get(flag):
            return False
        today = datetime.date.today().isoformat()
        day = story.story_flags.setdefault(flag + "_day", today)
        return day != today
    if arg.startswith("party_level:"):   # (a Pokemon with you at that level or more: Driftveil Market's Expert Belt man, 11-24)
        want = int(arg.split(":", 1)[1])
        return any(p and not getattr(p, "is_egg", False) and int(getattr(p, "level", 0) or 0) >= want for p in story.player_team)
    if arg == "female_player":
        return female(story)
    if arg == "male_player":
        return not female(story)
    return False


def _today_move(story, game):
    """The move the Luxury Suites lady asks to see today: one of your TMs' moves, the same all day (Black 2: she only asks
    for TM or HM moves you own)."""
    import datetime
    import json
    import os
    import random
    base = getattr(getattr(game, "assets", None), "assets_dir", None) or "assets"
    try:
        tms = json.load(open(os.path.join(base, "tms.json"), encoding="utf-8"))
    except Exception:
        return None
    owned = sorted(tms[k]["move"] for k, n in (story.inventory or {}).items() if k in tms and n)
    if not owned:
        return None
    return random.Random("move_lady@" + datetime.date.today().isoformat()).choice(owned)


TM_STEPS = (10, 20, 35, 50, 70, 95)   # (Black 2's TM fan in Mistralton: an HP Up at each, the last for all 95)


def _tm_count(story):
    return sum(1 for k, n in (story.inventory or {}).items() if str(k).startswith("TM") and str(k)[2:].isdigit() and n)


def _tm_lady(state, story, show):
    have = _tm_count(story)
    given = int(story.story_flags.get("b2_tm_lady_steps") or 0)
    due = sum(1 for s in TM_STEPS if have >= s)
    if given >= len(TM_STEPS):
        show(["You're a TM Master! Use lots of different moves and bring out your Pokemon's power!"])
        return
    if due <= given:
        show(["I'm very fussy about moves. Extra fussy about TMs! How many have you collected?",
              "Hmm... You have %d TMs! Collect a lot more and I'll give you something great!" % have])
        return
    story.story_flags["b2_tm_lady_steps"] = due
    story.inventory["HP_UP"] = story.inventory.get("HP_UP", 0) + (due - given)
    show(["Hmm... You have %d TMs!" % have,
          "Oh! I've never seen some of these before! As a reward, please take this!",
          "You received %s!" % ("an HP Up" if due - given == 1 else "%d HP Ups" % (due - given)),
          "There must be a lot more TMs! Collect even more and I'll give you another gift!"
          if due < len(TM_STEPS) else "You are a TM Master! Thank you very much!"])


def event(state, ev, lines, show):
    """{"toggle": flag}: flip a flag (the roller coaster's switches: each press changes a car's route).
    {"move_lady": true}: Driftveil Luxury Suites' lady: show her a Pokemon that knows today's move, a Heart Scale (once a day).
    {"runner": flag}: the thirsty runner on a bridge: a Fresh Water for his thanks (once)."""
    story = state.game.story_manager
    if ev.get("move_lady"):
        import datetime
        today = datetime.date.today().isoformat()
        if story.story_flags.get("b2_move_lady_day") == today:
            show(["I wonder what that move looks like when it's really used. I'm sure you use it beautifully!"])
            return
        mv = _today_move(story, state.game)
        if not mv:
            show(["Oh, a Trainer! Do come back when you've some TMs. I love to see Pokemon use them!"])
            return
        name = mv.replace("-", " ").title()
        knows = next((p for p in story.player_team if p and mv in [str(m).upper() for m in (getattr(p, "moves", None) or [])]), None)
        if knows is None:
            show(["Oh, a Trainer! Would you do me a favour? I'd love to see a Pokemon that knows %s. Today, please!" % name])
            return
        story.story_flags["b2_move_lady_day"] = today
        story.inventory["HEART_SCALE"] = story.inventory.get("HEART_SCALE", 0) + 1
        show(["Oh my! Your %s can use %s! You taught it just for me? How touching!" % (knows.display_name, name),
              "Please accept this small token of my thanks. You received a Heart Scale!"])
        return
    if ev.get("runner"):
        flag = ev["runner"]
        if story.story_flags.get(flag):
            show(["Refreshed! 100% rehydrated! I'll dash to the next bridge!"])
            return
        if not story.inventory.get("FRESH_WATER"):
            show(["*Pant... pant...* So thirsty... We met on Skyarrow Bridge, remember? A Fresh Water...?",
                  "You don't have any? Thanks for the thought anyway..."])
            return
        story.inventory["FRESH_WATER"] -= 1
        story.story_flags[flag] = True
        show(["*Pant... pant...* So thirsty... We met on Skyarrow Bridge, remember? Could you spare a Fresh Water?",
              "You handed over a Fresh Water.", "Refreshed! 100% rehydrated! Thank you! I'll dash to the next bridge!"])
        return
    if ev.get("tm_lady"):   # (batch 6b: Mistralton's TM fan: an HP Up at 10, 20, 35, 50 and 70 TMs, one more for all 95)
        return _tm_lady(state, story, show)
    if ev.get("daily_gift"):   # (batch 7b: Route 13's treasure hunter: one of his finds a day, the same all day)
        import datetime
        import random
        d = ev["daily_gift"]
        today = datetime.date.today().isoformat()
        if story.story_flags.get(d["key"]) == today:
            show(d.get("done") or ["Come back tomorrow!"])
            return
        item = random.Random(d["key"] + "@" + today).choice(d["items"])
        story.story_flags[d["key"]] = today
        story.inventory[item] = story.inventory.get(item, 0) + 1
        show(list(lines or []) + ["You received a %s!" % item.replace("_", " ").title()])
        return
    if ev.get("dex_register"):   # (batch 6b: Route 7's old man shows you Tornadus and Thundurus, then Landorus)
        for sp in ev["dex_register"]:
            state.game.data.mark_seen(int(sp))
        show(lines or ["They have been registered in the Pokedex."])
        return
    if ev.get("party_type"):   # (batch 6b: the Cargo Service's worker: 5 Net Balls once, for a Flying- or Psychic-type)
        want = {str(t).upper() for t in ev["party_type"]["types"]}
        flag = ev["party_type"]["flag"]
        if story.story_flags.get(flag):
            show(ev["party_type"].get("done") or ["Thanks again for the help!"])
            return
        has = any(p and not getattr(p, "is_egg", False) and want & {str(t).upper() for t in (getattr(p, "types", None) or [])}
                  for p in story.player_team)
        if not has:
            show(ev["party_type"].get("fail") or ["..."])
            return
        story.story_flags[flag] = True
        for item, n in (ev["party_type"].get("gift") or {}).items():
            story.inventory[item] = story.inventory.get(item, 0) + int(n)
        show(lines or ["Thank you!"])
        return
    if ev.get("toggle"):
        flags = state.game.story_manager.story_flags
        flags[ev["toggle"]] = not flags.get(ev["toggle"])
        if lines:
            show(lines)
        return
    show(lines or ["..."])
