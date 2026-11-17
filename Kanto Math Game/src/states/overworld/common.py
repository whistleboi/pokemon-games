"""Shared by the route and town screens: names in text, travel button words, trainer sprites,
and the story-event runner (src/world/story_events.py)."""

import pygame
import re
from src.utils import Utils
from src.world import seasons
from src.world import guide
from src.world import levels
from src.pokemon import evolution
from src.pokemon import forms
from src.pokemon.data import Pokemon
from src.world import story_events
from src.config import WHITE, BLACK, GOLD


TRIVIA_PRIZES = [("RARE_CANDY", 1), ("RARE_CANDY", 2), ("LUM_BERRY", 2), ("SITRUS_BERRY", 3), ("MAX_REVIVE", 1),
                 ("ULTRA_BALL", 5), ("FULL_RESTORE", 1)]


def _badge_trivia(state, lines, show):
    """Once a day, a question about one of this region's badges you hold: who gave it you, their strongest Pokemon, or
    the town of its Gym. Three answers to pick from; right: a good prize (TRIVIA_PRIZES)."""
    import datetime as _dt
    import random as _rnd
    game = state.game
    story = game.story_manager
    region = story.get_current_region()
    gyms = []
    for a in game.loader.area_data.get("STORY_PROGRESSION", {}).values():
        lead = (a.get("gym") or {}).get("leader") if isinstance(a, dict) and a.get("region") == region else None
        if isinstance(lead, dict) and lead.get("badge_reward") and lead.get("team"):
            levels = list(lead.get("levels") or [0] * len(lead["team"]))
            ace = lead["team"][max(range(len(lead["team"])), key=lambda i: (levels[i] if i < len(levels) else 0, i))]
            gyms.append({"badge": lead["badge_reward"], "leader": lead.get("name"), "town": a.get("route_name"),
                         "ace": str((game.loader.fetch_specific(int(ace)) or {}).get("name", "?")).title()})
    mine = [g for g in gyms if g["badge"] in (story.badges.get(region) or [])]
    if not mine:
        show(_resolve_lines(game, lines + ["Badge reader: You have no badges for me to read yet. Come back once you've earned one!"]))
        return
    today = _dt.date.today().isoformat()
    if story.story_flags.get("badge_trivia_day") == today or not hasattr(state, "_create_hover_menu"):
        show(_resolve_lines(game, lines + ["Badge reader: One reading a day. Come back tomorrow for another question!"]))
        return
    story.story_flags["badge_trivia_day"] = today
    rng = _rnd.Random()
    g = rng.choice(mine)
    kind, others = rng.choice([("leader", "Which Gym Leader gave you the {badge} Badge?"),
                               ("ace", "Who was {leader}'s strongest Pokémon?"),
                               ("town", "In which town is the Gym of the {badge} Badge?")])
    right = g[kind]
    wrong = rng.sample(sorted({x[kind] for x in gyms if x[kind] != right}), 2)
    answers = [right] + wrong
    rng.shuffle(answers)
    item, qty = rng.choice(TRIVIA_PRIZES)
    from src.pokemon import forms as _forms
    prize = f"{qty} {_forms.item_label(item)}" if qty > 1 else f"a {_forms.item_label(item)}"
    opts = [{"text": a, "action": "EVENT", "event": (
                {"lines": [f"Badge reader: {a}! That's right! You truly remember your journey.", f"Here, take {prize}."],
                 "gift_item": {item: qty}} if a == right else
                {"lines": [f"Badge reader: {a}? No... it was {right}. Try again tomorrow!"]})} for a in answers]
    question = "Badge reader: " + others.format(badge=str(g["badge"]).title(), leader=g["leader"])
    say = getattr(state, "show_message", None)
    if say is None:
        show(_resolve_lines(game, lines + [question]))
        return
    say(_resolve_lines(game, lines + [question]), callback=lambda: state._create_hover_menu(opts, None))


PRIMO_EGGS = [179, 194, 218]   # (HGSS: Primo's three Eggs - Mareep, Wooper, Slugma)
PRIMO_QUIZ = [("Which Pokemon evolves into Pikachu?", "Pichu", ["Raichu", "Plusle"]),
              ("What type are Water moves strong against?", "Fire", ["Grass", "Dragon"]),
              ("Which Pokemon is Johto's Water-type first partner?", "Totodile", ["Squirtle", "Mudkip"]),
              ("What does a Pokemon Center do for free?", "Heals your team", ["Sells Poke Balls", "Teaches moves"]),
              ("Which Badge does Falkner give?", "Zephyr Badge", ["Hive Badge", "Plain Badge"]),
              ("What type is Togepi in Johto?", "Normal", ["Fairy", "Psychic"]),
              ("Which item makes a Pokemon hold off evolving?", "Everstone", ["Moon Stone", "Leftovers"]),
              ("How many Pokemon can travel with you at once?", "Six", ["Four", "Eight"])]


def _primo_quiz(state, lines, show):
    """Primo, the TV star in Violet City's Pokemon Center (HGSS; Jordan 11-15: "do primo's quiz but have him return daily
    until the player has all 3 eggs"): one question a day; right, and you get his next Egg."""
    import datetime as _dt
    import random as _rnd
    game = state.game
    story = game.story_manager
    got = int(story.story_flags.get("primo_eggs", 0) or 0)
    if got >= len(PRIMO_EGGS):
        show(["Primo: You have all three of my Eggs! Watch my show, and raise them well!"])
        return
    today = _dt.date.today().isoformat()
    if story.story_flags.get("primo_day") == today or not hasattr(state, "_create_hover_menu"):
        show(["Primo: One question a day, my friend! Come back tomorrow for another."])
        return
    story.story_flags["primo_day"] = today
    q, right, wrong = _rnd.Random().choice(PRIMO_QUIZ)
    answers = [right] + list(wrong)
    _rnd.shuffle(answers)
    egg = PRIMO_EGGS[got]
    opts = [{"text": a, "action": "EVENT", "event": (
                {"lines": [f"Primo: {a}! Correct! You're a natural. Here's an Egg from my show!"], "gift_egg": egg, "primo_next": True}
                if a == right else {"lines": [f"Primo: {a}? Oh, so close! It was {right}. Try again tomorrow!"]})} for a in answers]
    say = getattr(state, "show_message", None)
    if say is None:
        show(_resolve_lines(game, lines + [f"Primo: {q}"]))
        return
    say(_resolve_lines(game, lines + [f"Primo: Quiz time! {q}"]), callback=lambda: state._create_hover_menu(opts, None))


def _memories(game):
    """The lines the Memory Girl reads from your first Pokemon: where you met, the battles it won with you, the catches
    it was there for, its Contest ribbons (what our game keeps of a Pokemon's journey)."""
    lead = next((p for p in game.story_manager.player_team if p and not getattr(p, "is_egg", False)), None)
    if lead is None:
        return ["Memory Girl: Hmm? You don't have a Pokemon with you."]
    name = getattr(lead, "display_name", None) or getattr(lead, "name", "Your Pokemon")
    c = getattr(lead, "counters", None) or {}
    out = [f"Memory Girl: Let me see... I can feel {name}'s memories."]
    region = str(getattr(lead, "caught_region", "") or "").replace("_", " ").title()
    lvl = getattr(lead, "caught_level", None)
    if region:
        out.append(f"It remembers the day it met you in {region}" + (f", back at level {lvl}." if lvl else "."))
    if c.get("wins"):
        out.append(f"It remembers winning {c['wins']} battle{'s' if c['wins'] != 1 else ''} with you"
                   + (f", and {c['crits']} critical hit{'s' if c.get('crits') != 1 else ''} that made you cheer!" if c.get("crits") else "!"))
    if c.get("catches"):
        out.append(f"It was there when you caught {c['catches']} Pokemon. It made new friends each time.")
    rib = getattr(lead, "ribbons", None) or []
    if rib:
        out.append(f"It remembers the crowd at the Contest Hall, and the {len(rib)} ribbon{'s' if len(rib) != 1 else ''} it won.")
    if len(out) == 1:
        out.append("Its memories with you are only just starting. Go and make some more!")
    else:
        out.append(f"Memory Girl: {name} treasures every one of those moments with you.")
    return out


