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
    if arg.startswith("hour:"):   # (the real clock's hour, 0-23: the Marine Tube's Wailord swims by from 3 to 4 pm; 8b)
        import datetime
        return datetime.datetime.now().hour == int(arg.split(":", 1)[1])
    if arg.startswith("holding:"):   # (a Pokemon with you holds this item: the Marine Tube's Roxie fan, a Poison Barb; 8b)
        want = arg.split(":", 1)[1]
        return any(p and getattr(p, "held_item", None) == want for p in story.player_team)
    if arg.startswith("party_ability:"):   # (a Pokemon with you that has this Ability: Village Bridge's baker, Honey Gather; 8a)
        want = arg.split(":", 1)[1].upper().replace("_", "-")
        return any(p and not getattr(p, "is_egg", False) and str(getattr(p, "ability", "") or "").upper().replace("_", "-") == want
                   for p in story.player_team)
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


def _daily_catch(state, story, d, show):
    """Today's species (the same all day, from the place's water); one of it in your party earns the gift, once a day. (Black 2
    also wants it caught that same day: p.caught_today(), the catch date each Pokemon keeps; a Pokemon from an older save has none.)"""
    import datetime
    import random
    from src.minigames.base import species_name
    today = datetime.date.today().isoformat()
    flags = story.story_flags
    sp = random.Random(d["key"] + "@" + today).choice(d["species"])
    name = species_name(state.game, sp)
    if flags.get(d["key"]) == today:
        show(d.get("done") or ["Come back tomorrow!"])
        return
    if not any(p and not getattr(p, "is_egg", False) and getattr(p, "id", None) == sp
               and getattr(p, "caught_today", lambda: False)() for p in story.player_team):
        show([line.replace("{species}", name) for line in d["ask"]])
        return
    flags[d["key"]] = today
    for item, n in (d.get("gift") or {}).items():
        story.inventory[item] = story.inventory.get(item, 0) + int(n)
    got = " and ".join("%d %ss" % (int(n), item.replace("_", " ").title()) for item, n in (d.get("gift") or {}).items())
    show([line.replace("{species}", name) for line in d["won"]] + ["You received %s!" % got])


def _daily_prop(state, story, d, show):
    """One Prop a day from a list, in order, till every one is given (Black 2: the Opelucid fan's Big Bag, Fluffy Beard, Gift Box
    and Scarlet Hat); needs the Prop Case."""
    import datetime
    from src.world import musical
    flags = story.story_flags
    if not flags.get("b2_prop_case"):
        show(d.get("no_case") or ["..."])
        return
    have = set(musical.props(state.game))
    left = [p for p in d["props"] if p not in have]
    if not left:
        show(d.get("all") or ["..."])
        return
    today = datetime.date.today().isoformat()
    if flags.get(d["key"]) == today:
        show(d.get("come_back") or ["Come back tomorrow!"])
        return
    flags[d["key"]] = today
    musical.give_prop(state.game, left[0])
    show(list(d.get("lines") or []) + ["You received the %s!" % musical.prop_name(left[0])] + list(d.get("come_back") or []))


# (Black 2's text 145: the girl names a Pokemon; the friend of the same family mimicked her: Klang, Swoobat, Azumarill,
#  Eelektross, and the names she calls out, lines 12-19)
MIMIC_FRIENDS = ["Klang", "Swoobat", "Azumarill", "Eelektross"]
MIMIC_CALLS = [["Klink", "Klinklang"], ["Woobat"], ["Azurill", "Marill"], ["Tynamo", "Eelektrik"]]


