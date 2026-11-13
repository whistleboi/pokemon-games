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
    flag = ev.get("flag")
    if flag and story.story_flags.get(flag):
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
        lines.append(story_events.gift_pokemon(game, gift, ev.get("gift_level")))
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
    if ev.get("tutor"):  # a move tutor (Pacifidlog's Explosion man): {"move", "like": a TM move whose learners can learn it too}
        tu = ev["tutor"]
        import json as _json, os as _os
        try:
            learners = set(_json.load(open(_os.path.join("assets", "tm_learners.json"), encoding="utf-8")).get(tu.get("like", ""), []))
        except (OSError, ValueError):
            learners = set()
        from src.pokemon import moves as _mv
        who = next((p for p in story.player_team if p and not getattr(p, "is_egg", False)
                    and (int(p.id) in learners or str(p.id) in learners or tu["move"] in _mv.learnable(game, p))
                    and tu["move"] not in (_mv.move_pool(game, p) or [])), None)
        if who is None:
            show(_resolve_lines(game, ev.get("fail") or ["None of your Pokemon can learn it right now."]))
            return
        _mv.move_pool(game, who).append(tu["move"])
        if len(who.moves) < _mv.MAX_MOVES:
            who.moves.append(tu["move"])
        lines.append(f"{who.display_name.upper()} learned {tu['move'].replace('-', ' ')}! (Set its moves in the Summary.)")
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
        tm = "TM113" if fond else "TM114"
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
    if ev.get("travel"):  # (and off you go: Fallarbor's rival takes you back to Mauville)
        from src.states.overworld import AreaTransitionState
        game.change_state(AreaTransitionState(game, ev["travel"], initial_message=lines or None))
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