def _fill_names(game, text):
    if not isinstance(text, str):
        return text
    text = (text.replace("{player_name}", getattr(game, "player_name", "TRAINER"))
                .replace("{rival_name}", getattr(game, "rival_name", "???"))
                .replace("{friend_name}", getattr(game, "friend_name", None) or "???"))
    if "{" in text and getattr(game, "story_manager", None) is not None and str(game.story_manager.get_current_region() or "") == "HOENN":
        from src.world import hoenn as _hoenn   # (Hoenn's scenes name the version's team and its leader: {team}, {leader}, {other_leader}...)
        for k, v in sorted(_hoenn.words(game.story_manager).items(), key=lambda kv: -len(kv[0])):
            text = text.replace("{" + k + "}", v)
    if "{kanto_" in text:  # Mew's hint: Kanto species #1-150 only (other regions don't count)
        caught = game.story_manager.kanto_caught_count()
        text = text.replace("{kanto_caught}", str(caught)).replace("{kanto_missing}", str(150 - caught))
    return text


# Travel buttons, one way in every region (Jordan, 11-01): the place's name in Title Case, and for a
# ride the ride too ("Seagallop to One Island"); no "back to", "exit", directions or capitals from
# the data. An option's own "label" wins. Red, in towns and on routes (gold: the way to the Journal's goal).
TRAVEL_RIDES = ("Seagallop", "S.S. Anne", "S.S. Aqua", "S.S. Tidal", "Magnet Train", "Cable Car", "Flying Taxi",
                "Space-Time Rift", "Spatial Rift", "Ultra Wormhole", "Exchange", "Train", "Ferry", "Boat", "Ship", "Bus")


TRAVEL_COLOR = "RED"


def _title_words(text):
    """'MT. SILVER' -> 'Mt. Silver', "BILL'S HOUSE" -> "Bill's House" (only text that's all capitals)."""
    if text != text.upper():
        return text
    return " ".join(w[:1].upper() + w[1:].lower() if not re.fullmatch(r"(?:[A-Z]\.)+", w) else w for w in text.split())


def travel_label(game, item):
    """The words on a travel button (see TRAVEL_RIDES)."""
    if item.get("label"):
        return _fill_names(game, item["label"])
    text = _fill_names(game, item.get("text") or "")
    target = item.get("target_area") or item.get("target")
    name = ((game.loader.area_data.get("STORY_PROGRESSION", {}).get(target) or {}).get("route_name")
            if target else None)
    ride = next((r for r in TRAVEL_RIDES if re.search(r"(?<![\w.])" + re.escape(r) + r"(?![\w])", text, re.I)), None)
    if not name:  # no such area (or no name): the words given, tidied
        name = re.sub(r"^(?:back to|return to|exit to|go to|to)\s+", "", text.replace("_", " "), flags=re.I)
        if ride:
            name = re.split(r"\bto\b", name, maxsplit=1, flags=re.I)[-1].strip() if re.search(r"\bto\b", name, re.I) else name
        name = re.sub(r"\s*\((?:to |north|south|east|west|base|ferry|train|bus)[^)]*\)\s*$", "", name, flags=re.I)
        name = _title_words(name.strip(" !")) or text
    if ride and ride.lower() not in name.lower():
        return f"{ride} to {name}"
    return name


def _resolve_lines(game, value):
    """GAME_TEXT key(s) or literal line(s) -> list of lines with names filled in."""
    items = value if isinstance(value, list) else [value]
    lines = []
    for item in items:
        if isinstance(item, str) and item in game.assets.game_text:
            text = game.assets.game_text[item]
            lines.extend(text if isinstance(text, list) else [text])
        elif item:
            lines.append(item)
    return [_fill_names(game, line) for line in lines]


def _scaled_player_image(game, char_key):
    img = game.assets.get_player_image(char_key, back=False) if char_key else None
    if not img:
        return None
    h = int(game.height * 0.6)
    return pygame.transform.scale(img, (int(img.get_width() * (h / img.get_height())), h))


def rival_image(game, char_key):
    """A rival's art: their trainer sprite (blue.png, silver.png, may.png...), else the player art."""
    img = game.assets.get_trainer_image(f"{char_key}.png") if char_key else None
    return img or _scaled_player_image(game, char_key)


def _trainer_sprite(game, sprite_name):
    """Trainer art; "{rival_character}" / "{friend_character}" are this region's rival and friend."""
    if sprite_name == "{friend_character}":
        img = rival_image(game, getattr(game, "friend_character", None))
        if img:
            return img
    elif sprite_name != "{rival_character}":
        img = game.assets.get_trainer_image(sprite_name or "rival.png")
        if img:
            return img
    return (rival_image(game, getattr(game, "rival_character", None))
            or game.assets.get_trainer_image("rival.png"))


def _region_starter_id(game):
    story = game.story_manager
    sid = story.story_flags.get(f"starter_{story.get_current_region().lower()}")
    if sid:
        return sid
    return story.player_team[0].id if story.player_team else None


def _cast_trainer(game, t_info):
    """A story trainer tied to a character of this region rather than a role (Jordan, 10-27).
    "who": "cheren" makes the battle show as whichever role that character holds in this save (the
    rival or the friend), and "by_character": {character: {team, team_choice, levels}} gives each
    character their own team (Cheren and Bianca in Unova, Serena and Calem in Kalos)."""
    who, by = t_info.get("who"), t_info.get("by_character")
    if not who and not by:
        return t_info
    t_info = dict(t_info)
    rival = str(getattr(game, "rival_character", "") or "").lower()
    friend = str(getattr(game, "friend_character", "") or "").lower()
    if who:
        if rival == who:
            t_info["name"], t_info["sprite"] = "{rival_name}", "{rival_character}"
        elif friend == who:
            t_info["name"], t_info["sprite"] = "{friend_name}", "{friend_character}"
        else:
            t_info.setdefault("name", who.title())
            t_info.setdefault("sprite", f"{who}.png")
        key = who
    else:
        key = friend if "{friend_name}" in str(t_info.get("name")) else rival
    t_info.update((by or {}).get(key) or {})
    return t_info


def _story_team(game, area_key, t_info):
    """A story trainer's team: picked by the player's starter ("team_choice"), at the exact
    levels from the games when given ("levels"), else around the top "level", else the area's."""
    t_info = _cast_trainer(game, t_info)
    team_ids = list((t_info.get("team_choice") or {}).get(str(_region_starter_id(game))) or t_info.get("team", []))
    team = [Pokemon(game.loader.fetch_specific(tid), game.assets, size_mult=3.125) for tid in team_ids]
    forms.mark_trainer_team(team, t_info)
    top = t_info.get("level")  # story beats set in early areas carry their own level
    if levels.postgame_trainers(game, area_key):  # post-game: every trainer follows the player's cap
        levels.set_team(team, levels.trainer_team_levels(game, area_key, len(team), boss=True))  # legendaries stay 70
    elif t_info.get("levels"):
        levels.set_team(team, levels.follow_team(game, t_info["levels"]), exact=True)
    elif top:
        levels.set_team(team, levels.follow_team(game, [max(2, top - (len(team) - 1 - i)) for i in range(len(team))]))
    else:
        levels.set_team(team, levels.trainer_team_levels(game, area_key, len(team), boss=True))
    return team