def _mimic(story, who, show):
    """who "girl": she calls out a Pokemon and one friend mimics it (story flag b2_mimic_pick: that friend's number);
    who 0-3: you pick that friend: right if it's the one of the same family."""
    import random
    flags = story.story_flags
    if who == "girl":
        k = random.randrange(len(MIMIC_FRIENDS))
        flags["b2_mimic_pick"] = k
        show(["Mimicking somebody is fun, isn't it? Want to find which of my friends mimics me?", "OK! Here goes!",
              "...%s!" % random.choice(MIMIC_CALLS[k]), "Who mimicked me? Go and talk to that friend!"])
        return
    pick = flags.get("b2_mimic_pick")
    if pick is None:   # (no game on: each friend's own line, Black 2's 20-22)
        show([["I'm not a mimicker. But mimicking is fun.", "I want to cherish my originality.",
               "It's nicer to be mimicked than to mimic somebody!", "Mimic? Me? Never!"][int(who)]])
        return
    flags.pop("b2_mimic_pick", None)
    if int(pick) == int(who):
        flags["b2_mimic_wins"] = int(flags.get("b2_mimic_wins", 0) or 0) + 1
        show(["%s!" % MIMIC_FRIENDS[int(who)], "Did that friend mimic me?", "Correct! Trainer, you're great! Talk to me to try again!"])
    else:
        show(["%s!" % MIMIC_FRIENDS[int(who)], "Did that friend mimic me?", "Hmmm... Too bad. Talk to me to try again!"])


# (Black 2's painter, Opelucid's text 141 lines 13-20: the Medal Box's colour by your Medal rank; ours by the share of the
#  Medal Rally's Medals you hold: a fifth, two fifths, three, four, and all of them for the version's legend)
PAINTS = [(0.2, "sky-blue", "The sky-blue is as refreshing as a clear autumn day!"),
          (0.4, "copper", "The copper coating sparkles so elegantly!"),
          (0.6, "silver", "That silver coating is so chic and cool!"),
          (0.8, "gold", "How luxurious! That gold coating is gorgeous!")]


def _medal_paint(story, show):
    from src.world import medals
    if not medals.have_box(story):
        show(["Oh! A Trainer without a Medal Box? Mr. Medal in Floccesy Town will give you one!"])
        return
    got, total = len(medals.received(story)), max(1, len(medals.MEDALS))
    flags = story.story_flags
    if got >= total:
        legend = "Zekrom" if flags.get("unova_version") != "WHITE_2" else "Reshiram"
        look = "black with blue highlights" if legend == "Zekrom" else "white with red highlights"
        paint, line = legend, "A stylish %s design, with %s as its motif! It's for those with every Medal!" % (look, legend)
    else:
        best = [p for p in PAINTS if got >= p[0] * total]
        if not best:
            show(["Oh! Your Medal Box... It's still plain. Collect more Medals and I'll paint it for you!",
                  "You have %d of %d Medals." % (got, total)])
            return
        _r, paint, line = best[-1]
    flags["b2_medal_box_paint"] = paint
    show(["Oh! Your Medal Box...", line, "Your Medal Box was painted %s!" % paint])


def _potion_errand(story, show):
    import datetime
    flags = story.story_flags
    today = datetime.date.today().isoformat()
    if flags.get("b2_mall_lady_done"):
        show(["Shopping is so much fun! I'm thrilled with all I've accomplished!"])
        return
    day = flags.get("b2_mall_lady_day")
    if not day:
        flags["b2_mall_lady_day"] = today
        story.money = int(getattr(story, "money", 0) or 0) + 1200
        show(["I'm a Lady... I'm having ever so much trouble finding out what is sold where.",
              "Would you be so kind as to buy a Hyper Potion for me? Here is the money for it.", "You received $1,200!"])
        return
    if not story.inventory.get("HYPER_POTION"):
        show(["Did I not ask you to buy a Hyper Potion for me? Please! I'm waiting."])
        return
    story.inventory["HYPER_POTION"] -= 1
    gift = "ENERGY_ROOT" if day == today else "ENERGY_POWDER"
    story.inventory[gift] = story.inventory.get(gift, 0) + 1
    flags["b2_mall_lady_done"] = True
    show(["It's a Hyper Potion!" + (" Thank you for buying it so quickly!" if gift == "ENERGY_ROOT"
                                    else " It feels as though I've been waiting ever so long. But I'm happy to have it."),
          "This isn't much, but please take it.", "You received %s!" % ("an Energy Root" if gift == "ENERGY_ROOT" else "an Energy Powder")])


