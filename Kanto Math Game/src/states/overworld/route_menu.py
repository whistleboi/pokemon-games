"""The route screen's menus: the EXPLORE / TRAVEL buttons, their conditions, zones, and leaving."""

import pygame
import random
from src.ui.panels import CityActionMenu, CommandButton
from src.ui import theme
from src.world import guide
from src.pokemon import catching
from src.world import story_events
from src.states.overworld.common import TRAVEL_COLOR, _fill_names, _resolve_lines, travel_label


class RouteActionMenu(CityActionMenu):
    """A route's EXPLORE / PKDEX / POKeMON / TRAVEL: the town menu, with the route's words."""

    def __init__(self, game, lines, **callbacks):
        super().__init__(game, "", **callbacks)
        self.lines = lines

    def prompt_lines(self):
        return self.lines


class RouteMenu:
    """Part of PlayState (route.py): its menus."""

    # Zones (Jordan, 11-01): a big area in parts, each with its own picture (Galar's Wild Areas, the
    # Isle of Armor, the Crown Tundra). The area's "zones" list [{"key", "name"}]; a ZONE item in its
    # route_menu becomes a TO <zone> button (under TRAVEL) for each other zone; the zone you're in is
    # kept (zone_<AREA> flag). Its picture is routes/<area>_<zone key>.png, else the area's.
    def _zones(self):
        return self.area_data.get("zones") or []

    def _zone(self):
        zones = self._zones()
        here = self.game.story_manager.story_flags.get(f"zone_{self.game.story_manager.current_area_key}")
        return next((z for z in zones if z.get("key") == here), zones[0] if zones else None)

    def _in_zone(self, item):
        """A menu item or trainer that belongs to one zone ("zone": key or [keys]) shows only there."""
        want = item.get("zone") if isinstance(item, dict) else None
        if not want:
            return True
        here = self._zone()
        return bool(here) and here.get("key") in (want if isinstance(want, list) else [want])

    def _zone_mood(self):
        """A line about the place ("zone_moods": the Pokemon Tower's haunting presence, any of a list;
        or one line per zone, {zone key: line}, the Seafoam Islands' floors), or None."""
        moods = self.area_data.get("zone_moods") or []
        if isinstance(moods, dict):
            here = self._zone()
            return moods.get(here.get("key")) if here else None
        return random.choice(moods) if moods else None

    def _zone_climbs(self, frm, to):
        """True if going from zone frm to zone to is up the stairs: the list goes up a tower, or down
        into a cave ("zones_descend": the Seafoam Islands, 1F to B4F)."""
        zones = self._zones()
        later = zones.index(to) > zones.index(frm)
        return later != bool(self.area_data.get("zones_descend"))

    def action_switch_zone(self, key):
        zones = self._zones()
        here = self._zone()
        nxt = next((z for z in zones if z.get("key") == key), None)
        if not nxt:
            return
        story = self.game.story_manager
        story.story_flags[f"zone_{story.current_area_key}"] = nxt["key"]
        self.route_bg = self._load_route_background()
        self.is_progression_paused = True
        self.hide_menu_buttons()
        if self.area_data.get("zones_linear"):  # floors: up or down the stairs
            up = self._zone_climbs(here, nxt)
            down = "You go down the stairs to" if self.area_data.get("zones_descend") else "You go back down to"
            lines = [f"You climb the stairs to {nxt['name']}." if up else f"{down} {nxt['name']}."]
        else:
            lines = [f"You head over to {nxt['name']}."]
        # A wandering boss can ambush you between zones (the Black Fog in the Pokemon Tower), until beaten.
        ambush = self.area_data.get("zone_ambush") or {}
        boss = ambush.get("boss")
        if boss and not story.story_flags.get(boss.get("victory_flag")) and random.random() < ambush.get("chance", 0.25):
            self.show_dialogue(lines + _resolve_lines(self.game, ambush.get("lines") or []),
                               callback=lambda b=boss: self.action_challenge_boss(b))
            return
        mood = self._zone_mood()
        self.show_dialogue(lines + ([mood] if mood else []), callback=self.show_progression_menu)

    # Jordan (10-29): trying to leave a route before it's done can bring an ambush on the way out.
    EXIT_AMBUSH_CHANCE = 0.4

    ROUTE_DONE_CONDITIONS = ("can_exit", "no_trainers")

    def _exit_block(self, item, trainers_left):
        """None (open), "route" (only the route's own actions are left), "story" (a badge, an HM,
        an item or a story step is missing) or "hidden" (another version's exit, or one that's gone)."""
        fc = item.get("flag_condition")
        flags = self.game.story_manager.story_flags
        if fc:
            parts = fc.split()
            if parts[0] == "not" and len(parts) == 2:
                if flags.get(parts[1]):
                    return "hidden"
        cond = item.get("condition")
        conds = cond if isinstance(cond, list) else [cond] if cond else []
        failing = [c for c in conds if not self._check_route_condition(c, trainers_left, item)]
        if any(isinstance(c, str) and c.startswith("hoenn_version:") for c in failing):
            return "hidden"
        if fc and fc.split()[0] != "not" and not flags.get(fc.split()[0]):
            failing.append(fc.split()[0])
        if not failing:
            return None
        if all(c in self.ROUTE_DONE_CONDITIONS for c in failing):
            return "route"
        return "story"

    def _exit_ambush(self, item):
        """A way out that only waits on this route's own catches and battles: sometimes a trainer
        (half the time, while any are left) or a wild Pokemon jumps out; otherwise say what's left."""
        story = self.game.story_manager
        area = story.current_area_key
        pool = self.area_data.get("trainer_pool", [])
        trainers = any(not story.is_trainer_defeated(area, i) for i in range(len(pool)))
        wild = bool(self._get_wild_pool(self.area_data))
        if random.random() < self.EXIT_AMBUSH_CHANCE and (trainers or wild):
            # Get through the ambush and you're on your way (Jordan, 10-29).
            story.ambush_exit = {"area": area, "exit": {k: v for k, v in item.items() if k != "exit_block"}}
            if trainers and (not wild or random.random() < 0.5):
                self.show_dialogue(["A trainer stops you on your way out!"], callback=self.action_search_trainer)
            else:
                self.show_dialogue(["A wild Pokémon jumps out as you try to leave!"], callback=self.action_battle_wild)
            return
        name = self.area_data.get("route_name", area.replace("_", " ").title())
        left = max(1, self.min_rounds - self.rounds_completed)
        if trainers and any(c == "no_trainers" for c in (item.get("condition") if isinstance(item.get("condition"), list)
                                                        else [item.get("condition")])):
            line = "Beat the trainers here first!"
        else:
            line = f"Explore a little more first: {left} more {'catches or battles' if left > 1 else 'catch or battle'}."
        self.show_dialogue([f"You can't leave {name} yet!", line], callback=self.show_progression_menu)

    def _exit_locked(self, item):
        """A way out that waits on the story: say what's needed."""
        story = self.game.story_manager
        lines = item.get("locked_text")
        if not lines:
            cond = item.get("condition")
            conds = cond if isinstance(cond, list) else [cond] if cond else []
            pool = self.area_data.get("trainer_pool", [])
            left = any(not story.is_trainer_defeated(story.current_area_key, i) for i in range(len(pool)))
            failing = [c for c in conds if not self._check_route_condition(c, left, item)
                       and c not in self.ROUTE_DONE_CONDITIONS]
            fc = item.get("flag_condition")
            if fc and fc.split()[0] != "not" and not story.story_flags.get(fc.split()[0]):
                failing.append(fc.split()[0])
            lines = [self._need_line(c) for c in failing[:2]] or ["The way is blocked for now."]
        lines = lines if isinstance(lines, list) else [lines]
        self.show_dialogue(lines, callback=self.show_progression_menu)

    def _need_line(self, c):
        """What a failed exit condition asks of the player, in words."""
        import re as _re
        prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        c = str(c)
        if c.startswith("has_item:HM_") or c.startswith("has_HM_"):
            move = c.split("HM_", 1)[1].replace("_", " ").title()
            return f"You need HM {move} to go this way."
        if c.startswith("has_item:"):
            return f"You need the {c.split(':', 1)[1].replace('_', ' ').title()} to go this way."
        if c in ("has_8_kanto_badges", "has_8_badges"):
            return "You need all eight badges to go this way."
        m = _re.match(r"has_(\w+?)_?badge$", c)
        if m:
            name = m.group(1).replace("_", " ").title()
            return f"You need the {name} to go this way." if name.endswith(" Z") else                 f"You need the {name} Badge to go this way."  # Alola's trials give Z-Crystals
        if c.startswith("beat_") and c.endswith("_champion") or c == "beat_alder":
            return "This way opens once you become the Champion."
        if c.startswith("visited_"):
            where = prog.get(c[8:], {}).get("route_name") or c[8:].replace("_", " ").title()
            return f"You need to visit {where} first."
        if c.endswith("boss_defeated"):
            return "Something blocks the way. Deal with it first!"
        missions = [m for m in self.game.story_manager.get_active_missions() if m.get("type") == "MAIN"]
        if missions:
            return f"Something still blocks the way. Your Journal says: {missions[0]['text']}."
        return "Something still blocks the way. Keep following the story!"

    def _why_disabled(self, condition):
        """A greyed route button says why it can't be used yet."""
        story = self.game.story_manager
        if condition == "has_balls":
            if not story.catch_unlocked():
                prof = story.get_region_start(story.get_current_region()).get("professor", "the professor")
                line = f"You can't catch Pokémon yet! Get a Pokédex and Poké Balls from {prof} first."
            else:
                line = "You're out of Poké Balls! Buy more at a Poké Mart."
        else:
            line = "There are no trainers left to battle here."
        self.show_dialogue([line], callback=self.show_progression_menu)

    def _leave_after_ambush(self):
        """Back from an exit ambush with a Pokemon still standing: carry on out that way."""
        story = self.game.story_manager
        pending = getattr(story, "ambush_exit", None)
        if not pending:
            return False
        story.ambush_exit = None
        if pending.get("area") != story.current_area_key or not any(p and p.current_hp > 0 for p in story.player_team):
            return False  # whited out (or somewhere else now): the way out waits
        callback = self._get_route_callback(pending["exit"])
        if not callback:
            return False
        callback()
        return True

    def show_progression_menu(self):
        if self._leave_after_ambush():
            return
        self.is_progression_paused = True
        self.dialogue_box.visible = False
        # The menu means no wild encounter is on: the last round's Pokemon leave the screen (they used
        # to stay drawn after CATCH's three rounds, untappable, even up the Pokemon Tower's stairs).
        self.p_data = [None] * 3
        self.selected_catch_idx = -1
        self.catch_selection_active = False

        area_key = self.game.story_manager.current_area_key
        trainer_pool = self.area_data.get("trainer_pool", [])
        trainers_left = any(  # (in a zoned place, the trainers in this zone)
            not self.game.story_manager.is_trainer_defeated(area_key, i) and self._in_zone(trainer_pool[i])
            for i in range(len(trainer_pool))
        )
        self._mark_route_progress(trainers_left)

        default_menu = [
            {"text": "CATCH WILD PKMN", "action": "CATCH", "condition": "has_balls", "color": "BLUE"},
            {"text": "LOOK FOR TRAINER", "action": "TRAINER", "condition": "has_trainers", "color": "BLUE"},
            {"text": "BATTLE WILD PKMN", "action": "BATTLE", "condition": "has_balls", "color": "GREEN"},
            {"text": "EXIT ROUTE", "action": "EXIT", "condition": "can_exit", "color": "RED"}
        ]

        menu_config = [i for i in self.area_data.get("route_menu", default_menu) if self._in_zone(i)]

        self.hide_menu_buttons()

        valid_options = []
        flags = self.game.story_manager.story_flags
        for item in menu_config:
            condition = item.get("condition")
            action = item.get("action")
            flag_condition = item.get("flag_condition")
            if action in ("EXIT", "TRAVEL") and self.area_data.get("area_type") != "town":
                block = self._exit_block(item, trainers_left)
                if block != "hidden":
                    valid_options.append(dict(item, exit_block=block) if block else item)
                continue
            if flag_condition:
                parts = flag_condition.split()
                if parts[0] == "not" and len(parts) == 2:
                    if flags.get(parts[1]):
                        continue
                elif not flags.get(parts[0]):
                    continue

            if action == "BATTLE":
                valid_options.append(item)
                continue

            if action == "BOSS" and flags.get(f"legend_rematch_{self._boss_flag_for(item)}"):
                valid_options.append(item)  # a beaten legendary that got away: rematch until caught
                continue

            if condition in ["has_balls", "has_trainers"] and not self._check_route_condition(condition, trainers_left, item):
                item_copy = item.copy()
                item_copy["disabled"] = True
                item_copy["color"] = "GRAY"
                valid_options.append(item_copy)
            elif self._check_route_condition(condition, trainers_left, item):
                valid_options.append(item)

        if not valid_options:
            if self.rounds_completed >= self.min_rounds or not trainers_left:
                valid_options.append({"text": "EXIT ROUTE", "action": "EXIT", "color": "RED"})
        here = self._zone()
        zones = self._zones()
        if self.area_data.get("zones_linear") and here:  # floors: only the ones up and down the stairs
            i = zones.index(here)
            near = [(o, "UP TO" if self._zone_climbs(here, o) else "DOWN TO") for j, o in enumerate(zones)
                    if abs(j - i) == 1]
        else:
            near = [(o, "TO") for o in zones if o is not here]
        valid_options = [z for item in valid_options for z in (
            [dict(item, to_zone=o["key"], text=f"{word} {o['name'].upper()}") for o, word in near]
            if item.get("action") == "ZONE" else [item])]  # "TO LAKE MILOCH", "UP TO 2F"

        for item in valid_options:
            color_map = {  # the battle menu's colours (src/ui/theme.py)
                "BLUE": theme.RUN, "GREEN": theme.POKEMON, "RED": theme.FIGHT, "ORANGE": (232, 132, 40),
                "GOLD": theme.BAG, "PURPLE": theme.MEGA, "GRAY": (120, 124, 144), "CYAN": (40, 170, 200)
            }
            way_out = item.get("action") in ("EXIT", "TRAVEL")
            bg_color = color_map.get(TRAVEL_COLOR if way_out and item.get("target_area") or way_out and item.get("target")
                                     else item.get("color", "BLUE"), theme.RUN)
            toward = way_out and (item.get("target_area") or item.get("target")) == guide.cached(self.game, "hop")
            if not way_out and not item.get("disabled") and guide.advances_goal(
                    self.game, self.game.story_manager.current_area_key, item):
                toward = True  # the battle or event the tracked Journal mission needs
            if toward:  # the way to the tracked Journal mission
                bg_color = theme.BAG

            callback = self._get_route_callback(item)
            if item.get("disabled"):
                callback = (lambda c=item.get("condition"): self._why_disabled(c))
            if item.get("exit_block") == "route":  # not done here yet: a chance of an ambush on the way out
                callback = (lambda i=item: self._exit_ambush(i))
            elif item.get("exit_block") == "story":  # say what has to happen first
                callback = (lambda i=item: self._exit_locked(i))
                bg_color = (120, 124, 144)

            words = travel_label(self.game, item) if way_out and (item.get("target_area") or item.get("target"))                 else _fill_names(self.game, item["text"])  # "BATTLE {rival_name}"
            label = ("> " if toward else "") + theme.pokemon_word(words)
            btn = CommandButton(pygame.Rect(0, 0, 330, 60), label, self.game.assets.fonts["label"],
                                self._route_pick(callback), bg_color=bg_color, autosize=False)
            # Zones are ways to go (TRAVEL), but floors of one building are explored (EXPLORE: the tower's
            # stairs), and so are the areas of one Safari Zone ("zones_explore").
            zone_travel = item.get("action") == "ZONE" and not (self.area_data.get("zones_linear")
                                                                or self.area_data.get("zones_explore"))
            btn.route_group = "travel" if way_out or zone_travel else "explore"
            self.route_buttons.append(btn)

        # Jordan (10-29): routes use the towns' menu: EXPLORE (catching, battles, trainers, fishing,
        # story events) and TRAVEL (the ways out) open pop-ups, beside PKDEX and POKeMON.
        self.route_popup = None
        self.route_action_menu = RouteActionMenu(
            self.game, self._route_prompt(),
            on_explore=lambda: self.toggle_route_popup("explore"), on_pkdex=self._open_pokedex,
            on_pkmn=self._open_party, on_travel=lambda: self.toggle_route_popup("travel"))
        self.game.ui_manager.add_element(self.route_action_menu)
        self.input_delay = 20

    def _mark_route_progress(self, trainers_left):
        """Story steps that are done once every trainer here is beaten (the route menu and the dungeon map).
        Every trainer in the area, not only this zone's (Silph Co.'s floors)."""
        story = self.game.story_manager
        pool = self.area_data.get("trainer_pool", [])
        if trainers_left or any(not story.is_trainer_defeated(story.current_area_key, i) for i in range(len(pool))):
            return
        # Nugget Bridge (Jordan, 11-03): a story step; both ways off the bridge wait until every trainer
        # on it is beaten (one at a time: rest and use items in between).
        if story.current_area_key == "KANTO_ROUTE_24":
            story.story_flags["nugget_bridge_cleared"] = True
        if self.area_data.get("cleared_flag") and self.area_data.get("trainer_pool"):  # (Silph Co.)
            story.story_flags[self.area_data["cleared_flag"]] = True
        # A gauntlet (the S.S. Anne's cabins): its "not <flag>" is set once its trainers are all beaten.
        if self.area_data.get("trainer_pool"):
            for item in self.area_data.get("route_menu", []):
                parts = str(item.get("flag_condition") or "").split()
                if item.get("action") == "GALACTIC_GAUNTLET" and len(parts) == 2 and parts[0] == "not":
                    story.story_flags[parts[1]] = True

    def _check_route_condition(self, condition, trainers_left, item=None):
        if not condition:
            return True

        if isinstance(condition, (list, tuple)):
            return all(self._check_route_condition(c, trainers_left, item) for c in condition)
        if isinstance(condition, dict) and "any" in condition:  # {"any": [...]}: one is enough
            return any(self._check_route_condition(c, trainers_left, item) for c in condition["any"])
        if isinstance(condition, str) and condition.startswith("not:"):
            return not self._check_route_condition(condition[4:], trainers_left, item)

        if isinstance(condition, str) and condition.startswith("has_item:"):
            return self.game.story_manager.inventory.get(condition[9:], 0) > 0
        if isinstance(condition, str) and condition.replace(" ", "").startswith("badges_less:"):
            # "badges_less: N": fewer than N badges in this region (Route 22's early rival)
            story = self.game.story_manager
            need = int(condition.split(":", 1)[1])
            return len(story.badges.get(story.get_current_region(), [])) < need
        if condition == "has_balls":  # any ball (Hoenn: no catching before Birch's Pokedex)
            return catching.total_balls(self.game.story_manager) > 0 and self.game.story_manager.catch_unlocked()
        if condition == "has_SQUIRT_BOTTLE":
            return self.game.story_manager.inventory.get("SQUIRT_BOTTLE", 0) > 0 and not self.game.story_manager.story_flags.get("defeated_sudowoodo")
        if condition == "has_stormbadge":
            return self.game.story_manager.has_badge("STORMBADGE")
        if condition == "has_glacier_badge":
            return self.game.story_manager.has_badge("GLACIER")
        if condition == "has_trainers":
            return trainers_left
        if condition == "no_trainers":
            return not trainers_left
        if condition == "can_headbutt":
            has_helmet = self.game.story_manager.inventory.get("ROCKY_HELMET", 0) > 0
            return has_helmet and self.area_data.get("has_trees", False)
        if condition == "can_fish":
            inv = self.game.story_manager.inventory
            has_rod = any(inv.get(r, 0) > 0 for r in ("OLD_ROD", "GOOD_ROD", "SUPER_ROD"))
            return has_rod and self.area_data.get("can_fish", False)
        if condition == "can_battle":
            return True
        if condition == "has_EON_TICKET":
            return self.game.story_manager.inventory.get("EON_TICKET", 0) > 0
        if condition == "can_dive":
             return self.area_data.get("battle_type") == "ocean" and self.game.story_manager.inventory.get("DIVE_GEAR", 0) > 0

        if condition == "mew_available":
            has_spotted = (self.game.story_manager.story_flags.get("mew_spotted_mt_moon", False)
                           and self.game.story_manager.kanto_caught_count() >= 150)
            has_caught = self.game.story_manager.story_flags.get("caught_mew", False)
            return has_spotted and not has_caught and not trainers_left

        if condition == "can_battle_red_gyarados":
            # As in the games: the Red Gyarados comes first, then Lance and the Rocket Hideout.
            boss_beaten = self.game.story_manager.story_flags.get("defeated_red_gyarados", False)
            return not boss_beaten and not trainers_left

        if condition == "can_exit":
            if self.area_data.get("area_type") == "town":
                return True
            if catching.total_balls(self.game.story_manager) <= 0:
                return True
            if self.rounds_completed >= self.min_rounds:
                return True
            # Nothing left to play here: no wild battles on the menu and every trainer beaten
            # (the Radio Tower cleared over two visits used to leave no way out).
            wild = any(o.get("action") in ("CATCH", "BATTLE") for o in self.area_data.get("route_menu", []))
            return not wild and not trainers_left

        if condition == "has_silph_scope":
            return self.game.story_manager.inventory.get("SILPH_SCOPE", 0) > 0
        if condition == "has_rainbow_wing":
            return self.game.story_manager.inventory.get("RAINBOW_WING", 0) > 0
        if condition == "has_8_badges":
            return sum(len(b) for b in self.game.story_manager.badges.values()) >= 8
        if condition == "has_8_kanto_badges":
            kanto_badges = {"BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"}
            player_badges = set(self.game.story_manager.badges.get("KANTO", []))
            return kanto_badges.issubset(player_badges)
        if condition == "has_8_johto_badges":
            johto_badges = {"ZEPHYR", "HIVE", "PLAIN", "FOG", "STORMBADGE", "MINERAL", "GLACIER", "RISING"}
            player_badges = set(self.game.story_manager.badges.get("JOHTO", []))
            return johto_badges.issubset(player_badges)

        if condition.startswith("has_") and condition.endswith("_badge"):
            from src.world.hms import _norm
            want = _norm(condition[4:-6])  # case and "_BADGE" don't matter ("KNuckle", "COAL_BADGE")
            story = self.game.story_manager
            # This region's badges: Galar's and Paldea's Grass Badges are different badges.
            return any(_norm(b) == want for b in story.badges.get(story.get_current_region(), []))

        special = self.game.story_manager.special_condition(condition)
        if special is not None:  # party_has:493, all_unown_registered
            return special
        if isinstance(condition, str) and condition.startswith("caught_range:"):
            lo, hi = (int(x) for x in condition.split(":", 1)[1].split("-"))
            return self.game.story_manager.caught_in_range(lo, hi) >= hi - lo + 1  # e.g. all of #1-251
        if condition == "boss_defeated":
            boss_data = self.area_data.get("area_boss", {})
            victory_flag = boss_data.get("victory_flag")

            if victory_flag:
                return self.game.story_manager.story_flags.get(victory_flag, False)
            default_flag = f"{self.game.story_manager.current_area_key}_boss_defeated"
            return self.game.story_manager.story_flags.get(default_flag, False)
        if condition == "shadows_left":  # Orre: a Shadow Pokemon here not yet snagged
            return self._next_shadow() is not None
        if condition == "shadows_cleared":  # every Shadow Pokemon here snagged: Cipher's stragglers
            return bool(self.area_data.get("shadow_pool")) and self._next_shadow() is None

        if condition == "boss_available":
            is_defeated = self._check_route_condition("boss_defeated", trainers_left)
            if is_defeated or trainers_left:
                return False

            if item and item.get("has_SILPH_SCOPE"):
                if self.game.story_manager.inventory.get("SILPH_SCOPE", 0) <= 0:
                    return False
            return True

        if condition == "boss_not_defeated":
            return not self._check_route_condition("boss_defeated", trainers_left, item)
        if condition == "boss_available_with_flute":
            # (FRLG: a Snorlax on Route 12 and another on Route 16; this area's own)
            return (self.game.story_manager.inventory.get("POKE_FLUTE", 0) > 0
                    and not self._check_route_condition("boss_defeated", trainers_left, item))
        if condition == "snorlax_defeated":
            return self.game.story_manager.snorlax_awake()
        if condition == "can_access_route_11":
            has_flute = self.game.story_manager.inventory.get("POKE_FLUTE", 0) > 0
            is_defeated = self.game.story_manager.story_flags.get("KANTO_ROUTE_11_boss_defeated", False)
            return has_flute or is_defeated

        if condition == "dungeon_cleared":
            if not item:
                return False
            areas = item.get("required_areas", [])
            for area in areas:
                a_data = self.game.loader.area_data.get("STORY_PROGRESSION", {}).get(area)
                if not a_data:
                    continue

                t_pool = a_data.get("trainer_pool", [])
                for i in range(len(t_pool)):
                    if not self.game.story_manager.is_trainer_defeated(area, i):
                        return False
            return True
        if condition == "dungeon_boss_available":
            return not self._check_route_condition("boss_defeated", trainers_left) and self._check_route_condition("dungeon_cleared", trainers_left, item)

        if isinstance(condition, str) and condition.startswith("has_")                 and self.game.story_manager.inventory.get(condition[4:].upper(), 0) > 0:
            return True  # "has_silver_wing": holding the SILVER_WING
        if isinstance(condition, str):
            return self.game.story_manager.story_flags.get(condition, False)

        return True

    def _get_route_callback(self, item):
        action = item.get("action")
        if action == "GAME_CORNER":  # the Game Corner's clerk: its games, coins and prizes
            from src.states.systems import GameCornerState
            return lambda: self.game.change_state(GameCornerState(self.game, self))
        if action == "DAYCARE":
            from src.states.daycare import DaycareState
            return lambda: self.game.change_state(DaycareState(self.game, self))
        if action == "CATCH":
            return self.action_search_pokemon
        if action == "TRAINER":
            return self.action_search_trainer
        if action == "BATTLE":
            return self.action_battle_wild
        if action == "BOSS":
            if item.get("boss"):
                return lambda b=item["boss"]: self.action_challenge_boss(b)
            return self.action_challenge_boss
        if action == "HEADBUTT":
            return self.action_headbutt
        if action == "DIVE":
            return self.action_dive
        if action == "FISH":
            return self.action_fish
        if action in ["EXIT", "TRAVEL"]:
            target = item.get("target") or item.get("target_area")
            return lambda t=target: self.action_exit_route(t)
        if action == "GALACTIC_GAUNTLET":
            return self.action_search_trainer
        if action == "MAX_RAID":
            return self.action_max_raid
        if action == "SNAG":
            return lambda: self.action_snag_shadow(repeat=bool(item.get("repeat")))
        if action == "BERRY":
            return self.action_pick_berries
        if action == "WEATHER_DIRECTOR":
            return self.visit_weather_director
        if action == "EVENT":
            return lambda e=item.get("event") or {}: self.story_event(e)
        if action == "CAMP":
            return self.open_camp
        if action == "ZONE":
            return lambda z=item.get("to_zone"): self.action_switch_zone(z)
        if action == "REST":  # a long ride's cabin (the Decolore ferry): a free full heal
            return self.action_rest_in_cabin
        if action == "HOENN_EVENT":
            return lambda e=item.get("event"): self.hoenn_event(e)
        if action == "NPC":
            key = item.get("dialogue") or item.get("target")
            if key in story_events.ROUTE_METHODS:
                return getattr(self, story_events.ROUTE_METHODS[key])
            if story_events.get(key):
                return lambda k=key: self.story_event(k)
            if key in self.game.assets.game_text:
                return lambda k=key, f=item.get("victory_flag"): self._route_npc_text(k, f)
        return lambda: print(f"Unknown action: {action}")

    def hide_menu_buttons(self):
        for btn in self.route_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.route_buttons.clear()
        menu = getattr(self, "route_action_menu", None)
        if menu in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(menu)
        self.route_action_menu = None
        self.route_popup = None
        self.route_popup_rect = None

    def _sync_route_menu(self):
        """A message in the text box (the "can't leave yet" warning, a lock's reason) shows over
        the route menu: the menu steps aside while it's up and comes back after."""
        menu = getattr(self, "route_action_menu", None)
        if menu is None:
            return
        talking = bool(self.dialogue_box.visible)
        menu.visible = not talking
        if talking and getattr(self, "route_popup", None):
            self.close_route_popup()

    def _route_prompt(self):
        """The route menu's words in the text box, as in a town."""
        if self.rounds_completed == 0:
            name = self.area_data.get("route_name", self.game.story_manager.current_area_key.replace("_", " ").title())
            zone = self._zone()
            mood = "A cold black fog is gathering again..." if getattr(self, "fog_returned", False) else None
            return [f"{name}, {zone['name']}" if zone else f"Entered {name}",
                    mood or self._zone_mood() or self.game.assets.get_text("whats_next")]
        return [self.game.assets.get_text("explored_area"), self.game.assets.get_text("whats_next")]

    def _route_pick(self, callback):
        """A pop-up option: close the pop-up, then act."""
        def pick():
            self.close_route_popup()
            if callback:
                callback()
        return pick

    def close_route_popup(self):
        for btn in self.route_buttons:
            if btn in self.game.ui_manager.elements:
                self.game.ui_manager.elements.remove(btn)
        self.route_popup = None
        self.route_popup_rect = None

    def toggle_route_popup(self, group):
        """EXPLORE / TRAVEL: the route's options of that kind in a column above the commands
        (the towns' pop-up). Tapping the same command again closes it."""
        if self.route_popup == group:
            self.close_route_popup()
            return
        self.close_route_popup()
        btns = [b for b in self.route_buttons if getattr(b, "route_group", "") == group]
        if not btns:
            self.show_dialogue(["There's nothing to do here right now." if group == "explore"
                                else "You can't leave this way yet."], callback=self.show_progression_menu)
            return
        font = self.game.assets.fonts["label"]
        btn_w = max(260, max(font.size(b.text)[0] + 50 for b in btns))
        btn_h, gap, pad = 60, 10, 18
        panel = self.route_action_menu.right_rect
        bottom = panel.top - 10
        fit = max(1, (bottom - 90 - pad * 2 + gap) // (btn_h + gap))
        cols = -(-len(btns) // fit)
        rows = -(-len(btns) // cols)
        w = cols * btn_w + (cols - 1) * gap + pad * 2
        h = rows * btn_h + (rows - 1) * gap + pad * 2
        self.route_popup_rect = pygame.Rect(panel.right - 18 - w, bottom - h, w, h)
        for i, b in enumerate(btns):
            col, row = divmod(i, rows)
            b.rect = pygame.Rect(self.route_popup_rect.x + pad + col * (btn_w + gap),
                                 self.route_popup_rect.y + pad + row * (btn_h + gap), btn_w, btn_h)
            b.font = font if font.size(b.text)[0] <= btn_w - 24 else self.game.assets.fonts["tiny"]
            if hasattr(b, "arm"):
                b.arm(250)  # the tap that opened the pop-up can't press an option
            self.game.ui_manager.add_element(b)
        self.route_popup = group

    def action_exit_route(self, target_area=None):
        from src.states.overworld.area_transition import AreaTransitionState
        self.wild_catches_on_route = 0
        if target_area:
            next_area_key = target_area
        else:
            next_area_key = self.game.story_manager.get_current_area_data().get("next_area")

        if not next_area_key:
            next_area_key = self.game.story_manager.current_area_key

        if next_area_key:
            self.game.change_state(AreaTransitionState(self.game, next_area_key))