def _start_event_battle(game, area_key, t_info, flag):
    """A story NPC's trainer battle (team chosen by the region starter when it has a team_choice)."""
    from src.states.battle import TrainerBattleState, TrainerIntroState
    t_info = _cast_trainer(game, t_info)
    if t_info.get("villain") and str(game.story_manager.get_current_region() or "") == "HOENN":
        from src.world import hoenn as _h   # (a scene's villain, written into a map: dressed as this version's team, like the data's)
        v = _h.VERSIONS.get(_h.version(game.story_manager))
        if v:
            keep = t_info.get("name")
            t_info = _h._villain(dict(t_info), v)
            if "{" in str(keep or ""):   # (a name of its own with the team's word in it: "{team} Grunts")
                t_info["name"] = keep
    team = _story_team(game, area_key, t_info)
    sprite = _trainer_sprite(game, t_info.get("sprite"))
    dlg = t_info.get("dialogue") or {}
    battle = TrainerBattleState(
        game, team, trainer_sprite=sprite, trainer_class=t_info.get("class", "TRAINER"),
        trainer_name=_fill_names(game, t_info.get("name")),
        custom_dialogue={k: _resolve_lines(game, v) for k, v in dlg.items() if k != "intro"},
        rewards=dict(t_info.get("rewards") or {"balls": 3}), battle_type="event",
        is_boss_battle=t_info.get("is_boss_battle", False), area_name=area_key, victory_flag=flag)
    return TrainerIntroState(game, sprite, t_info.get("_intro_lines") or ["..."], battle)


