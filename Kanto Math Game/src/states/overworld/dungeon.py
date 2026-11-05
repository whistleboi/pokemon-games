"""Route dungeons (Jordan, 11-05): a route walked on a map, Mystery Dungeon style, instead of the route menu.

Which areas: assets/dungeon_routes.json (Route 1, Route 2 and Viridian Forest to start). The rules
(floors, turns, wild Pokemon that chase you, loot, TM spots) are src/dungeon/core.py; this is the screen.

How the route's actions map onto the walk:
- CATCH WILD PKMN -> bump into a wild Pokemon and pick MATH: one question, a right answer throws a ball
  at the route catch's odds (a wrong one and it runs away). Or HONEY / SWEET SCENT draws three wild
  Pokemon for the usual three-Pokemon catch (the route's own catch screen, then back to the map).
- BATTLE WILD PKMN -> bump into a wild Pokemon and pick BATTLE (the full battle screen).
- BATTLE TRAINER -> bump into a trainer, or walk into one's line of sight.
- Items lie about (the area's loot table), and TM spots hold a TM picked once per save.
- The ways out are signs on the map: where you came in, and the rest in the far rooms (stairs first
  when the area has more than one floor).

DungeonState is a PlayState, so battles, the catch screen, evolutions and the side menus all work as
on a route. PlayState(game) itself hands back a DungeonState for a dungeon area (see PlayState.__new__),
and after a battle the same walk carries on (the battle builds PlayState(game, restore_data)).
Headless (the check suites) the old route screen stays, unless game.dungeon_routes is set.
"""
import json
import math
import os
import random

import pygame

from src.config import FPS
from src.dungeon import core
from src.pokemon import balance, catching, forms, tms
from src.pokemon.data import Pokemon
from src.states.overworld.common import _trainer_sprite, travel_label
from src.states.overworld.route import PlayState
from src.ui import theme
from src.utils import Utils
from src.world import levels

TILE = 56
STEP_FRAMES = 6          # frames a step takes (the walk animation)
MATH_SECONDS = 30
QUICK_SECONDS = 5        # a right answer this fast weakens it to 1 HP (as on the route catch screen)

COLORS = {  # floor, tall grass, wall (trees or rock), wall top
    "field": ((150, 206, 108), (82, 164, 78), (44, 104, 58), (62, 132, 70)),
    "forest": ((118, 160, 92), (64, 132, 66), (24, 72, 44), (38, 94, 54)),
    "cave": ((160, 140, 116), (140, 122, 100), (72, 60, 54), (96, 82, 72)),
}

_recipes = {}


# ---------------------------------------------------------------- which areas, and their recipes
def recipes(game):
    if "all" not in _recipes:
        path = os.path.join(game.assets.assets_dir or "", "dungeon_routes.json")
        try:
            with open(path, encoding="utf-8-sig") as f:
                _recipes["all"] = json.load(f)
        except (OSError, ValueError):
            _recipes["all"] = {}
    return _recipes["all"]


def recipe_for(game, area_key):
    all_ = recipes(game)
    recipe = dict(all_.get("DEFAULT", {}))
    recipe.update(all_.get(area_key, {}))
    return recipe


def enabled(game, area_key):
    all_ = recipes(game)
    if area_key not in all_ or area_key.startswith("_") or area_key == "DEFAULT":
        return False
    if all_[area_key].get("enabled") is False:
        return False
    if not getattr(game, "dungeon_routes", os.environ.get("SDL_VIDEODRIVER") != "dummy"):
        return False
    if getattr(game, "classic_route", None) == area_key:  # CLASSIC VIEW for this visit
        return False
    area = game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})
    return area.get("area_type") != "town"


def dungeon_for(game, restore_data=None):
    """What PlayState(game, restore_data) should be here: the walk going on (back from a battle), a
    new DungeonState (still to be set up), or None for the old route screen."""
    key = game.story_manager.current_area_key
    if getattr(game, "classic_route", None) not in (None, key):
        game.classic_route = None  # CLASSIC VIEW lasts until you leave that area
    if not enabled(game, key):
        return None
    cur = getattr(game, "dungeon_state", None)
    if restore_data and cur is not None and getattr(cur, "area_key", None) == key:
        return cur
    return object.__new__(DungeonState)