def _dex_info(game):
    """assets/dex_info.json (height m, weight kg...), loaded once (the same cache as catching.weight)."""
    info = getattr(game, "_dex_info", None)
    if info is None:
        import json, os
        try:
            with open(os.path.join(game.assets.assets_dir, "dex_info.json"), encoding="utf-8") as f:
                info = json.load(f)
        except OSError:
            info = {}
        game._dex_info = info
    return info


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
    if ev.get("show_size"):   # (batch 12a: Accumula's fans of tiny and huge Pokemon - show one with you, a gift once a day)
        import datetime
        sz = ev["show_size"]
        today = datetime.date.today().isoformat()
        if story.story_flags.get(sz["flag"]) == today:
            show(sz.get("done") or ["Show me another one tomorrow!"])
            return
        info = _dex_info(state.game)
        tall = lambda p: float((info.get(str(int(p.id))) or {}).get("height") or 0)
        fits = lambda h: h > 0 and ((h <= float(sz["max"])) if "max" in sz else (h >= float(sz.get("min", 99))))
        mon = next((p for p in story.player_team if p and fits(tall(p))), None)
        if mon is None:
            show(list(lines or []) + list(sz.get("ask") or []))
            return
        story.story_flags[sz["flag"]] = today
        for item, n in (sz.get("gift") or {}).items():
            story.inventory[item] = story.inventory.get(item, 0) + int(n)
        show([l.replace("{mon}", mon.display_name) for l in sz.get("thanks") or []]
             + ["You received %s!" % ", ".join(k.replace("_", " ").title() for k in (sz.get("gift") or {}))])
        return
    if ev.get("show_ability"):   # (batch 12a: Route 2's Lady wants a Pokemon with Solid Rock - a Dawn Stone, once)
        sa = ev["show_ability"]
        if story.story_flags.get(sa["flag"]):
            show(sa.get("done") or ["What is this feeling coursing through my veins?"])
            return
        from src.pokemon import abilities as _ab
        want = str(sa["ability"]).upper().replace("-", "_").replace(" ", "_")
        norm = lambda k: str(k or "").upper().replace("-", "_").replace(" ", "_")
        mon = next((p for p in story.player_team if p and norm(_ab.ability(state.game, p)) == want), None)
        if mon is None:
            show(list(lines or []) + list(sa.get("ask") or []))
            return
        story.story_flags[sa["flag"]] = True
        for item, n in (sa.get("gift") or {}).items():
            story.inventory[item] = story.inventory.get(item, 0) + int(n)
        show([l.replace("{mon}", mon.display_name) for l in sa.get("thanks") or []]
             + (["You received %s!" % ", ".join(k.replace("_", " ").title() for k in sa["gift"])] if sa.get("gift") else []))
        return
    if ev.get("starter_quiz"):   # (batch 12a: Accumula's quiz on your first partner's height - a Gem of its type, once)
        sq = ev["starter_quiz"]
        if story.story_flags.get(sq["flag"]):
            show(sq.get("done") or ["You really know your first partner!"])
            return
        from src.states.overworld.common import _region_starter_id
        sid = _region_starter_id(state.game)
        raw = state.game.loader.fetch_specific(int(sid)) if sid else None
        types = [str(t).upper() for t in ((raw or {}).get("types") or [])]
        gem = next((g for t, g in (("GRASS", "GRASS_GEM"), ("FIRE", "FIRE_GEM"), ("WATER", "WATER_GEM")) if t in types), None)
        h = (_dex_info(state.game).get(str(int(sid))) or {}).get("height") if sid else None
        if not gem or not h:
            show(["Which Pokemon did you pick as your first partner? ...Hmm, I don't know that one!"])
            return
        name = str((raw or {}).get("name", "")).replace("-", " ").title()
        story.story_flags[sq["flag"]] = True
        story.inventory[gem] = story.inventory.get(gem, 0) + 1
        show(list(lines or []) + ["Your first partner was %s? All righty, a quiz! How tall is %s?" % (name, name),
                                  "You answered: %.1f m. ...Correct! You really know your partner!" % float(h),
                                  "You received a %s!" % gem.replace("_", " ").title()])
        return
    if ev.get("fossil_choice"):   # (batch 12a: Lenora in the Nacrene Museum - pick the Cover Fossil or the Plume Fossil, once)
        fc = ev["fossil_choice"]
        if story.story_flags.get(fc["flag"]):
            show(fc.get("done") or ["Lenora: Take good care of that Fossil! The front desk can restore it."])
            return
        from src.states.systems.pick_list import PickListState
        from src.states.overworld.common import _say_then
        rows = [(c.replace("_", " ").title(), c) for c in fc["choices"]]

        def pick(item):
            if item is None:
                show(["Lenora: Take your time. They'll be here."])
                return
            story.story_flags[fc["flag"]] = item
            story.inventory[item] = story.inventory.get(item, 0) + 1
            show(["You received the %s!" % item.replace("_", " ").title()] + list(fc.get("after") or []))
        _say_then(state, list(lines or []), lambda: state.game.change_state(
            PickListState(state.game, state, fc.get("ask") or "WHICH FOSSIL?", rows, pick)))
        return
    if ev.get("runner"):
        flag = ev["runner"]
        chain = ev.get("chain") or []   # (Skyarrow Bridge, his first and last bridge: once he's had water on every bridge
        if chain and story.story_flags.get(flag) and all(story.story_flags.get(f) for f in chain):   # after it, his thanks)
            if story.story_flags.get(flag + "_thanks"):
                show(["I ran across every bridge in Unova, thanks to you! I'm back where I started!"])
                return
            story.story_flags[flag + "_thanks"] = True
            for item, n in (ev.get("reward") or {}).items():
                story.inventory[item] = story.inventory.get(item, 0) + int(n)
            show(["You! You kept me going across every bridge in Unova! Please, take these!",
                  "You received %s!" % " and ".join("%d %s" % (int(n), item.replace("_", " ").title())
                                                    for item, n in (ev.get("reward") or {}).items())])
            return
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
    if ev.get("daily_catch"):   # (batch 8a: Village Bridge's Hip Waders: today's species; show one caught today, a gift once a day)
        return _daily_catch(state, story, ev["daily_catch"], show)
    if ev.get("daily_prop"):    # (batch 8a: Opelucid's Musical fan: one of his four Props a day, till you have them all)
        return _daily_prop(state, story, ev["daily_prop"], show)
    if ev.get("rotom_form"):   # (batch 8b: Shopping Mall Nine's stockroom: an appliance box changes your Rotom's form)
        from src.pokemon import forms
        slot = next((i for i, p in enumerate(story.player_team) if p and int(getattr(p, "id", 0) or 0) == forms.ROTOM), None)
        if slot is None:
            show(lines or ["A mountain of boxes full of appliances. They're going to waste..."])
            return
        said = forms.rotom_change(state.game, slot, ev["rotom_form"]) or []
        show(list(lines or []) + list(said))
        return
    if ev.get("potion_errand"):   # (batch 8b: the Mall's Lady: $1,200 for a Hyper Potion; that day an Energy Root, later EnergyPowder)
        return _potion_errand(story, show)
    if ev.get("medal_paint"):   # (batch 8a extras: every Center's Medal Box painter, by how many Medals you have)
        return _medal_paint(story, show)
    if ev.get("mimic") is not None:   # (batch 8a extras: Opelucid's Mimic game, upstairs in the old Battle House)
        return _mimic(story, ev["mimic"], show)
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
    if ev.get("clear"):   # (flags that last only while you're in a place: Village Bridge's musicians, Black 2's 0x400A-D)
        for f in ev["clear"]:
            state.game.story_manager.story_flags.pop(f, None)
        if lines:
            show(lines)
        return
    if ev.get("toggle"):
        flags = state.game.story_manager.story_flags
        flags[ev["toggle"]] = not flags.get(ev["toggle"])
        if lines:
            show(lines)
        return
    show(lines or ["..."])