def _run_story_event(state, key, check, show):
    """Play a story NPC event (see src/world/story_events.py).
    check(condition) tests a menu condition; show(lines) shows dialogue and returns to the menu."""
    game = state.game
    story = game.story_manager
    ev = key if isinstance(key, dict) else story_events.get(key)
    if ev.get("stages"):  # one NPC through the story: the first stage that is ready and not done
        stage = next((st for st in ev["stages"] if not story.story_flags.get(st.get("flag") or "")
                      and all(check(c) for c in st.get("requires", []))), None)
        ev = stage or {"lines": ev.get("done") or ["..."]}
    if ev.get("daily") and ev.get("flag"):  # (once a day, by the real clock: an Apricorn tree; HGSS, Jordan 11-15)
        import datetime
        today = f"{ev['flag']}@{datetime.date.today().isoformat()}"
        for k in [k for k in story.story_flags if k.startswith(ev["flag"] + "@") and k != today]:
            story.story_flags.pop(k)   # (yesterday's picking forgotten: one flag a tree)
        ev = dict(ev, flag=today)
    flag = ev.get("flag")
    if flag and story.story_flags.get(flag):
        if ev.get("tutor") and not ev["tutor"].get("choices"):   # (a once-only tutor, used: again, for money; Jordan 11-16)
            _tutor_again(state, ev, show)
            return
        show(_resolve_lines(game, ev.get("done") or ev.get("lines") or ["..."]))
        return
    if "unlocked_national_dex" in ev.get("requires", []):
        from src.states.systems import has_national_dex
        has_national_dex(story)
    if not all(check(c) for c in ev.get("requires", [])):
        if ev.get("fail_flag"):  # hearing the "not yet" can start a task (Devon's stolen parts: the journal)
            story.story_flags[ev["fail_flag"]] = True
        show(_resolve_lines(game, ev.get("fail") or ["You can't do that yet."]))
        return
    lines = _resolve_lines(game, ev.get("lines") or [])
    if ev.get("puzzle"):  # a math minigame (Dotted Hole's braille, a Rocket door code...)
        _start_event_puzzle(state, ev, lines, show)
        return
    if ev.get("battle"):
        t_info = dict(ev["battle"], _intro_lines=lines or None)
        game.change_state(_start_event_battle(game, story.current_area_key, t_info, flag))
        return
    if ev.get("pay"):  # (an entry fee: the Pewter Museum's 50 ticket, FireRed; the Day Care Annex lady's $100 loan, ORAS)
        cost = int(ev["pay"])
        if getattr(story, "money", 0) < cost:
            show(_resolve_lines(game, ev.get("fail") or ["You don't have enough money."]))
            return
        story.money -= cost
        lines.append(f"{getattr(game, 'player_name', 'You')} paid ${cost}.")
    if ev.get("starter"):  # (one of the Poke Balls on Oak's table: the starter screen, then the rival's first battle)
        from src.states.menus import StarterSelectionState
        reg = ev["starter"]
        if story.story_flags.get(f"received_starter_{reg.lower()}"):
            show(_resolve_lines(game, ev.get("done") or ["It's empty now."]))
            return
        if reg == "KANTO":
            story.story_flags["kanto_parcel_era"] = True  # (the FireRed opening: the Parcel, then the Pokedex)
        ids = story.get_region_start(reg).get("starters") or [1, 4, 7]
        if getattr(state, "room", None) and hasattr(state, "player"):   # (back where you stood afterwards: Elm's Lab, HGSS)
            game.walk_town_pos = (state.area_key, tuple(state.player), (0, 1))
            game.walk_town_room = (state.area_key, state.room)
        go = lambda: game.change_state(StarterSelectionState(game, starter_ids=ids, region=reg))
        if lines:
            state_show = getattr(state, "show_message", None) or getattr(state, "show_dialogue")
            state_show(lines, callback=go)
        else:
            go()
        return
    if ev.get("scene") == "wally_catch":  # Wally catches his Ralts (src/states/hoenn.py)
        from src.states.hoenn import WallyCatchState

        def after():
            if flag:  # first, so arriving back doesn't start the scene again
                story.story_flags[flag] = True
            if hasattr(state, "is_resuming"):
                state.is_resuming = True
            game.change_state(state)
            _run_story_event(state, dict(ev, scene=None, flag=None, lines=ev.get("after") or ["..."]), check, show)
        show_then = lines or ["..."]
        state_show = getattr(state, "show_message", None) or getattr(state, "show_dialogue")
        state_show(show_then, callback=lambda: game.change_state(WallyCatchState(game, after)))
        return
    if ev.get("gift_daily"):   # (a Mirage spot's hidden item: today's, once a day: src/world/soaring.py)
        from src.world import soaring as _soar
        _item = _soar.daily_item(story, ev["gift_daily"])
        story.inventory[_item] = story.inventory.get(_item, 0) + 1
        story.story_flags.pop("mirage_daily_ready", None)
        lines.append(f"{getattr(game, 'player_name', 'You')} found a {forms.item_label(_item).upper()}!")
    if ev.get("gift_cycle"):   # (one after another, then the last again and again: the S.S. Aqua captain's Plates, then Nuggets; HGSS)
        _cf = ev.get("cycle_flag") or "gift_cycle"
        _n = int(story.story_flags.get(_cf) or 0)
        _item = ev["gift_cycle"][min(_n, len(ev["gift_cycle"]) - 1)]
        story.story_flags[_cf] = _n + 1
        story.inventory[_item] = story.inventory.get(_item, 0) + 1
        lines.append(f"{getattr(game, 'player_name', 'You')} received the {forms.item_label(_item).upper()}!")
    for item, qty in (ev.get("gift_item") or {}).items():
        if item == "balls":
            story.balls_left = getattr(story, "balls_left", 0) + qty  # the one ball count
            lines.append(f"You received {qty} Poke Balls!")
            continue
        story.inventory[item] = story.inventory.get(item, 0) + qty
        lines.append(f"{getattr(game, 'player_name', 'You')} received the {forms.item_label(item).upper()}!")
    for item, qty in (ev.get("take_item") or {}).items():
        story.inventory[item] = max(0, story.inventory.get(item, 0) - qty)
    if ev.get("heal"):  # a nurse in a building (Silph Co.): like a Pokemon Center
        from src.states.overworld.area_transition import heal_team
        heal_team(game)
    if ev.get("reset_area"):  # Mt. Battle: start the mountain over (its trainers can be fought again)
        story.defeated_trainers.pop(story.current_area_key, None)
        for f in ev.get("clear_flags", []):
            story.story_flags.pop(f, None)
    lines += _teach_move(game, ev.get("teach"))
    lines += story.evolve_party(ev.get("evolve"))  # Kubfu at the Towers of Two Fists
    if ev.get("purify") == "choose":  # Orre's Relic Stone: purify one Shadow Pokemon, if you want to
        _choose_purify(state, lines, show)
        return
    if ev.get("purify"):
        names = story.purify_shadow()
        lines += ([f"{n}'s heart opened! It's no longer a Shadow Pokemon." for n in names]
                  or ["None of your Pokemon need purifying right now."])
        if names:
            lines += _evolve_due(game, names)
    if ev.get("odd_egg"):  # (Route 34's Day-Care Man: seven Odd Eggs, one a day after the last hatches - src/world/odd_egg.py)
        from src.world import odd_egg as _odd
        _sp = _odd.talk(game, lines)
        if _sp:
            ev = dict(ev, gift_egg=_sp)
    if ev.get("gift_egg"):  # an Egg to hatch on your travels (Lavaridge's old woman: Wynaut, as in the games)
        from src.pokemon import breeding
        from src.pokemon.data import Pokemon
        egg = Pokemon(game.loader.fetch_specific(int(ev["gift_egg"])), game.assets, size_mult=2.5)
        egg.level, egg.xp = 1, 0
        egg.caught_region = story.get_current_region()
        egg.moves, egg.move_pool = [], []
        breeding.make_unhatched(game, egg)
        story.player_team.append(egg)
        lines.append(f"{game.player_name} received an Egg!")
    gift = story_events.gift_for_starter(ev.get("gift_pokemon"), _region_starter_id(game))
    if gift:
        if ev.get("max_party") and len([p for p in story.player_team if p]) > int(ev["max_party"]):   # (HGSS's Elder: room for it)
            show(_resolve_lines(game, ev.get("full") or ["You have no room in your party for it."]))
            return
        before = len(story.player_team)
        lines.append(story_events.gift_pokemon(game, gift, ev.get("gift_level"), ev.get("gift_held")))
        gm = ev.get("gift_moves")   # {"if": flag, "moves": [...], "else": [...]}: the Dragon Shrine's Dratini (Extreme Speed or Leer)
        if gm and len(story.player_team) > before:
            mon = story.player_team[-1]
            mv = gm["moves"] if story.story_flags.get(gm.get("if", "")) else gm.get("else") or []
            if mv:
                from src.pokemon import moves as _mvg
                pool = _mvg.move_pool(game, mon)
                for m in mv:
                    if m not in pool:
                        pool.append(m)
                mon.moves = list(mv)[:_mvg.MAX_MOVES]
    if flag:
        story.story_flags[flag] = True
    if ev.get("trade"):  # an in-game trade (Fortree's girl: a Spinda for her Skitty): your first one they want, for theirs
        tr = ev["trade"]   # {"want": species, "give": species, "item": what it holds}
        from src.pokemon.data import Pokemon
        mine = next((i for i, p in enumerate(story.player_team) if p and p.id == int(tr["want"]) and not getattr(p, "is_egg", False)), None)
        if mine is None:
            show(_resolve_lines(game, ev.get("fail") or ["You don't have the Pokemon they want."]))
            return
        old = story.player_team[mine]
        new = Pokemon(game.loader.fetch_specific(int(tr["give"])), game.assets, size_mult=2.5)
        new.level = old.level
        new.current_hp = new.get_max_hp()
        new.caught_region = story.get_current_region()
        if tr.get("item"):
            new.held_item = tr["item"]
        story.player_team[mine] = new
        game.data.mark_seen(new.id)
        game.data.add_pokemon(new)
        lines.append(f"{old.display_name} was traded for {new.display_name}!")
    if ev.get("elevator"):  # (Goldenrod Dept. Store's elevator attendant, Jordan 11-15 option B: the floors as a list)
        from src.states.systems.pick_list import PickListState
        floors = [("B1F", "B1F")] + [(f"{n}F", n) for n in range(1, 7)]

        def ride(to):
            if to is None:
                show(["Attendant: Do come again!"])
                return
            from src.states.overworld import AreaTransitionState
            if to == "B1F":
                game.arrive_floor = ("GOLDENROD_UNDERGROUND", 4, [18, 6])
                game.change_state(AreaTransitionState(game, "GOLDENROD_UNDERGROUND", initial_message=["The elevator hums down to B1F..."]))
                return
            room = "dept" if to == 1 else f"dept_{to}"
            game.walk_town_room = ("GOLDENROD_CITY", room)
            game.walk_town_pos = ("GOLDENROD_CITY", tuple(ev.get("lift_at") or (19, 3)), (0, 1))
            game.change_state(AreaTransitionState(game, "GOLDENROD_CITY", initial_message=[f"The elevator stops at {to}F."]))
        game.change_state(PickListState(game, state, "ELEVATOR", floors, ride))
        return
    if ev.get("feed"):  # (Moomoo Farm's sick Miltank, HGSS: feed it Oran Berries one at a time till it's well)
        fd = ev["feed"]; flags = story.story_flags
        if flags.get(fd["flag"]):
            show(_resolve_lines(game, ev.get("done") or ["It looks happy and healthy."]))
            return
        if story.inventory.get(fd["item"], 0) <= 0:
            show(_resolve_lines(game, lines + list(fd.get("fail") or ["It needs something to eat..."])))
            return
        story.inventory[fd["item"]] -= 1
        if story.inventory[fd["item"]] <= 0:
            story.inventory.pop(fd["item"], None)
        n = int(flags.get(fd["count"], 0)) + 1
        flags[fd["count"]] = n
        name = fd["item"].replace("_", " ").title()
        if n >= int(fd["need"]):
            flags[fd["flag"]] = True
            show(_resolve_lines(game, [f"You gave it a {name}.", *fd.get("well", ["It's full of energy again!"])]))
        else:
            show(_resolve_lines(game, [f"You gave it a {name}. It munched it up... ({n} of {fd['need']})", *fd.get("more", ["It still looks weak."])]))
        return
    if ev.get("size_record"):  # (Lake of Rage's Fishing Guru, HGSS's Magikarp record - Jordan 11-15: measured by its hidden strength,
        import random as _rnd   #  the sum of its six IVs, record starting at 130; shown as a length, never as IVs)
        flags = story.story_flags
        karps = [p for p in story.player_team if p and getattr(p, "id", None) == 129 and not getattr(p, "is_egg", False)]
        if not karps:
            show(_resolve_lines(game, lines + [_rnd.choice(["Bring me a Magikarp and I'll measure it! I'm after a record-breaker.",
                                                           "No Magikarp with you? Catch one in the lake and show me!"])]))
            return
        ivs = lambda p: dict(getattr(p, "ivs", {}) or {})
        best = max(karps, key=lambda p: sum(ivs(p).values()))
        total = sum(ivs(best).values())
        inch = lambda t: round(10 + t / 4, 1)
        record = int(flags.get("magikarp_record", 130))
        out = list(lines) + [f"Let's see that Magikarp... It measures {inch(total)} inches!"]
        if total > record:
            flags["magikarp_record"] = total
            story.inventory["ETHER"] = story.inventory.get("ETHER", 0) + 1
            out += [_rnd.choice(["Wow! That's a new record! It beats the old one at " + str(inch(record)) + " inches!",
                                 "Incredible! " + str(inch(total)) + " inches! The record's yours now!",
                                 "Now THAT is a Magikarp! A new record, no doubt about it!"]),
                    "Here, take this as a prize.", f"{getattr(game, 'player_name', 'You')} received an ETHER!"]
        else:
            out.append(_rnd.choice([f"Hmm... Not bad, but the record is {inch(record)} inches.",
                                    f"Close, but no record. The one to beat is {inch(record)} inches.",
                                    f"Respectable! Still, my record book says {inch(record)} inches."]))
            low_k, low_v = min(ivs(best).items(), key=lambda kv: kv[1]) if ivs(best) else (None, 99)
            if low_v < 17:
                said = {"SPEED": ["The one Ralph had was faster than that!", "Ralph's was quicker in the water, I tell you."],
                        "ATTACK": ["The one Ralph had hit harder than that!", "Ralph's Magikarp had more punch to its splash."],
                        "DEFENSE": ["The one Ralph had was tougher than that!", "Ralph's had scales like armor plating!"],
                        "SPATK": ["The one Ralph had had a sharper glint in its eye!"],
                        "SPDEF": ["The one Ralph had was steadier than that!", "Ralph's Magikarp never flinched at anything."],
                        "HP": ["The one Ralph had was hardier than that!", "Ralph's could flop around all day long!"]}.get(low_k)
                if said:
                    out.append(_rnd.choice(said))
        show(_resolve_lines(game, out))
        return
    if ev.get("salon"):  # (Goldenrod Tunnel's Pokemon Salon, HGSS: a haircut a day; the older brother's does more for its friendship)
        import datetime as _dt
        sal = ev["salon"]; today = _dt.date.today().isoformat()
        lead = next((p for p in story.player_team if p and not getattr(p, "is_egg", False)), None)
        if story.story_flags.get(sal["key"]) == today:
            show(["Sorry, one haircut a day. Come back tomorrow!"])
            return
        if lead is None:
            show(["Bring a Pokemon along and I'll make it look wonderful!"])
            return
        story.story_flags[sal["key"]] = today
        from src.pokemon import items as _items
        _items.friend_gain(lead, int(sal.get("gain", 5)))
        show(_resolve_lines(game, lines + [f"Snip, snip... There! {lead.display_name} looks happier already!"]))
        return
    if ev.get("photo"):  # (the Memorial Photo Studio, option B: a picture of your team, kept in your Trainer stats)
        import datetime as _dt
        team = [p.display_name for p in story.player_team if p and not getattr(p, "is_egg", False)]
        story.story_flags.setdefault("photos", []).append({"date": _dt.date.today().isoformat(), "team": team, "place": str(story.current_area_key).split("_CITY")[0].replace("_", " ").title()})
        show(_resolve_lines(game, lines + ["Say cheese! ...Click!", f"A photo of you with {', '.join(team) or 'nobody'}. It's kept in your Trainer stats."]))
        return
    if ev.get("raffle"):  # Goldenrod Dept. Store 6F's Daily Drawing (HGSS): $300 a day; a Berry, a Poke Ball or (rarely) a TM
        import datetime as _dt, random as _rnd
        today = _dt.date.today().isoformat()
        if story.story_flags.get("goldenrod_raffle_day") == today:
            show(["Clerk: You've had today's draw. Please come again tomorrow!"])
            return
        if getattr(story, "money", 0) < 300:
            show(["Clerk: A draw is $300. Do come back when you have it!"])
            return
        story.money -= 300
        story.story_flags["goldenrod_raffle_day"] = today
        roll = _rnd.random()
        from src.pokemon import tms as _tms
        tm_pool = [k for k in ("TM05", "TM03", "TM04", "TM25", "TM17", "TM18") if k in (_tms.all_tms(game) if hasattr(_tms, "all_tms") else [k])]
        item = (_rnd.choice(["ORAN_BERRY", "PECHA_BERRY", "CHERI_BERRY", "RAWST_BERRY", "SITRUS_BERRY", "LUM_BERRY"]) if roll < 0.55 else
                _rnd.choice(["GREAT_BALL", "ULTRA_BALL", "NEST_BALL", "LUXURY_BALL", "QUICK_BALL"]) if roll < 0.9 else _rnd.choice(tm_pool or ["TM05"]))
        story.inventory[item] = story.inventory.get(item, 0) + 1
        from src.pokemon import forms as _forms
        show([f"{game.player_name} paid $300.", "Clerk: Round and round it goes... and the winner is...",
              f"Clerk: {_forms.item_label(item)}! Congratulations!"])
        return
    if ev.get("radio_quiz"):  # Goldenrod Radio Tower's Radio Card quiz: five YES / NO equations in a row (Jordan 11-15)
        if story.inventory.get("RADIO_CARD"):
            show(["Quiz lady: You've already won your Radio Card. Enjoy the shows!"])
            return
        from src.states.systems.yes_no_quiz import YesNoQuizState

        def quiz_done(won):
            if won:
                story.inventory["RADIO_CARD"] = 1
                show(["Quiz lady: Five in a row! Congratulations, you've won a Radio Card!",
                      "Your Pokegear can play the radio now! Tune in from the MENU."])
            else:
                show(["Quiz lady: Oh, so close! Try again any time."])
        game.change_state(YesNoQuizState(game, state, 5, quiz_done))
        return
    if ev.get("buena"):  # Buena's Password (HGSS): tell her today's password from her show, a point a day; prizes along the way
        import datetime as _dt
        from src.world import radio as _radio
        today = _dt.date.today().isoformat()
        if story.story_flags.get("buena_told") == today:
            show(["Buena: You've already told me today's password. Tune in again tomorrow!"])
            return
        if story.story_flags.get("buena_heard") != today:
            show(_resolve_lines(game, lines + ["Buena: Listen to my show on your Pokegear's radio, then come back and tell me the password!"]))
            return
        story.story_flags["buena_told"] = today
        pts = int(story.story_flags.get("buena_points", 0) or 0) + 1
        story.story_flags["buena_points"] = pts
        prizes = {1: ("ULTRA_BALL", 1), 3: ("FULL_HEAL", 2), 5: ("NUGGET", 1), 10: ("RARE_CANDY", 1), 20: ("PP_UP", 1), 30: ("MASTER_BALL", 1)}
        out = [f"Buena: '{_radio.password_today()}'? That's right! Here's a Blue Card point. You have {pts} now!"]
        if pts in prizes:
            item, n = prizes[pts]
            story.inventory[item] = story.inventory.get(item, 0) + n
            from src.pokemon import forms as _forms
            out.append(f"Buena: {pts} points! Here's a prize for you: {_forms.item_label(item)}!")
        show(out)
        return
    if ev.get("primo"):  # Violet City's TV star: a question a day, an Egg for a right answer (HGSS)
        _primo_quiz(state, lines, show)
        return
    if ev.get("primo_next"):
        story.story_flags["primo_eggs"] = int(story.story_flags.get("primo_eggs", 0) or 0) + 1
    if ev.get("trivia"):  # Mossdeep's Hex Maniac: a daily question about one of your badges (Jordan, 11-13)
        _badge_trivia(state, lines, show)
        return
    if ev.get("craft"):  # made from what you bring (Shoal Cave's old man: four Shoal Salt and four Shoal Shells, a Shell Bell)
        cr = ev["craft"]   # {"needs": {item: count}, "gives": item}
        if any(story.inventory.get(k, 0) < n for k, n in cr["needs"].items()):
            show(_resolve_lines(game, ev.get("fail") or ["You don't have everything that's needed yet."]))
            return
        for k, n in cr["needs"].items():
            story.inventory[k] -= n
            if story.inventory[k] <= 0:
                story.inventory.pop(k, None)
        story.inventory[cr["gives"]] = story.inventory.get(cr["gives"], 0) + 1
        from src.pokemon import forms as _forms
        lines.append(f"{game.player_name} received the {_forms.item_label(cr['gives']).upper()}!")
    if ev.get("quiz"):  # HGSS's Dragon Shrine: the Elder's questions, one menu each ({"q", "options", "right"}); answered,
        _run_quiz(state, ev, lines, show)   #  "quiz_flag" is set (and "<quiz_flag>_perfect" when all were right the first time)
        return
    if ev.get("give_badge"):  # a badge given outside its Gym's battle (HGSS: Clair's Rising Badge, at the Dragon Shrine)
        lines += _give_badge(game, ev["give_badge"])
    if ev.get("tutor"):  # a move tutor (Pacifidlog's Explosion man): {"move", "like": a TM move whose learners can learn it too,
        tu = ev["tutor"]   #   "choices": [moves] for a menu (Crystal's Goldenrod tutor), "min_friend": it must love you (Grandma Wilma),
        if ev.get("tutor_repeat"):   #   "coins", "take": items}; you pick which Pokemon learns it (Jordan 11-16)
            _tutor_again(state, ev, show)
            return
        if tu.get("choices"):
            from src.states.systems.pick_list import PickListState
            def chose(mv):
                if mv is None:
                    show(_resolve_lines(game, ev.get("cancel") or ["Come back any time!"]))
                    return
                _tutor_flow(state, dict(tu, move=mv, like=mv), ev, [], show)
            game.change_state(PickListState(game, state, "WHICH MOVE?", [(m.replace("-", " "), m) for m in tu["choices"]], chose))
            return
        _tutor_flow(state, tu, ev, lines, show, flag=flag)
        return
    if ev.get("friend_check"):  # (Goldenrod's friendship checker, HGSS: how your first Pokemon feels about you)
        lead = next((p for p in story.player_team if p and not getattr(p, "is_egg", False)), None)
        f = max(int(getattr(lead, "friendship", 0) or 0), int(getattr(lead, "affection", 0) or 0)) if lead else 0
        name = getattr(lead, "display_name", "Your Pokemon") if lead else "Your Pokemon"
        lines += [f"{name} looks really happy! It must love you a lot." if f >= 200 else
                  f"{name} seems to trust you." if f >= 150 else
                  f"{name} is getting used to you. Keep at it!" if f >= 70 else
                  f"{name} doesn't seem very close to you yet. Treat it kindly!"]
    if ev.get("friend_tm"):  # once a week: Return for a first Pokemon that likes you, Frustration if not (Pacifidlog, Emerald)
        import datetime as _dt
        week = _dt.date.today().isocalendar()[:2]
        key = ev["friend_tm"]
        if story.story_flags.get(key) == list(week):
            show(_resolve_lines(game, ev.get("wait") or ["Come back next week!"]))
            return
        from src.pokemon import evolution as _evo
        lead = next((p for p in story.player_team if p and not getattr(p, "is_egg", False)), None)
        fond = lead is not None and (getattr(lead, "friendship", 0) >= _evo.FRIENDSHIP_CATCHES or getattr(lead, "affection", 0) >= 150)
        tm = (ev.get("tms") or ["HTM27", "HTM21"])[0 if fond else 1]  # (Hoenn's own: Return TM27, Frustration TM21; "tms": a region's own keys)
        story.story_flags[key] = list(week)
        story.inventory[tm] = story.inventory.get(tm, 0) + 1
        lines += ([f"Your {lead.display_name} looks so happy with you. This TM's for you: Return!"] if fond
                  else ["Your Pokemon doesn't seem very close to you... Here, this TM suits it: Frustration."])
        lines.append(f"{game.player_name} received {tm}!")
    if ev.get("swap"):  # a trade of items (Route 124's Treasure Hunter: a Shard for its evolution stone), as often as you like
        have = next((k for k in ev["swap"] if story.inventory.get(k, 0) > 0), None)
        if have is None:
            show(_resolve_lines(game, ev.get("fail") or ["You don't have anything they want."]))
            return
        give = ev["swap"][have]
        story.inventory[have] -= 1
        if story.inventory[have] <= 0:
            story.inventory.pop(have, None)
        story.inventory[give] = story.inventory.get(give, 0) + 1
        from src.pokemon import forms as _forms
        lines.append(f"{game.player_name} traded the {_forms.item_label(have).upper()} for the {_forms.item_label(give).upper()}!")
    if ev.get("judge"):  # the Judge (ORAS's Battle Resort, now at the Frontier): your first Pokemon's potential, from its IVs
        lead = next((p for p in story.player_team if p and not getattr(p, "is_egg", False)), None)
        if lead is not None:
            ivs = getattr(lead, "ivs", None) or {}
            total = sum(ivs.values())
            overall = ("decent" if total <= 90 else "above average" if total <= 120 else "relatively superior" if total <= 150
                       else "outstanding")
            lines.append(f"Hmm... Your {lead.display_name}'s overall potential is {overall}.")
            names = {"HP": "HP", "ATTACK": "Attack", "DEFENSE": "Defense", "SPATK": "Sp. Atk", "SPDEF": "Sp. Def", "SPEED": "Speed"}
            best = max(ivs.values()) if ivs else 0
            tops = [names[k] for k in names if ivs.get(k) == best]
            word = ("It can't be beat!" if best == 31 else "It's fantastic!" if best >= 30 else "It's very good." if best >= 26
                    else "It's pretty good." if best >= 16 else "It's decent." if best >= 1 else "It's no good.")
            lines.append(f"Its best stat{'s are' if len(tops) > 1 else ' is'} {' and '.join(tops)}. {word}")
    if ev.get("badges"):  # Mossdeep's Hex Maniac: she reads your badges
        got = list(story.badges.get(story.get_current_region(), []) or [])
        lines.append(f"You have {len(got)} badge{'s' if len(got) != 1 else ''} here: " + ", ".join(str(b).title() for b in got) + "."
                     if got else "You don't have a single badge from this region yet!")
        if got:
            lines.append("Each one still glows with the strength of the Pokémon that won it with you.")
    if ev.get("block_taste"):  # Mossdeep's husband: the Pokeblock colour your first Pokemon likes, by its type
        lead = next((p for p in story.player_team if p and not getattr(p, "is_egg", False)), None)
        if lead is not None:
            from src.pokemon import contest as _ct
            cat = _ct.move_category((getattr(lead, "types", None) or ["NORMAL"])[0])
            col = {"COOL": "red", "BEAUTY": "blue", "CUTE": "pink", "SMART": "green", "TOUGH": "yellow"}[cat]
            lines.append(f"Hmm... Your {lead.display_name} likes {col} Pokéblocks. I'm sure of it!")
    if ev.get("memory"):  # the Memory Girl (ORAS, outside Lilycove's Pokemon Center): what your lead Pokemon remembers
        lines += _memories(game)
    if ev.get("daily_gift"):  # one a day (Jordan, 11-12: the Weather Institute's receptionist and her weather rocks):
        dg = ev["daily_gift"]  # {"key": its record, "items": [...], "order": true (in turn) or random, "wait": lines}
        import datetime as _dt
        import random as _rnd
        today = _dt.date.today().isoformat()
        rec = dict(story.story_flags.get(dg["key"]) or {"day": "", "n": 0})
        if rec["day"] == today:
            show(_resolve_lines(game, dg.get("wait") or ["Come back tomorrow!"]))
            return
        items = dg["items"]
        item = items[rec["n"] % len(items)] if dg.get("order") else _rnd.choice(items)
        story.inventory[item] = story.inventory.get(item, 0) + dg.get("count", 1)   # (count: two at once, the Berry Master's)
        story.story_flags[dg["key"]] = {"day": today, "n": rec["n"] + 1}
        from src.pokemon import forms as _forms
        lines.append(f"{game.player_name} received the {_forms.item_label(item).upper()}!")
    if ev.get("place") and hasattr(state, "player") and not hasattr(state, "run"):  # (in town: you stand there after: Lavaridge's hot springs)
        state.player = tuple(ev["place"])
        state.anim = 0
        if hasattr(state, "_remember"):
            state._remember()
    for k in ev.get("clear", []):   # (story flags it unsets: the Hall of Fame's, used once per title)
        story.story_flags.pop(k, None)
    if ev.get("choose"):   # (pick one, kept as a story flag: {"flag", "ask", "choices": [{"text", "value"}], "done": [...]} - the Johto
        from src.states.systems.pick_list import PickListState   #  Safari Zone's Area Setup, which of its ten layouts you walk into; 11-16)
        ch = ev["choose"]
        rows = [(o["text"], o["value"]) for o in ch.get("choices", [])]

        def picked(v):
            if v is None:
                show(_resolve_lines(game, ch.get("cancel") or ["Come back any time."]))
                return
            story.story_flags[ch["flag"]] = v
            show(_resolve_lines(game, ch.get("done") or ["All set!"]))
        _say_then(state, lines, lambda: game.change_state(PickListState(game, state, ch.get("ask") or "WHICH ONE?", rows, picked)))
        return
    if ev.get("travel_choices"):   # (a guide who takes you on: [{"text", "to", "requires": [...]}], the ones you may take; Mt. Silver)
        from src.states.systems.pick_list import PickListState
        from src.states.overworld import AreaTransitionState
        can = [(o["text"], o["to"]) for o in ev["travel_choices"] if all(check(c) for c in o.get("requires", []))]
        if not can:
            show(lines or ["..."])
            return

        def go(to):
            if to is None:
                show(_resolve_lines(game, ev.get("cancel") or ["Take care out there."]))
                return
            game.change_state(AreaTransitionState(game, to))
        _say_then(state, lines, lambda: game.change_state(PickListState(game, state, ev.get("ask") or "WHERE TO?", can, go)))
        return
    if ev.get("travel"):  # (and off you go: Fallarbor's rival takes you back to Mauville)
        from src.states.overworld import AreaTransitionState
        to = ev["travel"]
        if to == "@ferry":   # (a ferry's sailor: on to the other port from the one you boarded at, the area's "ferry" map:
            areas = game.loader.area_data.get("STORY_PROGRESSION", {})   # the S.S. Tidal)
            ship = getattr(state, "area_key", None) or story.current_area_key   # (the ship you're walking on: Jordan 11-15, a stale
            if not (areas.get(ship) or {}).get("ferry"):                       #  area key after a reload sent the sailor's trip back to the ship)
                ship = next((k for k, a in areas.items() if isinstance(a, dict) and a.get("ferry") and k in (story.current_area_key, story.last_area_key)), ship)
            ferry = (areas.get(ship) or {}).get("ferry") or {}
            to = ferry.get(story.last_area_key) or ferry.get(story.story_flags.get(f"ferry_from_{ship}"))
            if not to or to == ship:
                to = next((v for v in ferry.values() if v != ship), story.last_area_key)
        game.change_state(AreaTransitionState(game, to, initial_message=lines or None))
        return
    show(lines or ["..."])