# ---------------------------------------------------------------- the screen
class DungeonState(PlayState):

    def __init__(self, game, restore_data=None, classic=False):
        if getattr(self, "_dungeon_ready", False):  # the walk going on, back from a battle
            self._back_from_battle()
            return
        super().__init__(game, restore_data=restore_data, classic=True)
        self._dungeon_ready = True
        story = game.story_manager
        self.area_key = story.current_area_key
        self.recipe = recipe_for(game, self.area_key)
        game.dungeon_state = self

        self.exit_items = {}  # target area -> its route_menu entry (for the sign's name and its locks)
        for item in self.area_data.get("route_menu", []):
            target = item.get("target") or item.get("target_area")
            if item.get("action") in ("EXIT", "TRAVEL") and target and target not in self.exit_items:
                if self._exit_block(item, True) != "hidden":
                    self.exit_items[target] = item
        exits = list(self.exit_items)
        came = getattr(story, "last_area_key", None)
        nxt = self.area_data.get("next_area")
        if came in exits:
            entrance = came
        else:  # (a new game, a load, Fly...): start at the end away from where the route leads
            entrance = next((e for e in exits if e != nxt), exits[0] if exits else None)
        forwards = [e for e in exits if e != entrance] or ([nxt] if nxt else [])

        pool = self.area_data.get("trainer_pool", [])
        trainers = [(i, t) for i, t in enumerate(pool) if not story.is_trainer_defeated(self.area_key, i)]
        spots = [s for s in self.recipe.get("tm_spots", []) if not story.story_flags.get(f"dungeon_tm_{s}")]
        loot = self.recipe.get("loot") or {}
        self.run = core.Run(self.recipe, random.Random(), entrance=entrance, forwards=forwards,
                            make_wild=self._make_wild, trainers=trainers,
                            loot_for=lambda rng: core.roll_loot(rng, loot), tm_spots=spots)

        self.mode = "MAP"          # MAP, CHOICE, MATH, THROW, SPOTTED, CATCH (the route's catch screen)
        self.facing = (0, 1)
        self.anim = 0              # frames left of the step animation
        self.anim_from = self.run.player
        self.walk_goal = None      # a tapped tile you're walking to
        self.encounter = None      # the wild Pokemon or trainer you met
        self.choice = 0            # MATH (0) or BATTLE (1) on the choice cards
        self.math_timer = 0
        self.throw_timer = 0
        self.throw_result = None
        self.spot_timer = 0
        self.pending = None        # ("wild" | "trainer", mover): a battle we're away at
        self.toast, self.toast_timer = "", 0
        self.scent_floor = -1      # the floor Sweet Scent was used on (once a floor)
        self.banner = 150          # the area's name, when you arrive
        self._floor_surf = None
        self._floor_index = -1
        self._sprites = {}

    # ---- keys: the map takes the arrows (the keyboard highlight only works the catch screen)
    @property
    def uses_keyboard(self):
        return getattr(self, "mode", "MAP") != "CATCH"

    # ---------------------------------------------------------------- wild Pokemon
    def _make_wild(self, rng):
        pool = self._get_wild_pool(self.area_data)
        if not pool:
            return None
        pid = int(Utils.weighted_random_choice(pool))
        raw = self.game.loader._fetch_raw(id_pool=[pid], area_data=self.area_data)
        if not raw or raw.get("id", 0) == 0:
            return None
        p = Pokemon(raw, self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, p, self.area_key)
        return p

    # ---------------------------------------------------------------- coming and going
    def start(self):
        for el in [self.dialogue_box] + list(self.hud_buttons) + [self.btn_flee, self.btn_yes, self.btn_no]:
            if el not in self.game.ui_manager.elements:
                self.game.ui_manager.add_element(el)
        if self.mode != "CATCH":
            self.btn_flee.set_visibility(False)
        pygame.event.clear()
        self.game.story_manager.story_flags[f"visited_{self.area_key}"] = True
        self.is_resuming = False

    def _back_from_battle(self):
        """Back on the map after a battle: the wild Pokemon is gone (beaten, caught or left behind),
        a beaten trainer too."""
        kind, mover = self.pending or (None, None)
        self.pending = None
        if mover is not None:
            if kind == "wild":
                self.run.remove(mover)
            elif kind == "trainer":
                idx = mover.payload[0]
                if self.game.story_manager.is_trainer_defeated(self.area_key, idx):
                    self.run.remove(mover)
                else:  # lost (or ran out of Pokemon): it looks away, so you can get past
                    mover.facing = (-mover.facing[0], -mover.facing[1])
        self.encounter = None
        self.mode = "MAP"
        self.walk_goal = None

    def show_progression_menu(self):
        """The route's catch screen (or a battle) is done: back to the map."""
        self.is_progression_paused = True
        self.p_data = [None] * 3
        self.catch_selection_active = False
        self.selected_catch_idx = -1
        self.pause_timer = 0
        self.btn_flee.set_visibility(False)
        self.dialogue_box.visible = False
        self.mode = "MAP"

    def _leave(self, target):
        self.game.dungeon_state = None
        self.action_exit_route(target)

    def _classic(self):
        """CLASSIC VIEW: the old route menu for the rest of this visit."""
        self.game.classic_route = self.area_key
        self.game.dungeon_state = None
        state = PlayState(self.game)
        self.game.states["play"] = state
        self.game.change_state(state)

    # ---------------------------------------------------------------- talking
    def say(self, lines, then=None):
        def done():
            self.dialogue_box.visible = False
            if then:
                then()
        self.dialogue_box.reset(lines if isinstance(lines, list) else [lines])
        self.dialogue_box.callback = done

    def flash(self, text, frames=90):
        self.toast, self.toast_timer = text, frames

    # ---------------------------------------------------------------- a step
    def _ready(self):
        return self.mode == "MAP" and self.anim == 0 and not self.dialogue_box.visible

    def step(self, dx, dy):
        if not self._ready():
            return
        self.facing = (dx, dy)
        before = self.run.player
        events = self.run.step(dx, dy)
        if self.run.player != before:
            self.anim_from, self.anim = before, STEP_FRAMES
        self._handle(events)

    def wait_turn(self):
        if self._ready():
            self._handle(self.run.wait())

    def _handle(self, events):
        for ev in events:
            kind = ev[0]
            if kind == "blocked":
                self.walk_goal = None
            elif kind == "item":
                self._pick_up(ev[1])
            elif kind == "tm":
                self.walk_goal = None
                self._pick_up_tm(ev[1])
            elif kind == "exit":
                self.walk_goal = None
                self._try_exit(ev[1])
                return
            elif kind == "stairs":
                self.walk_goal = None
                self.say(["You found the stairs!", "You went on to the next floor."], then=self._descend)
                return
            elif kind in ("bump", "ambush") and ev[1].kind == "wild":
                self._meet_wild(ev[1])
                return
            elif kind in ("bump", "spotted") and ev[1].kind == "trainer":
                self._meet_trainer(ev[1], spotted=(kind == "spotted"))
                return
        # stop a long walk when a wild Pokemon comes close
        px, py = self.run.player
        if self.walk_goal and any(m.kind == "wild" and m.alert and abs(m.x - px) + abs(m.y - py) <= 3
                                  for m in self.run.floor.movers):
            self.walk_goal = None

    def _descend(self):
        self.run.descend()
        self.anim = 0
        self.anim_from = self.run.player
        self.banner = 120

    def _try_exit(self, target):
        item = self.exit_items.get(target)
        story = self.game.story_manager
        pool = self.area_data.get("trainer_pool", [])
        left = any(not story.is_trainer_defeated(self.area_key, i) for i in range(len(pool)))
        if item is not None and self._exit_block(item, left) == "story":
            self._step_back()
            self._exit_locked(item)  # says what's needed (then show_progression_menu: the map)
            return
        self._leave(target)

    def _step_back(self):
        """Off an exit you can't take yet, back onto the tile you came from."""
        self.run.player = self.anim_from
        self.anim = 0

    # ---- items
    def _pick_up(self, key):
        story = self.game.story_manager
        if key == catching.POKE:
            story.balls_left += 1
            name = "POKE BALL"
        else:
            story.add_item(key)
            name = forms.item_label(key).upper()
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        self.flash(f"You found a {name}!")

    def _pick_up_tm(self, spot):
        story = self.game.story_manager
        seed = story.story_flags.setdefault("dungeon_seed", random.randrange(1 << 30))
        region = story.get_current_region()
        badges = len(story.badges.get(region, []))
        tm = core.pick_tm(seed, spot, tms.table(self.game), tms.owned(story), badges)
        story.story_flags[f"dungeon_tm_{spot}"] = tm or "RARE_CANDY"
        if tm:
            story.add_item(tm)
            lines = [f"You found {tms.label(self.game, tm)}!", "Your Pokemon that can learn it now have the move to pick."]
        else:  # every TM owned already
            story.add_item("RARE_CANDY")
            lines = ["You found a RARE CANDY!"]
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        self.say(lines)

    # ---------------------------------------------------------------- meeting a wild Pokemon
    def _can_catch(self):
        story = self.game.story_manager
        return catching.total_balls(story) > 0 and story.catch_unlocked()

    def _meet_wild(self, mover):
        self.walk_goal = None
        self.encounter = mover
        self.choice = 0 if self._can_catch() else 1
        p = mover.payload
        self.game.data.mark_seen(p.id)
        if p.cry:
            p.cry.play()
        self.mode = "CHOICE"

    def _pick(self, which):
        if which == 0:
            if not self._can_catch():
                story = self.game.story_manager
                if not story.catch_unlocked():
                    self.flash("You can't catch Pokemon yet!")
                else:
                    self.flash("You're out of Poke Balls!")
                return
            self._start_math()
        else:
            self._battle_wild(self.encounter)

    def _start_math(self):
        self.mode = "MATH"
        self.problem_str, self.correct_ans, self.options = self.generate_math_set(self.total_caught, num_options=3)
        self.math_timer = MATH_SECONDS * FPS

    def _answer(self, idx):
        if self.mode != "MATH" or idx >= len(self.options):
            return
        story = self.game.story_manager
        p = self.encounter.payload
        ball = catching.selected(story)
        catching.use(story, ball)
        self._thrown_ball = ball
        right = self.options[idx] == self.correct_ans
        shiny_pass = bool(p.is_shiny) and not right  # a shiny is caught even on a wrong answer (as on the route)
        self.was_shiny_override = shiny_pass
        if right or shiny_pass:
            quick = (MATH_SECONDS * FPS - self.math_timer) < QUICK_SECONDS * FPS
            max_hp = p.get_max_hp()
            roll = catching.window_throw(self.game, p, ball, guaranteed=balance.is_legendary(p.id) or shiny_pass,
                                         hp=1 if quick else max(1, max_hp // 4), max_hp=max_hp,
                                         terrain=self.area_data.get("battle_type", ""))
            self.throw_result = "caught" if roll[0] else "broke"
        else:
            self.current_streak = 0
            self.throw_result = "wrong"
        self.mode, self.throw_timer = "THROW", int(FPS * 1.2)

    def _resolve_throw(self):
        mover, p = self.encounter, self.encounter.payload
        name = p.display_name.upper()
        self.run.remove(mover)
        self.encounter = None
        if self.throw_result == "caught":
            if p.cry:
                p.cry.play()
            self.mode = "MAP"
            self.p_data = [None, p, None]
            self.ball_target = [self.game.width // 2, self.game.height // 2]
            self.complete_catch(1)  # the route's own: party or PC, Pokedex, streak, milestones, save
            catching.after_catch(self.game, p, getattr(self, "_thrown_ball", None))
            self.pause_timer = 0
            self.p_data = [None] * 3
            evolve = self.dialogue_box.callback  # (the route checks for a catch evolution after)
            self.say(self.dialogue_box.text_lines, then=evolve)
            return
        self.mode = "MAP"
        if self.throw_result == "broke":
            self.say([f"Oh no! {name} broke free!", f"{name} ran away!"])
        elif self.throw_result == "timeout":
            self.say([f"Too slow! {name} ran away!"])
        else:
            self.say([f"That's not it! {name} ran away!"])

    def _battle_wild(self, mover):
        from src.states.battle import WildBattleState
        self.pending = ("wild", mover)
        self.mode = "MAP"
        self.rounds_completed += 1
        battle = WildBattleState(self.game, mover.payload, self.area_key,
                                 background_image=self._get_battle_background_for_area())
        battle.play_state_data = self._play_data()
        pygame.event.clear()
        self.game.change_state(battle)

    def _play_data(self):
        return {"balls_left": self.balls_left, "current_streak": self.current_streak,
                "rounds_completed": self.rounds_completed, "pending_wild_encounters": 0,
                "initial_round_active": False, "dungeon": True}

    # ---------------------------------------------------------------- trainers
    def _meet_trainer(self, mover, spotted=False):
        self.walk_goal = None
        self.encounter = mover
        if spotted:
            self.mode, self.spot_timer = "SPOTTED", int(FPS * 0.8)
            sfx = getattr(self.game.assets, "ui_sfx", None)
            sound = sfx.get("select") if isinstance(sfx, dict) else None
            if sound:
                sound.play()
        else:
            self._battle_trainer(mover)

    def _battle_trainer(self, mover):
        self.pending = ("trainer", mover)
        self.mode = "MAP"
        self.rounds_completed += 1
        self.trigger_trainer_battle(specific_index=mover.payload[0])  # intro, battle, rewards: the route's own

    # ---------------------------------------------------------------- Sweet Scent and Honey
    def _scent_source(self):
        """What draws three wild Pokemon here: "SWEET SCENT" (a party Pokemon's move, once a floor),
        "HONEY" (used up), or None."""
        story = self.game.story_manager
        if not self._can_catch() or not self._get_wild_pool(self.area_data):
            return None
        knows = any(p and p.current_hp > 0 and any(str(m).upper().replace(" ", "-") == "SWEET-SCENT"
                                                   for m in (getattr(p, "moves", None) or []))
                    for p in story.player_team)
        if knows and self.scent_floor != self.run.index:
            return "SWEET SCENT"
        if story.inventory.get("HONEY", 0) > 0:
            return "HONEY"
        return None

    def use_scent(self):
        if not self._ready():
            return
        source = self._scent_source()
        story = self.game.story_manager
        if source is None:
            if not self._can_catch():
                self.flash("You need Poke Balls to catch here.")
            else:
                self.flash("No HONEY, and no Pokemon that knows SWEET SCENT.")
            return
        if source == "HONEY":
            story.inventory["HONEY"] -= 1
            first = f"{self.game.player_name} spread some HONEY around..."
        else:
            self.scent_floor = self.run.index
            first = "A sweet scent drifted through the air..."
        self.walk_goal = None

        def begin():
            self.mode = "CATCH"
            self.is_progression_paused = False
            self.pending_wild_encounters = 0
            self.input_delay = 20
            self.trigger_wild_encounter()  # the route's three-Pokemon catch, then show_progression_menu
        self.say([first, "Wild Pokemon were drawn in!"], then=begin)

    # ---------------------------------------------------------------- input
    def _buttons(self):
        """The map's own buttons (bottom right): (rect, label, colour, action, enabled)."""
        w, h = self.game.width, self.game.height
        source = self._scent_source()
        label = "HONEY" if source == "HONEY" else "SWEET SCENT"
        honey = self.game.story_manager.inventory.get("HONEY", 0)
        sub = f"x{honey}" if source == "HONEY" else ("once a floor" if source else "")
        return [
            (pygame.Rect(w - 280, h - 162, 260, 70), label, theme.BAG, self.use_scent, source is not None, sub),
            (pygame.Rect(w - 280, h - 80, 104, 58), "WAIT", theme.RUN, self.wait_turn, True, None),
            (pygame.Rect(w - 164, h - 80, 144, 58), "CLASSIC", theme.BACK, self._classic, True, None),
        ]

    def _choice_rects(self):
        w, h = self.game.width, self.game.height
        return [pygame.Rect(w // 2 - 330, int(h * 0.62), 300, 120), pygame.Rect(w // 2 + 30, int(h * 0.62), 300, 120)]

    def _answer_rects(self):
        w, h = self.game.width, self.game.height
        bw = 230
        x0 = w // 2 - (3 * bw + 2 * 30) // 2
        return [pygame.Rect(x0 + i * (bw + 30), int(h * 0.66), bw, 110) for i in range(3)]

    def _camera(self):
        """The pixel the screen is centred on (the player, mid-step)."""
        px, py = self.run.player
        if self.anim > 0:
            k = 1 - self.anim / STEP_FRAMES
            fx, fy = self.anim_from
            px, py = fx + (px - fx) * k, fy + (py - fy) * k
        return px * TILE + TILE / 2, py * TILE + TILE / 2

    def _tile_at(self, pos):
        cx, cy = self._camera()
        ox, oy = self.game.width / 2 - cx, self.game.height / 2 - cy
        return int((pos[0] - ox) // TILE), int((pos[1] - oy) // TILE)

    KEYS = {pygame.K_UP: (0, -1), pygame.K_w: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0)}

    def handle_events(self, events):
        if self.mode == "CATCH":
            return super().handle_events(events)
        for e in events:
            if self.dialogue_box.visible:  # a tap anywhere (or Enter) moves the text on
                if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or \
                        (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)):
                    self.dialogue_box.advance()
                continue
            if self.mode == "MAP":
                self._map_event(e)
            elif self.mode == "CHOICE":
                self._choice_event(e)
            elif self.mode == "MATH":
                self._math_event(e)

    def _map_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in self.KEYS:
                self.walk_goal = None
                self.step(*self.KEYS[e.key])
            elif e.key in (pygame.K_PERIOD, pygame.K_z):
                self.wait_turn()
            elif e.key == pygame.K_h:
                self.use_scent()
            elif e.key in (pygame.K_ESCAPE, pygame.K_m) and self.hud_buttons:
                self.hud_buttons[0].callback()  # MENU
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for rect, _label, _color, action, ok, _sub in self._buttons():
                if rect.collidepoint(e.pos):
                    action()
                    return
            if self._minimap_rect().collidepoint(e.pos):
                return
            tx, ty = self._tile_at(e.pos)
            px, py = self.run.player
            if (tx, ty) == (px, py):
                self.wait_turn()
            elif abs(tx - px) + abs(ty - py) == 1:
                self.walk_goal = None
                self.step(tx - px, ty - py)
            elif self.run.floor.walkable(tx, ty) and (tx, ty) in self.run.floor.seen:
                self.walk_goal = (tx, ty)
            else:  # somewhere unseen: one step that way
                dx, dy = tx - px, ty - py
                self.walk_goal = None
                self.step(*((1 if dx > 0 else -1, 0) if abs(dx) >= abs(dy) else (0, 1 if dy > 0 else -1)))

    def _choice_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, rect in enumerate(self._choice_rects()):
                if rect.collidepoint(e.pos):
                    self._pick(i)
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                self.choice = 1 - self.choice
            elif e.key in (pygame.K_1, pygame.K_KP1):
                self._pick(0)
            elif e.key in (pygame.K_2, pygame.K_KP2):
                self._pick(1)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self._pick(self.choice)

    def _math_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, rect in enumerate(self._answer_rects()):
                if rect.collidepoint(e.pos):
                    self._answer(i)
                    return
        elif e.type == pygame.KEYDOWN:
            keys = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2}
            if e.key in keys:
                self._answer(keys[e.key])

    # ---------------------------------------------------------------- each frame
    def update(self):
        if self.mode == "CATCH":
            return super().update()
        if self.dialogue_box.visible:
            self.dialogue_box.update()
        if self.toast_timer > 0:
            self.toast_timer -= 1
        if self.banner > 0:
            self.banner -= 1
        if self.anim > 0:
            self.anim -= 1
        if self.mode == "MAP":
            if self.walk_goal and self._ready():
                if self.run.player == self.walk_goal:
                    self.walk_goal = None
                else:
                    step = self.run.walk_toward(self.walk_goal)
                    if step is None:
                        self.walk_goal = None
                    else:
                        self.step(*step)
        elif self.mode == "MATH":
            self.math_timer -= 1
            if self.math_timer <= 0:
                self.throw_result = "timeout"
                self._resolve_throw()
        elif self.mode == "THROW":
            self.throw_timer -= 1
            if self.throw_timer <= 0:
                self._resolve_throw()
        elif self.mode == "SPOTTED":
            self.spot_timer -= 1
            if self.spot_timer <= 0:
                self._battle_trainer(self.encounter)

    # ---------------------------------------------------------------- drawing
    def _render_floor(self):
        f = self.run.floor
        floor_c, grass_c, wall_c, top_c = COLORS.get(f.style, COLORS["field"])
        surf = pygame.Surface((f.w * TILE, f.h * TILE))
        surf.fill(wall_c)
        rng = random.Random(self.run.index * 7919 + f.w)
        for y in range(f.h):
            for x in range(f.w):
                r = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                t = f.tiles[y][x]
                if t == core.WALL:
                    near = any(f.walkable(x + dx, y + dy) for dx, dy in core.DIRS)
                    if near or rng.random() < 0.5:  # a tree (or a boulder in a cave)
                        pygame.draw.circle(surf, theme.shade(wall_c, 0.7), (r.centerx, r.centery + 6), TILE // 2 - 2)
                        pygame.draw.circle(surf, top_c, (r.centerx, r.centery - 2), TILE // 2 - 6)
                        pygame.draw.circle(surf, theme.shade(top_c, 1.25), (r.centerx - 8, r.centery - 10), TILE // 6)
                    continue
                pygame.draw.rect(surf, floor_c, r)
                if t == core.GRASS:
                    pygame.draw.rect(surf, grass_c, r.inflate(-2, -2), border_radius=6)
                    dark = theme.shade(grass_c, 0.7)
                    for i in range(4):
                        bx = r.x + 8 + i * 11
                        by = r.y + 14 + (i % 2) * 18
                        pygame.draw.polygon(surf, dark, [(bx, by + 14), (bx + 5, by), (bx + 10, by + 14)])
                elif f.style == "field" and rng.random() < 0.06:  # a few flowers
                    c = rng.choice([(240, 240, 240), (250, 210, 80), (240, 120, 140)])
                    pygame.draw.circle(surf, c, (r.x + rng.randint(10, TILE - 10), r.y + rng.randint(10, TILE - 10)), 4)
        self._floor_surf, self._floor_index = surf, self.run.index

    def _sprite(self, key, make):
        if key not in self._sprites:
            try:
                self._sprites[key] = make()
            except (pygame.error, OSError, ValueError, TypeError):
                self._sprites[key] = None
        return self._sprites[key]

    def _icon(self, pokemon, size=TILE, flip=False):
        from src.minigames.base import icon
        return icon(self.game, pokemon.id, size, flip=flip)

    def _trainer_img(self, info):
        name = info.get("sprite") or "rival.png"

        def make():
            img = _trainer_sprite(self.game, name)
            if img is None:
                return None
            box = img.get_bounding_rect()
            img = img.subsurface(box) if box.w and box.h else img
            k = (TILE + 18) / max(1, img.get_height())
            return pygame.transform.smoothscale(img, (max(1, int(img.get_width() * k)), TILE + 18))
        return self._sprite(("trainer", name), make)

    def _item_img(self, key, size=34):
        def make():
            img = self.game.assets.get_item_image("POKE_BALL" if key == catching.POKE else key)
            if img is None:
                return None
            return pygame.transform.smoothscale(img, (size, size))
        return self._sprite(("item", key, size), make)

    def _ball_img(self, size=34):
        return self._sprite(("ball", size), lambda: pygame.transform.smoothscale(self.game.assets.ball_imgs[0], (size, size)))

    def _area_name(self, key):
        item = self.exit_items.get(key)
        if item:
            return travel_label(self.game, item)
        prog = self.game.loader.area_data.get("STORY_PROGRESSION", {})
        return (prog.get(key) or {}).get("route_name") or key.replace("_", " ").title()

    def lead(self):
        team = self.game.story_manager.player_team
        return next((p for p in team if p and p.current_hp > 0), team[0] if team else None)

    def draw(self):
        if self.mode == "CATCH":
            return super().draw()
        screen = self.game.screen
        W, H = self.game.width, self.game.height
        f = self.run.floor
        screen.fill((10, 14, 24))  # (the fog's colour: the unknown edge of the map)
        if self._floor_index != self.run.index or self._floor_surf is None:
            self._render_floor()
        cx, cy = self._camera()
        ox, oy = int(W / 2 - cx), int(H / 2 - cy)
        screen.blit(self._floor_surf, (ox, oy))
        x0, y0 = max(0, -ox // TILE - 1), max(0, -oy // TILE - 1)
        x1, y1 = min(f.w, (W - ox) // TILE + 2), min(f.h, (H - oy) // TILE + 2)
        fonts = self.game.assets.fonts

        def at(x, y):
            return pygame.Rect(ox + x * TILE, oy + y * TILE, TILE, TILE)

        # things lying about (in tiles you've seen)
        for (x, y), target in f.exits.items():
            if (x, y) not in f.seen:
                continue
            r = at(x, y)
            if target == core.STAIRS:
                pygame.draw.rect(screen, (60, 52, 44), r.inflate(-6, -6), border_radius=6)
                for i in range(4):
                    pygame.draw.line(screen, (196, 180, 150), (r.x + 10, r.y + 12 + i * 9), (r.right - 10, r.y + 12 + i * 9), 3)
                label = "STAIRS"
            else:
                pygame.draw.rect(screen, (150, 104, 60), (r.centerx - 4, r.y + 20, 8, TILE - 22))
                pygame.draw.rect(screen, (214, 172, 104), (r.x + 4, r.y + 4, TILE - 8, 24), border_radius=5)
                pygame.draw.rect(screen, (110, 72, 40), (r.x + 4, r.y + 4, TILE - 8, 24), 2, border_radius=5)
                label = self._area_name(target)
            tag = fonts["caption"].render(theme.pokemon_word(label.upper()), True, (255, 255, 255))
            pill = tag.get_rect(midbottom=(r.centerx, r.y - 2)).inflate(12, 6)
            pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
            screen.blit(tag, tag.get_rect(center=pill.center))
        for (x, y), key in f.items.items():
            if (x, y) in f.seen:
                img = self._item_img(key) or self._ball_img()
                screen.blit(img, img.get_rect(center=at(x, y).center))
        bob = int(3 * math.sin(pygame.time.get_ticks() / 180))
        for (x, y) in f.tm_spots:
            if (x, y) in f.seen:
                img = self._ball_img(38)
                glow = at(x, y).inflate(-8, -8)
                pygame.draw.ellipse(screen, (255, 236, 140), glow, 3)
                screen.blit(img, img.get_rect(center=(glow.centerx, glow.centery + bob)))
        # wild Pokemon and trainers you can see
        for m in f.movers:
            if not self.run.visible(m.x, m.y):
                continue
            r = at(m.x, m.y)
            if m.kind == "wild":
                img = self._icon(m.payload, TILE, flip=(m.x < self.run.player[0]))
                screen.blit(img, img.get_rect(center=r.center))
                if m.payload.is_shiny:
                    pygame.draw.circle(screen, (255, 230, 90), (r.right - 8, r.y + 8), 5)
                if m.alert:
                    theme.shadow_text(screen, "!", fonts["label"], r.right - 6, r.y - 18, color=(220, 60, 50))
            else:
                img = self._trainer_img(m.payload[1])
                if img:
                    screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom)))
                else:
                    pygame.draw.circle(screen, (90, 90, 160), r.center, TILE // 3)
                # which way it's looking
                fx, fy = m.facing
                tip = (r.centerx + fx * (TILE // 2 + 6), r.centery + fy * (TILE // 2 + 6))
                pygame.draw.circle(screen, (255, 255, 255), tip, 5)
                pygame.draw.circle(screen, (40, 40, 60), tip, 5, 2)
        # you: your lead Pokemon
        lead = self.lead()
        pr = pygame.Rect(0, 0, TILE, TILE)
        pr.center = (W // 2, H // 2)
        if lead:
            img = self._icon(lead, TILE + 8, flip=(self.facing[0] > 0))
            screen.blit(img, img.get_rect(center=(pr.centerx, pr.centery - 4)))
        # the fog: unseen tiles are dark, seen ones you can't see right now are dimmed
        fog = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        fog.fill((10, 14, 24, 150))
        for y in range(y0, y1):
            for x in range(x0, x1):
                r = at(x, y)
                if (x, y) not in f.seen:
                    screen.fill((10, 14, 24), r)
                elif not self.run.visible(x, y):
                    screen.blit(fog, r)

        self._draw_hud(screen)
        if self.mode in ("CHOICE", "MATH", "THROW"):
            self._draw_encounter(screen)
        elif self.mode == "SPOTTED" and self.encounter:
            m = self.encounter
            r = at(m.x, m.y)
            bubble = pygame.Rect(0, 0, 40, 46)
            bubble.midbottom = (r.centerx, r.y - 22)
            pygame.draw.rect(screen, (255, 255, 255), bubble, border_radius=10)
            pygame.draw.rect(screen, (40, 40, 60), bubble, 3, border_radius=10)
            theme.shadow_text(screen, "!", fonts["button"], bubble.centerx, bubble.centery, color=(220, 60, 50), align="center")
        if self.dialogue_box.visible:
            self.dialogue_box.draw(screen)
        for b in self.hud_buttons:
            b.draw(screen)

    def _minimap_rect(self):
        f = self.run.floor
        s = 4
        return pygame.Rect(self.game.width - f.w * s - 24, 92, f.w * s + 8, f.h * s + 8)

    def _draw_hud(self, screen):
        W, H = self.game.width, self.game.height
        fonts = self.game.assets.fonts
        story = self.game.story_manager
        bar = pygame.Rect(210, 12, W - 420, 64)
        theme.draw_textbox(screen, bar)
        name = self.area_data.get("route_name", self.area_key.replace("_", " ").title())
        floor_txt = f"  {self.run.index + 1}F" if self.run.n_floors > 1 else ""
        theme.shadow_text(screen, theme.pokemon_word(name) + floor_txt, fonts["button"], bar.x + 20,
                          bar.centery - fonts["button"].get_height() // 2)
        ball = catching.selected(story)
        bimg = self._item_img(ball, 30) or self._ball_img(30)
        bx = bar.right - 380
        screen.blit(bimg, (bx, bar.centery - 15))
        theme.shadow_text(screen, f"x{catching.owned(story, ball)}", fonts["label"], bx + 36, bar.centery - 12)
        lead = self.lead()
        if lead:
            theme.shadow_text(screen, f"{lead.display_name.upper()} Lv{lead.level}", fonts["caption"], bar.right - 250, bar.y + 10)
            theme.hp_bar(screen, bar.right - 250, bar.y + 36, 220, lead.current_hp, lead.get_max_hp())
        # the mini-map
        f = self.run.floor
        mm = self._minimap_rect()
        panel = pygame.Surface(mm.size, pygame.SRCALPHA)
        panel.fill((10, 14, 24, 170))
        screen.blit(panel, mm.topleft)
        s = 4
        for (x, y) in f.seen:
            if f.walkable(x, y):
                screen.fill((150, 190, 230), (mm.x + 4 + x * s, mm.y + 4 + y * s, s, s))
        for (x, y), target in f.exits.items():
            if (x, y) in f.seen:
                screen.fill((250, 200, 60), (mm.x + 3 + x * s, mm.y + 3 + y * s, s + 2, s + 2))
        for (x, y) in list(f.items) + list(f.tm_spots):
            if (x, y) in f.seen:
                screen.fill((90, 220, 120), (mm.x + 4 + x * s, mm.y + 4 + y * s, s, s))
        for m in f.movers:
            if self.run.visible(m.x, m.y):
                screen.fill((230, 80, 70) if m.kind == "wild" else (170, 110, 230),
                            (mm.x + 4 + m.x * s, mm.y + 4 + m.y * s, s, s))
        px, py = self.run.player
        pygame.draw.circle(screen, (255, 255, 255), (mm.x + 4 + px * s + 2, mm.y + 4 + py * s + 2), 3)
        # the buttons
        if self.mode == "MAP" and not self.dialogue_box.visible:
            mouse = pygame.mouse.get_pos()
            for rect, label, color, _a, ok, sub in self._buttons():
                theme.command_button(screen, rect, label, fonts["caption"], color if ok else theme.BACK,
                                     hover=rect.collidepoint(mouse), small=fonts["small"], sub=sub or None)
        # a found item, and the area's name on arrival
        if self.toast_timer > 0:
            t = fonts["label"].render(self.toast, True, (255, 255, 255))
            r = t.get_rect(midtop=(W // 2, 92)).inflate(28, 14)
            pygame.draw.rect(screen, (30, 36, 58), r, border_radius=12)
            pygame.draw.rect(screen, theme.BAG, r, 2, border_radius=12)
            screen.blit(t, t.get_rect(center=r.center))
        if self.banner > 0 and self.mode == "MAP":
            word = theme.pokemon_word(self.area_data.get("route_name", "")) + \
                (f"  {self.run.index + 1}F" if self.run.n_floors > 1 else "")
            t = fonts["big"].render(word, True, (255, 255, 255))
            r = t.get_rect(center=(W // 2, int(H * 0.3))).inflate(60, 24)
            panel = pygame.Surface(r.size, pygame.SRCALPHA)
            panel.fill((10, 14, 24, min(200, self.banner * 4)))
            screen.blit(panel, r.topleft)
            t.set_alpha(min(255, self.banner * 5))
            screen.blit(t, t.get_rect(center=r.center))

    def _draw_encounter(self, screen):
        W, H = self.game.width, self.game.height
        fonts = self.game.assets.fonts
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 140))
        screen.blit(shade, (0, 0))
        p = self.encounter.payload if self.encounter else None
        if p is None:
            return
        card = pygame.Rect(0, 0, 760, 120)
        card.midtop = (W // 2, 96)
        theme.draw_textbox(screen, card)
        theme.shadow_text(screen, f"A wild {p.display_name.upper()} (Lv{p.level}) appeared!", fonts["button"],
                          card.centerx, card.centery - 18, align="center")
        if self.mode == "CHOICE":
            sub = "Pick MATH to try a quick catch, or BATTLE." if self._can_catch() else "Pick BATTLE."
        elif self.mode == "MATH":
            sub = "Answer right to throw a ball!"
        else:
            sub = ""
        if sub:
            theme.shadow_text(screen, sub, fonts["label"], card.centerx, card.centery + 22, align="center")
        img = p.image
        y_mid = int(H * 0.42)
        if self.mode == "THROW":
            k = 1 - self.throw_timer / (FPS * 1.2)
            if self.throw_result in ("caught", "broke") or k < 0.5:
                ball = self._ball_img(48)
                bx = W // 2 + int((1 - min(1, k * 2)) * 260)
                by = y_mid + int((1 - min(1, k * 2)) * 220) - int(math.sin(min(1, k * 2) * math.pi) * 120)
                if k >= 0.5 and self.throw_result in ("caught", "broke"):  # in the ball, shaking
                    bx += int(math.sin(k * 40) * 8)
                    img = None
                screen.blit(ball, ball.get_rect(center=(bx, by)))
        if img is not None:
            screen.blit(img, img.get_rect(center=(W // 2, y_mid)))
        mouse = pygame.mouse.get_pos()
        if self.mode == "CHOICE":
            can = self._can_catch()
            labels = [("MATH", "1 question: catch it!" if can else "No balls / no Pokedex", theme.RUN if can else theme.BACK),
                      ("BATTLE", "Fight it in a battle", theme.FIGHT)]
            for i, (rect, (label, small, color)) in enumerate(zip(self._choice_rects(), labels)):
                theme.command_button(screen, rect, label, fonts["button"], color,
                                     hover=rect.collidepoint(mouse) or self.choice == i, small=fonts["caption"], sub=small)
        elif self.mode == "MATH":
            q = pygame.Rect(0, 0, max(380, fonts["big"].size(self.problem_str)[0] + 120), 92)
            q.center = (W // 2, int(H * 0.58))
            theme.draw_textbox(screen, q)
            theme.shadow_text(screen, self.problem_str, fonts["big"], q.centerx, q.centery, align="center")
            for i, rect in enumerate(self._answer_rects()):
                theme.card(screen, rect, hover=rect.collidepoint(mouse), accent=theme.RUN)
                theme.shadow_text(screen, str(self.options[i]), fonts["num"], rect.centerx, rect.centery, align="center")
            k = max(0.0, self.math_timer / (MATH_SECONDS * FPS))
            track = pygame.Rect(W // 2 - 300, int(H * 0.66) + 126, 600, 14)
            pygame.draw.rect(screen, (60, 64, 80), track, border_radius=7)
            pygame.draw.rect(screen, theme.POKEMON if k > 0.33 else theme.FIGHT,
                             (track.x, track.y, max(8, int(track.w * k)), track.h), border_radius=7)
