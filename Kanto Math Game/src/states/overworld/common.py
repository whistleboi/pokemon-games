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


def _fill_names(game, text):
    if not isinstance(text, str):
        return text
    text = (text.replace("{player_name}", getattr(game, "player_name", "TRAINER"))
                .replace("{rival_name}", getattr(game, "rival_name", "???"))
                .replace("{friend_name}", getattr(game, "friend_name", None) or "???"))
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
    gift = story_events.gift_for_starter(ev.get("gift_pokemon"), _region_starter_id(game))
    if gift:
        lines.append(story_events.gift_pokemon(game, gift, ev.get("gift_level")))
    if flag:
        story.story_flags[flag] = True
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