def _choose_purify(state, lines, show):
    """Pick a party Pokemon at the Relic Stone. Shadow Pokemon are a variant: nothing is purified
    unless the player picks one."""
    from src.states.systems import PokemonPartyMenuState
    game = state.game
    story = game.story_manager
    if not any(story.is_shadow(p) for p in story.player_team if p):
        show(lines + ["None of the Pokemon with you are Shadow Pokemon."])
        return

    def back(out):
        if hasattr(state, "is_resuming"):
            state.is_resuming = True
        game.change_state(state)
        show(out)

    def picked(i):
        team = story.player_team
        if i >= len(team) or not story.is_shadow(team[i]):
            back(["That Pokemon isn't a Shadow Pokemon. Nothing happened."])
            return
        name = story.purify_slot(i)
        back([f"{name}'s heart opened! It's no longer a Shadow Pokemon."] + _evolve_due(game, [name]))

    game.change_state(PokemonPartyMenuState(game, previous_state=state, context="use_item", on_select=picked,
                                            on_cancel=lambda: back(["You left the Relic Stone."])))


def _evolve_due(game, names):
    """Party Pokemon (by name) whose evolution is already due evolve now. Purified Shadow
    Pokemon are often past their evolution level, and Orre has no battles left to trigger it."""
    from src.pokemon import evolution
    story = game.story_manager
    out = []
    for i, p in enumerate(story.player_team):
        if not p or p.name.upper() not in names:
            continue
        ready = evolution.ready_evolutions(game, p, any_time=True)
        if not ready:
            continue
        entry = story.pick_evolution_branch(ready)
        if "_" in entry:
            continue  # a form evolution: leave it to the usual evolution screen
        new_id = game.name_to_id.get(entry.upper())
        if not new_id:
            continue
        old_name = p.display_name.upper()
        story.player_team[i] = new = story.change_species(p, new_id)
        game.data.add_pokemon(new)
        out.append(f"What? {old_name} evolved into {new.display_name.upper()}!")
    return out


def _start_event_puzzle(state, ev, lines, show):
    """Run an event's puzzle (src/states/gym_puzzles.py). Solved: the event's flag and gifts,
    then its lines. Left or failed: back to the area with its "fail" lines."""
    from src.states.gym_puzzles import GymPuzzleState
    game = state.game
    story = game.story_manager

    def done(solved):
        if hasattr(state, "is_resuming"):
            state.is_resuming = True
        game.change_state(state)
        if not solved:
            show(_resolve_lines(game, ev.get("puzzle_fail") or ["You'll have to try again."]))
            return
        out = list(lines)
        for item, qty in (ev.get("gift_item") or {}).items():
            story.add_item(item, qty)
            out.append(f"{getattr(game, 'player_name', 'You')} received the {forms.item_label(item).upper()}!")
        if ev.get("flag"):
            story.story_flags[ev["flag"]] = True
        show(out or ["..."])

    game.change_state(GymPuzzleState(game, story.current_area_key, ev["puzzle"], done))


def _give_badge(game, badge):
    """The badge into the current region's case (and its HM), with the line that says so."""
    from src.world import hms
    story = game.story_manager
    earned = story.badges.setdefault(story.get_current_region(), [])
    if badge in earned:
        return []
    earned.append(badge)
    hms.give_for_badges(story)
    return [f"{getattr(game, 'player_name', 'You')} received the {badge.replace('_', ' ').title()} Badge!"]


def _run_quiz(state, ev, lines, show):
    """Ask ev["quiz"]'s questions one menu at a time, then show ev["after"] lines (and give ev["give_badge"]).
    Only the first time through counts for "<quiz_flag>_perfect" (HGSS: the Dratini knows Extreme Speed)."""
    from src.states.systems.pick_list import PickListState
    game = state.game
    story = game.story_manager
    qs, right = ev["quiz"], []

    def ask(i):
        if i == len(qs):
            flag = ev.get("quiz_flag") or "quiz_done"
            if not story.story_flags.get(flag):
                story.story_flags[flag + "_perfect"] = all(right)
            story.story_flags[flag] = True
            out = _resolve_lines(game, ev.get("after") or [])
            if ev.get("give_badge"):
                out += _give_badge(game, ev["give_badge"])
            out += _resolve_lines(game, ev.get("after_badge") or [])
            show(out or ["..."])
            return
        q = qs[i]

        def chose(v):
            if v is None:
                show(_resolve_lines(game, ev.get("cancel") or ["Come back when you are ready to answer."]))
                return
            right.append(v == q["right"])
            ask(i + 1)
        game.change_state(PickListState(game, state, q["q"], [(o, k) for k, o in enumerate(q["options"])], chose))

    say = getattr(state, "show_message", None) or getattr(state, "show_dialogue", None)
    if lines and say:
        say(lines, callback=lambda: ask(0))
    else:
        ask(0)


def _tutor_price(game, move):
    """What a tutor asks to teach a move again (Jordan 11-16: "an appropriate relative cost"), beside the TMs' $3000: support
    moves $1500, up to 70 power $2000, fixed-damage moves (Seismic Toss) $2500, up to 90 $3000, up to 120 $4000, stronger $6000."""
    try:
        import json as _json, os as _os
        d = _json.load(open(_os.path.join("assets", "moves.json"), encoding="utf-8")).get(move) or {}
    except (OSError, ValueError):
        d = {}
    power = int(d.get("power") or 0)
    if str(d.get("category", "")).upper() == "STATUS":
        return 1500
    if power == 0:
        return 2500
    return 2000 if power <= 70 else 3000 if power <= 90 else 4000 if power <= 120 else 6000


def _say_then(state, lines, then):
    say = getattr(state, "show_message", None) or getattr(state, "show_dialogue", None)
    if lines and say:
        say(lines, callback=then)
    else:
        then()


def _tutor_flow(state, tu, ev, head, show, flag=None, price=0):
    """Teach tu["move"]: you pick which of the Pokemon that can learn it (nobody: the "fail" lines, and a once-only tutor
    isn't used up), then pay `price` (money) and what tu["take"] asks for."""
    from src.states.systems.pick_list import PickListState
    game = state.game
    story = game.story_manager
    can, fail = _tutor_candidates(game, tu, ev)
    if fail:
        if flag:
            story.story_flags.pop(flag, None)
        show(_resolve_lines(game, fail))
        return

    def go(who):
        if who is None:
            if flag:
                story.story_flags.pop(flag, None)
            show(_resolve_lines(game, ev.get("cancel") or ["Come back any time!"]))
            return
        out = _tutor_teach(game, tu, ev, who=who)
        if out and out[0] == "\x00fail":
            if flag:
                story.story_flags.pop(flag, None)
            show(_resolve_lines(game, out[1:]))
            return
        if price:
            story.money -= price
            out = [f"{getattr(game, 'player_name', 'You')} paid ${price:,}."] + out
        for item, qty in (tu.get("take") or {}).items():   # (what they want for it, taken once it's taught: Copycat's Poke Doll)
            story.inventory[item] = max(0, story.inventory.get(item, 0) - qty)
        show((list(head) if len(can) == 1 else []) + out)

    if len(can) == 1:
        go(can[0])
        return
    pick = lambda: game.change_state(PickListState(game, state, "WHO SHOULD LEARN " + tu["move"].replace("-", " ") + "?",
                                                   [(f"{p.display_name} Lv{p.level}", i) for i, p in enumerate(can)],
                                                   lambda i: go(None if i is None else can[i])))
    _say_then(state, list(head), pick)


def _tutor_again(state, ev, show):
    """A tutor who has taught their move already (FireRed's teach once): again, to any Pokemon, for money."""
    from src.states.systems.pick_list import PickListState
    game = state.game
    story = game.story_manager
    tu = dict(ev["tutor"])
    tu.pop("take", None)   # (Copycat wants a doll once; after that, money like the rest)
    move = tu["move"].replace("-", " ").title()
    price = int(ev.get("repeat_price") or tu.get("price") or _tutor_price(game, tu["move"]))
    lines = _resolve_lines(game, ev.get("done") or []) + [f"I can teach {move} again, to any Pokemon that can learn it. That'll be ${price:,}."]

    def answer(yes):
        if not yes:
            show(["Come back any time!"])
            return
        if getattr(story, "money", 0) < price:
            show([f"${price:,}, please... You don't have enough money right now."])
            return
        _tutor_flow(state, tu, ev, [], show, price=price)

    _say_then(state, lines, lambda: game.change_state(PickListState(game, state, f"TEACH {move.upper()} FOR ${price:,}?",
                                                                     [(f"Yes, pay ${price:,}", True)], answer)))


def _tutor_candidates(game, tu, ev):
    """(the party Pokemon that can learn tu["move"] now, None), or ([], the lines saying why nobody can)."""
    import json as _json, os as _os
    from src.pokemon import moves as _mv
    story = game.story_manager
    try:
        learners = set(_json.load(open(_os.path.join("assets", "tm_learners.json"), encoding="utf-8")).get(tu.get("like") or tu["move"], []))
    except (OSError, ValueError):
        learners = set()
    can = [p for p in story.player_team if p and not getattr(p, "is_egg", False)
           and (int(p.id) in learners or str(p.id) in learners or tu["move"] in _mv.learnable(game, p))
           and tu["move"] not in (_mv.move_pool(game, p) or [])]
    if tu.get("min_friend"):
        close = [p for p in can if max(int(getattr(p, "friendship", 0) or 0), int(getattr(p, "affection", 0) or 0)) >= int(tu["min_friend"])]
        if can and not close:
            return [], list(ev.get("not_close") or ["That Pokemon could learn it, but it doesn't trust you enough yet. Come back when you're closer!"])
        can = close
    if not can:
        return [], list(ev.get("fail") or ["None of your Pokemon can learn it right now."])
    return can, None


def _tutor_teach(game, tu, ev, who=None):
    """Teach tu["move"] to `who` (else the first party Pokemon that can learn it): its lines, or [FAILMARK, ...] when nobody can."""
    from src.pokemon import moves as _mv
    story = game.story_manager
    can, fail = _tutor_candidates(game, tu, ev)
    if fail:
        return ["\x00fail"] + fail
    if tu.get("coins"):   # (Crystal's Goldenrod tutor: Game Corner coins, 4000 a move)
        from src.states import game_corner as _gc
        if _gc.coins(story) < int(tu["coins"]):
            return ["\x00fail", f"That'll be {tu['coins']} coins... You only have {_gc.coins(story)}. Win some at the Game Corner first!"]
        _gc.add_coins(story, -int(tu["coins"]))
    who = who if who in can else can[0]
    _mv.move_pool(game, who).append(tu["move"])
    if len(who.moves) < _mv.MAX_MOVES:
        who.moves.append(tu["move"])
    return [f"{who.display_name.upper()} learned {tu['move'].replace('-', ' ')}! (Set its moves in the Summary.)"]


def _teach_move(game, teach):
    """A move tutor: {species id: move} for the first party Pokemon that can learn one."""
    from src.pokemon import moves as movelib
    for p in game.story_manager.player_team if teach else []:
        move = teach.get(str(p.id))
        pool = movelib.move_pool(game, p) if move else []
        if not move or move in pool:
            continue
        label = move.replace("-", " ")
        pool.append(move)  # it joins the move pool; the player sets it in the Summary
        if len(p.moves) < movelib.MAX_MOVES:
            p.moves.append(move)
            return [f"{p.display_name.upper()} learned {label}!"]
        return [f"{p.display_name.upper()} learned {label}! Set its moves in the Summary."]
    return []



HUD_INFO_Y = 128  # the season / Repel / Journal lines start under the MENU button


def _draw_season_hud(game, screen, area_key, x, y=HUD_INFO_Y):
    """Season and today's weather, Repel and the tracked Journal mission, stacked under the MENU
    button (top left) on a soft dark panel so they read on any background."""
    lines = []
    label = seasons.hud_label(game, area_key)
    if label:
        lines.append(label)
    if getattr(game.story_manager, "repel_routes", 0) > 0:
        lines.append((f"Repel: {game.story_manager.repel_routes} routes left", WHITE))
    lines += [(line, GOLD) for line in guide.cached(game, "hud")]  # where to go next
    if not lines:
        return
    font = game.assets.fonts["small"]
    lh = font.get_linesize() + 4
    panel = pygame.Rect(x - 10, y - 6, max(font.size(t)[0] for t, _ in lines) + 24, lh * len(lines) + 10)
    shade = pygame.Surface(panel.size, pygame.SRCALPHA)
    pygame.draw.rect(shade, (16, 20, 36, 150), shade.get_rect(), border_radius=10)
    screen.blit(shade, panel)
    for text, color in lines:
        Utils.draw_text_outline(screen, text, font, color, x, y, align="left", outline_color=BLACK)
        y += lh
