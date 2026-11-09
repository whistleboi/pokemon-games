"""A guest walking the host's map (Jordan, 11-08): the same drawn map, the host beside you. The game files are the same
on both devices, so only positions cross the network. The guest follows when the host changes area, for now."""
import collections
import copy
import math
import threading
import time
import types

import pygame

from src.coop import session as sess
from src.coop import world
from src.dungeon import art
from src.states.base import GameState
from src.states.systems.mart import PokeMartState
from src.states.overworld import dungeon as dn
from src.states.overworld import overworld_battle as owb
from src.states.overworld.walk_town import custom
from src.pokemon.data import Pokemon
from src.world.story import StoryManager
from src.ui import theme
from src.ui.panels import CommandButton

TILE = world.TILE
STEP = 8
KEYS = {pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
        pygame.K_w: (0, -1), pygame.K_s: (0, 1), pygame.K_a: (-1, 0), pygame.K_d: (1, 0)}
RECONNECT_FOR = sess.GRACE_SECONDS
TETHER = 4          # tiles: how far a fainted guest can be from the host
BALLS = 10          # a guest's Poke Balls (their own shopping comes with the guest's money)
BLOCKED = set("ob")  # (water and boulders: not on foot; Surf and Strength are the host's journey for now)


class _GuestMart(PokeMartState):
    """The Mart, on the guest's own money."""

    def __init__(self, game, map_state):
        super().__init__(game, map_state)
        self.map_state = map_state

    def exit_shop(self):
        self.map_state.send_ledger()
        super().exit_shop()

    def update(self):
        if self.map_state.pump():
            super().update()


class _Floor:
    """The little of a floor that a battle on the map asks about."""
    movers = ()

    def __init__(self, world_state):
        self.world_state = world_state

    def walkable(self, x, y):
        return self.world_state._open((x, y))

    def occupied(self, x, y):
        return (x, y) in self.world_state.solid


class _Run:
    def __init__(self, world_state):
        self.world_state, self.floor = world_state, _Floor(world_state)

    @property
    def player(self):
        return self.world_state.player

    @player.setter
    def player(self, t):
        self.world_state.player = t


class CoopWorldState(GameState):
    uses_keyboard = True
    _backdrop = False
    _focus = None
    _ow_foe = None
    _tile_rect = owb.OverworldBattles._tile_rect
    _partner_beside = owb.OverworldBattles._partner_beside
    _throw_spot = owb.OverworldBattles._throw_spot
    # (the map's own drawing, so everything looks as it does on the host's screen)
    HONEY_PACK = dn.DungeonState.HONEY_PACK
    JUMBO = dn.DungeonState.JUMBO
    _sprite = dn.DungeonState._sprite
    _sheet_frame = dn.DungeonState._sheet_frame
    _icon = dn.DungeonState._icon
    _follower_img = dn.DungeonState._follower_img
    _trainer_scale = dn.DungeonState._trainer_scale
    _jumbo = dn.DungeonState._jumbo
    _trainer_img = dn.DungeonState._trainer_img
    _item_img = dn.DungeonState._item_img
    _ball_img = dn.DungeonState._ball_img
    _figure_img = dn.DungeonState._figure_img
    _draw_gate = dn.DungeonState._draw_gate
    _boss_sprite = dn.DungeonState._boss_sprite

    def __init__(self, game, link, lobby):
        super().__init__(game)
        self.link, self.lobby = link, lobby
        # This device's own game is put aside for the session: the guest plays on a blank story, and nothing here saves.
        self._home = game.story_manager, game.states.get("play"), copy.deepcopy(game.data.data)
        game.story_manager = StoryManager()
        game.story_manager.game = game
        game.story_manager.balls_left = BALLS
        game.story_manager.money = 0  # (a blank story starts with some: a guest's is what they earn)
        game.states["play"] = self
        game.data.read_only = True
        self.total_caught, self.p_data = 0, [None] * 3
        self.roster, self.picked, self.team_ready, self.asking = None, False, False, False
        self.outbox, self.note, self.note_time = None, "", 0
        self.link.send_intent({"roster_ask": True})
        self.run, self.fighting = _Run(self), False
        self.feeds, self.doors, self.swapping = {}, {}, False
        self.exits, self.vote, self.asked, self.before_exit = {}, None, False, None
        self.trainers, self.after_reading, self.ow_stander, self.down = {}, None, None, False
        self._sprites = {}
        self.area_key, self.area_data = None, {}
        self.scene, self.solid, self.signs, self.wilds = {}, set(), {}, {}
        self.reading, self.want = None, None
        self.area, self.floor, self.grid, self.surf = None, 0, None, None
        self.player, self.facing, self.anim, self.anim_from = (0, 0), (0, 1), 0, (0, 0)
        self.partner = self.partner_from = self.player
        self.host = {}
        self.path = []
        self.char = lobby.char
        self.reconnecting, self._retry = None, None
        self._busy_retry = False
        self.btn_leave = CommandButton((game.width - 176, 14, 160, 56), "LEAVE", game.assets.fonts["label"], self.leave,
                                       bg_color=theme.FIGHT, autosize=False)
        self.btn_raid = CommandButton((game.width - 586, 14, 220, 56), "JOIN RAID", game.assets.fonts["label"], self.join_raid,
                                      bg_color=(200, 60, 120), autosize=False)
        self.btn_watch = CommandButton((game.width - 356, 14, 170, 56), "WATCH", game.assets.fonts["label"], self.watch,
                                       bg_color=theme.RUN, autosize=False)
        cx = game.width // 2
        self.btn_yes = CommandButton((cx - 180, 310, 170, 60), "YES", game.assets.fonts["label"], lambda: self._vote(True),
                                     bg_color=theme.POKEMON, autosize=False)
        self.btn_revive = CommandButton((game.width // 2 - 150, 86, 300, 60), "REVIVE", game.assets.fonts["label"], self.revive,
                                        bg_color=theme.POKEMON, autosize=False)
        self.btn_no = CommandButton((cx + 10, 310, 170, 60), "NO", game.assets.fonts["label"], lambda: self._vote(False),
                                    bg_color=theme.FIGHT, autosize=False)

    def _can_help(self):
        """Who you could revive with a Revive of your own (you must be able to fight), or None."""
        inv = self.game.story_manager.inventory
        if self.down or self.fighting or not self._healthy_team() or not any(inv.get(k, 0) > 0 for k in ("REVIVE", "MAX_REVIVE")):
            return None
        return next((d for d in self.host.get("down", []) if d["who"] != self.link.pid), None)

    def revive(self):
        target = self._can_help()
        if target:
            self.link.send_intent({"revive": target["who"]})

    def _vote(self, yes):
        self.link.send_intent({"vote_answer": self.vote["id"], "yes": yes})
        self.vote = None
        if yes:
            self.say_note("Waiting for everyone...")

    def _propose(self, t):
        if self.asked or self.vote:
            return
        self.asked, self.path, self.want = True, [], None
        self.link.send_intent({"propose": list(t)})
        self.say_note(f"Asking to go to {self.exits[t]}...")

    def _not_going(self, why):
        self.asked = False
        if self.before_exit:
            self.player = self.anim_from = self.before_exit
            self.before_exit = None
            self._report()
        if why:
            self.say_note(why)

    @property
    def feed(self):
        """A fight going on that could be watched (the first, if there are several)."""
        return next(iter(self.feeds.values()), None)

    def _raid_open(self):
        raid = (self.feeds.get("") or {}).get("raid")
        return bool(raid and raid["open"]) and not self.fighting and not self.down and self._healthy_team()

    def join_raid(self):
        self.link.send_intent({"raid_join": True})
        self.say_note("Joining the raid...")

    def left_raid(self):
        """Leaving part way: the host hears, then the map."""
        self.link.send_intent({"raid_leave": True})

    def watch(self):
        from src.states.coop_watch import CoopWatchState
        who = next(iter(self.feeds), None)
        if who is not None:
            self.game.change_state(CoopWatchState(self.game, self, lambda: self.feeds.get(who), who or self.host.get("name", "The host"), pump=self.pump))

    # ------------------------------------------------------------------ the map
    def _load(self, area, floor):
        self.area, self.floor, self.grid, self.surf = area, floor, None, None
        self.area_key = area
        self.game.story_manager.current_area_key = area
        self.scene, self.solid, self.signs, self.reading, self.want = {}, set(), {}, None, None
        self.wilds, self.doors, self.exits, self.asked, self.before_exit = {}, {}, {}, False, None
        self.trainers = {}
        m = custom(self.game).get(area)
        if not m:
            return
        floors = m.get("floors")
        if floors and floor < len(floors):
            self.grid = floors[floor]["art"]
        elif not floors:
            self.grid = m["art"]
        if self.grid:
            self.surf = art.surface(self.grid, m.get("buildings", {}), TILE, m.get("roofs"), m.get("theme"))
            for t, letter in art.doors(self.grid).items():
                if letter not in m.get("exits", {}):
                    self.doors[t] = m.get("buildings", {}).get(letter, "house")

    def _open(self, t):
        x, y = t
        return bool(self.grid) and 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]) \
            and art.walkable(self.grid, x, y) and self.grid[y][x] not in BLOCKED and t not in self.solid

    def _arrive(self, x, y):
        """Beside the host, on open ground."""
        seen, todo = {(x, y)}, collections.deque([(x, y)])
        while todo:
            t = todo.popleft()
            if self._open(t) and t != (x, y):
                self.player = self.anim_from = t
                return
            for d in KEYS.values():
                n = (t[0] + d[0], t[1] + d[1])
                if n not in seen and len(seen) < 400:
                    seen.add(n)
                    todo.append(n)
        self.player = self.anim_from = (x, y)

    def _on_host(self, info):
        self.host = info
        if "area" not in info or self.fighting:  # (a fight stays where it is: the guest catches up after)
            return
        if self.down and (info["area"], info["floor"]) == (self.area, self.floor) \
                and abs(self.player[0] - info["x"]) + abs(self.player[1] - info["y"]) > TETHER + 1:
            self._arrive(info["x"], info["y"])  # (the host walked on: a fainted guest is brought along)
            self.path = []
            self._report()
        if (info["area"], info["floor"]) != (self.area, self.floor):
            self._load(info["area"], info["floor"])
            self.path = []
            self._arrive(info["x"], info["y"])
            self._report()

    def _on_scene(self, scene):
        """What's on the map now: anything standing there is in the way, and signs can be read."""
        if (scene.get("area"), scene.get("floor")) != (self.area, self.floor):
            return
        self.scene = scene
        self.area_data = {"area_boss": {"id": scene["boss"]}} if "boss" in scene else {}
        self.solid = {(m["x"], m["y"]) for m in scene["movers"]}
        self.solid.update((b[0], b[1]) for b in scene["boulders"])
        self.solid.update((g[0], g[1]) for g in scene["gates"])
        self.signs = {(s[0], s[1]): s[2] for s in scene["signs"]}
        self.wilds = {(m["x"], m["y"]): m for m in scene["movers"] if m["k"] == "w"}
        self.trainers = {(m["x"], m["y"]): m for m in scene["movers"] if m["k"] == "t"}
        self.exits = {(x, y): label for x, y, label in scene.get("exits", [])}

    def _report(self):
        p = [self.area, self.floor, self.player[0], self.player[1], self.facing[0], self.facing[1]]
        self.link.send_intent({"at": p, "char": self.char})

    # ------------------------------------------------------------------ walking
    def _tethered(self, t):
        """Fainted: only near whoever can still fight."""
        h = self.host
        return self.down and h.get("active") and h.get("area") == self.area and h.get("floor") == self.floor \
            and abs(t[0] - h.get("x", t[0])) + abs(t[1] - h.get("y", t[1])) > TETHER

    def _step(self, d):
        t = (self.player[0] + d[0], self.player[1] + d[1])
        self.facing = d
        if self._tethered(t):
            self.say_note("Your team fainted: stay close.")
            self.path = []
            return False
        if self._open(t):
            self.anim_from, self.player, self.anim = self.player, t, STEP
            self._report()
            if t in self.exits:  # (a way out: suggest it)
                self.before_exit = self.anim_from
                self._propose(t)
            elif any(i[:2] == list(t) for i in self.scene.get("items", [])):
                self.link.send_intent({"pick": list(t)})
            return True
        if t in self.signs:  # (walked into a sign: read it)
            self.reading, self.path = self.signs[t], []
        elif t in self.wilds:
            self._ask_fight(self.wilds[t])
        elif t in self.trainers:
            self._ask_trainer(self.trainers[t])
        elif t in self.exits:
            self._propose(t)
        elif t in self.doors:
            self._use(t)
        return False

    # ------------------------------------------------------------------ Pokemon and fights
    # (what the battle screen asks of the map it came from)
    @property
    def balls_left(self):
        return self.game.story_manager.balls_left

    def generate_math_set(self, score_unused=0, num_options=3):
        return self.game.math.generate(self.game.story_manager.get_math_level(), num_options=num_options)

    def check_for_evolution(self, force_catch_evo=False):  # (the host's Pokemon evolve on the host's game)
        return False

    def complete_catch(self, idx):  # (the host keeps it: see fight_over)
        self.p_data = [None] * 3

    def say_note(self, text):
        self.note, self.note_time = text, 150

    def borrow(self, uids):
        if uids:
            self.link.send_intent({"borrow": list(uids)})
            self.say_note("Asking the host for your team...")

    def _got_team(self, msg):
        story = self.game.story_manager
        if msg.get("replace"):
            story.player_team = []
        for row in msg.get("lent", []):
            p = story._load_pokemon(row["rec"], self.game.loader)
            p.coop_uid = row["uid"]
            story.player_team.append(p)
        got = msg.get("settings") or {}
        story.badges = got.get("badges", {})
        story.active_badge_region = got.get("active_badge_region")
        story.math_difficulty = got.get("math_difficulty", "AUTO")
        story.story_flags = got.get("story_flags", {})  # (level caps and obedience as on the host's game; a copy, never sent back)
        story.level_cap_mode = got.get("level_cap_mode", "STORY")
        can = bool(got.get("can_catch", True))
        story.catch_unlocked = lambda region=None: can
        self.team_ready = bool(story.player_team)
        self.down = self.team_ready and not self._healthy_team()
        self.say_note("Your team is ready!" if self.team_ready else "Those Pokemon aren't free now.")
        self.picked = self.team_ready

    def _healthy_team(self):
        return any(p.current_hp > 0 and not getattr(p, "is_egg", False) for p in self.game.story_manager.player_team)

    def _ask_fight(self, m):
        if self.asking or self.outbox:
            return
        if not self._healthy_team():
            self.say_note("You need a Pokemon that can fight.")
            return
        self.asking, self.path, self.want = True, [], None
        self.link.send_intent({"fight": m["uid"]})

    def _ask_trainer(self, m):
        if self.asking or self.outbox:
            return
        if not self._healthy_team():
            self.say_note("You need a Pokemon that can fight.")
            return
        self.asking, self.path, self.want = True, [], None
        self.link.send_intent({"trainer": m["uid"]})

    def _start_trainer(self, info):
        from src.coop.guest_battle import GuestTrainerBattle
        from src.states.battle import TrainerIntroState
        self.asking, self.fighting = False, True
        story, game = self.game.story_manager, self.game
        team = []
        for rec in info["team"]:
            form = rec.get("form", "normal")
            raw = game.loader.fetch_specific(rec["id"], form="normal" if form == "gmax" else form, is_shiny=rec.get("shiny", False))
            p = Pokemon(raw, game.assets, size_mult=3.125)
            story._apply_record(p, rec, form)
            team.append(p)
        sprite = dn._trainer_sprite(game, info.get("sprite"))
        pygame.event.clear()
        battle = GuestTrainerBattle(game, team, self, info["eid"], trainer_sprite=sprite, trainer_class=info["class"], trainer_name=info["name"],
                                    custom_dialogue=info.get("dialogue"), rewards=info.get("rewards"), battle_type=info.get("battle_type"),
                                    is_boss_battle=info.get("boss", False), area_name=info.get("area"), background_image=info.get("bg"))
        battle.coop_bg = info.get("bg")
        lines = info.get("lines") or []
        if info.get("on_map") and self.grid:  # (fought here on the map: its words in the map's text box, then the fight)
            mover = types.SimpleNamespace(kind="trainer", x=info["x"], y=info["y"], facing=tuple(info.get("f") or (0, 1)))
            battle.overworld = owb.OverworldView(self, mover)
            self.ow_stander = {"k": "t", "x": mover.x, "y": mover.y, "sprite": info.get("sprite"), "f": list(mover.facing)}
            self._report()
            name = info.get("name") or "A trainer"
            self.reading = [f"{name}: {line}" for line in lines] or [f"{name} wants to battle!"]
            self.after_reading = lambda: self.game.change_state(battle)
        else:
            game.change_state(TrainerIntroState(game, sprite, lines or ["Prepare to battle!"], battle))

    def _start_fight(self, info):
        from src.coop.guest_battle import GuestWildBattle
        self.asking, self.fighting = False, True
        story, game = self.game.story_manager, self.game
        rec, form = info["rec"], info["rec"].get("form", "normal")
        raw = game.loader.fetch_specific(rec["id"], form="normal" if form == "gmax" else form, is_shiny=rec.get("shiny", False))
        foe = Pokemon(raw, game.assets, size_mult=3.125)
        story._apply_record(foe, rec, form)
        pygame.event.clear()
        battle = GuestWildBattle(game, foe, info.get("area") or self.area, info.get("bg"), self, info["eid"])
        battle.coop_bg = info.get("bg")
        if info.get("on_map") and self.grid:  # (the host's BATTLE STYLE: OVERWORLD: fought here on the map)
            battle.overworld = owb.OverworldView(self, types.SimpleNamespace(kind="wild", x=info["x"], y=info["y"], facing=(0, 1)))
            self._report()
        game.change_state(battle)

    def fight_over(self, eid, outcome, ball):
        """Back from a fight: tell the host (again after a dropped connection, till it answers)."""
        story = self.game.story_manager
        self.fighting, self._ow_foe, self.ow_stander = False, None, None
        if not self._healthy_team():  # (follower-only, near the host, till they revive or everyone's out)
            self.down = True
            self.say_note("Your team fainted! Stay close to a friend.")
        self.outbox = {"fight_end": {"eid": eid, "outcome": outcome, "ball": ball, "team": self._team_records(), "ledger": self._ledger()}}
        self.link.send_intent(self.outbox)
        self.path, self.want = [], None
        pygame.event.clear()
        self.game.change_state(self)

    def _facing_sign(self):
        t = (self.player[0] + self.facing[0], self.player[1] + self.facing[1])
        if t in self.signs:
            self.reading, self.path = self.signs[t], []

    def _use(self, t):
        if t in self.signs:
            self.reading = self.signs[t]
        elif t in self.wilds:
            self._ask_fight(self.wilds[t])
        elif t in self.trainers:
            self._ask_trainer(self.trainers[t])
        elif t in self.doors:
            self._enter(self.doors[t])

    def _enter(self, kind):
        """The buildings a guest uses: the Center (heals, and the PC to swap Pokemon) and the Mart."""
        if kind == "center":
            self._heal_and_swap()
        elif kind == "mart":
            self.game.change_state(_GuestMart(self.game, self))
        else:
            self.say_note("The host goes in there.")

    def _team_records(self):
        story, team = self.game.story_manager, []
        for p in story.player_team:
            rec = story._pokemon_record(p)
            rec["uid"] = p.coop_uid
            team.append(rec)
        return team

    def _heal_and_swap(self):
        story = self.game.story_manager
        for p in story.player_team:
            p.heal_full()
        self.down = False
        self.say_note("Your team is healed!" if story.player_team else "Welcome!")
        self.link.send_intent({"team": self._team_records()})
        self.swapping = True
        self.link.send_intent({"roster_ask": True})

    def swap(self, uids):
        if uids and sorted(uids) != sorted(p.coop_uid for p in self.game.story_manager.player_team):
            self.link.send_intent({"exchange": list(uids)})
            self.say_note("Swapping at the PC...")

    def send_ledger(self):
        self.link.send_intent({"ledger": self._ledger()})

    def _ledger(self):
        story = self.game.story_manager
        return {"money": story.money, "items": dict(story.inventory), "balls": story.balls_left}

    def _tap_sign(self, t):
        """A tapped sign or wild Pokemon: from beside it, walking there first if need be."""
        for d in KEYS.values():
            if (self.player[0] + d[0], self.player[1] + d[1]) == t:
                self.facing, self.path = d, []
                self._use(t)
                return
        ways = [self._route((t[0] + d[0], t[1] + d[1])) for d in set(KEYS.values())]
        ways = [w for w in ways if w]
        if ways:
            self.path, self.want = min(ways, key=len), t

    def _route(self, goal):
        """The way to a tapped tile."""
        prev, todo = {self.player: None}, collections.deque([self.player])
        while todo:
            t = todo.popleft()
            if t == goal:
                out = []
                while prev[t] is not None:
                    out.append((t[0] - prev[t][0], t[1] - prev[t][1]))
                    t = prev[t]
                return out[::-1]
            for d in KEYS.values():
                n = (t[0] + d[0], t[1] + d[1])
                if n not in prev and self._open(n):
                    prev[n] = t
                    todo.append(n)
        return []

    def _camera(self):
        """The pixel the screen is centred on (a battle on the map: the fight, clear of its text box)."""
        px, py = self.player
        if self.anim > 0:
            k = 1 - self.anim / STEP
            fx, fy = self.anim_from
            px, py = fx + (px - fx) * k, fy + (py - fy) * k
        W, H = self.game.width, self.game.height
        cx, cy = px * TILE + TILE / 2, py * TILE + TILE / 2
        if self._backdrop and self._focus:
            cx, cy = self._focus[0], self._focus[1] + H * 0.14
        if self.surf:
            mw, mh = self.surf.get_size()
            cx = mw / 2 if mw <= W else min(max(cx, W / 2), mw - W / 2)
            cy = mh / 2 if mh <= H else min(max(cy, H / 2), mh - H / 2)
        return cx, cy

    def _origin(self):
        cx, cy = self._camera()
        return int(self.game.width / 2 - cx), int(self.game.height / 2 - cy)

    def draw_backdrop(self, screen):
        """Just the map and who's on it: behind a battle in the OVERWORLD style."""
        self._backdrop = True
        try:
            self.draw()
        finally:
            self._backdrop = False

    def _out(self, message=""):
        """Back to the lobby, with this device's own game put back as it was."""
        game = self.game
        game.story_manager, play, game.data.data = self._home
        if play is None:
            game.states.pop("play", None)
        else:
            game.states["play"] = play
        game.data.read_only = False
        self.lobby.link, self.lobby.entered, self.lobby.message = None, False, message
        game.change_state(self.lobby)

    def leave(self):
        self.link.leave()
        self._out()

    def handle_events(self, events):
        for e in events:
            if self.btn_leave.handle_event(e):
                return
            if self.feed and not self.fighting and self.btn_watch.handle_event(e):
                return
            if self._raid_open() and self.btn_raid.handle_event(e):
                return
            if self.vote:
                if self.btn_yes.handle_event(e) or self.btn_no.handle_event(e):
                    return
                continue
            if self.reading:
                if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or e.type == pygame.KEYDOWN:
                    self.reading = None
                    if self.after_reading:
                        go, self.after_reading = self.after_reading, None
                        go()
                        return
                continue
            if self._can_help() and self.btn_revive.handle_event(e):
                return
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._facing_sign()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.grid:
                ox, oy = self._origin()
                t = ((e.pos[0] - ox) // TILE, (e.pos[1] - oy) // TILE)
                self.want = None
                if t in self.signs or t in self.wilds or t in self.trainers or t in self.doors:
                    self._tap_sign(t)
                else:
                    self.path = self._route(t)

    def _try_reconnect(self):
        if self._busy_retry:
            return
        self._busy_retry = True
        link = self.link

        def work():
            try:
                self._retry = sess.GuestLink(link.host, link.port, link.session, "", link.name, token=link.token)
            except OSError:
                self._retry = None
            self._busy_retry = False
        threading.Thread(target=work, daemon=True).start()

    def pump(self):
        """The link, every frame, wherever the guest is (the map, a battle, the team picker). False: the session ended."""
        for msg in self.link.poll():
            if msg.get("t") == "state" and "watch" in msg:
                who = str(msg.get("who") or "")  # (nobody named: the host's own fight)
                if msg["watch"]:
                    self.feeds[who] = msg["watch"]
                else:
                    self.feeds.pop(who, None)
            elif msg.get("t") == "event":
                self._on_event(msg)
            elif msg.get("t") == "state" and isinstance(msg.get("host"), dict):
                self._on_host(msg["host"])
                if isinstance(msg.get("scene"), dict):
                    self._on_scene(msg["scene"])
        if self.link.status == "removed" or self.link.status == "invalid":
            self._out("The session has ended.")
            return False
        if self.link.lost:
            now = time.monotonic()
            self.reconnecting = self.reconnecting or now
            if now - self.reconnecting > RECONNECT_FOR:
                self._out("Lost the connection to the host.")
                return False
            if self._retry is not None:
                self._retry.poll()
                if self._retry.status == "allowed":  # (only once the host has taken the token back)
                    old, self.link = self.link, self._retry
                    self._retry = None
                    old.close()
                    self.reconnecting = None
                    self.asking = self.asked = False
                    self._report()
                    if self.outbox:
                        self.link.send_intent(self.outbox)
                elif self._retry.status != "connecting" or self._retry.lost:
                    self._retry.close()
                    self._retry = None
            elif not self._busy_retry:
                self._try_reconnect()
        return True

    def _on_event(self, msg):
        if "raid_joined" in msg:
            from src.states.coop_raid import CoopRaidState
            self.fighting, self.path, self.want = True, [], None
            self.game.change_state(CoopRaidState(self.game, self, lambda: self.feeds.get(""), self.host.get("name", "The host"), self.pump, self.link.pid))
        elif "raid_over" in msg:
            self.fighting = False
            self.feeds.pop("", None)
            if self.game.current_state.__class__.__name__ == "CoopRaidState":
                self.game.change_state(self)
            self.say_note("You won the raid!" if msg.get("won") else "The raid is over.")
        elif "wipe" in msg:
            for p in self.game.story_manager.player_team:
                p.heal_full()
            self.down, self.path = False, []
            self.say_note("Everyone fainted... back to the Pokemon Center.")
        elif "revived" in msg:
            got = msg["revived"]
            p = next((m for m in self.game.story_manager.player_team if m.coop_uid == got["uid"]), None)
            if p is not None:
                p.current_hp = got["hp"]
                p.status = None
                self.down = False
                self.say_note(f"{got['by']} revived your {p.display_name.upper()}!")
        elif "trainer_fight" in msg:
            self._start_trainer(msg["trainer_fight"])
        elif "vote" in msg:
            self.vote = msg["vote"]
        elif "vote_over" in msg:
            if self.vote and self.vote["id"] == msg["vote_over"]:
                self.vote = None
            if self.asked and not msg.get("went"):
                self._not_going("The answer was no.")
            elif msg.get("went"):
                self.asked = False
        elif "propose_no" in msg:
            self._not_going(str(msg["propose_no"]))
        elif "found" in msg:
            from src.pokemon import forms
            self.say_note(f"You found {forms.item_label(msg['found']).upper()}!")
        elif "ledger_now" in msg:
            story, now = self.game.story_manager, msg["ledger_now"]
            story.money, story.inventory, story.balls_left = now["money"], dict(now["items"]), now["balls"]
        elif "roster" in msg:
            self.roster = msg["roster"]
            if self.swapping:
                self.swapping = False
                if len(self.roster) > sum(1 for r in self.roster if r.get("mine")):  # (something to swap for)
                    from src.states.coop_borrow import CoopBorrowState
                    self.game.change_state(CoopBorrowState(self.game, self, self.roster, swapping=True))
        elif "lent" in msg:
            self._got_team(msg)
        elif "fight" in msg:
            self._start_fight(msg["fight"])
        elif "fight_no" in msg:
            self.asking = False
            self.say_note(str(msg["fight_no"]))
        elif "fight_done" in msg and self.outbox and self.outbox["fight_end"]["eid"] == msg["fight_done"]:
            self.outbox = None

    def update(self):
        if not self.pump() or self.game.current_state is not self:
            return
        if self.note_time > 0:
            self.note_time -= 1
        if self.roster is not None and not self.picked:
            self.picked = True
            if self.roster:
                from src.states.coop_borrow import CoopBorrowState
                self.game.change_state(CoopBorrowState(self.game, self, self.roster))
                return
            self.say_note("The host has no Pokemon to lend yet.")
        if self.anim > 0:
            self.anim -= 1
            return
        if self.reading or self.vote or self.asked:
            return
        held = pygame.key.get_pressed()
        for key, d in KEYS.items():
            if held[key]:
                self.path = []
                self._step(d)
                return
        if self.path:
            if not self._step(self.path.pop(0)):
                self.path = []
        elif self.want:  # (arrived beside the tapped sign)
            t, self.want = self.want, None
            if abs(t[0] - self.player[0]) + abs(t[1] - self.player[1]) == 1:
                self.facing = (t[0] - self.player[0], t[1] - self.player[1])
                self._use(t)

    def _rect(self, ox, oy, x, y):
        return pygame.Rect(ox + x * TILE, oy + y * TILE, TILE, TILE)

    def _draw_things(self, ox, oy):
        """Items and gates now; those who stand on the map come back to be drawn in order with the players."""
        screen, sc, out = self.game.screen, self.scene, []
        if not sc:
            return out
        bob = int(3 * math.sin(pygame.time.get_ticks() / 180))
        for x, y, kind in sc["gates"]:
            self._draw_gate(screen, self._rect(ox, oy, x, y), kind)
        for x, y, key in sc["items"]:
            img = self._item_img(key) or self._ball_img()
            screen.blit(img, img.get_rect(center=self._rect(ox, oy, x, y).center))
        for x, y in sc["tms"]:
            glow, img = self._rect(ox, oy, x, y).inflate(-8, -8), self._ball_img(38)
            pygame.draw.ellipse(screen, (255, 236, 140), glow, 3)
            screen.blit(img, img.get_rect(center=(glow.centerx, glow.centery + bob)))
        for x, y in sc["boulders"]:
            r = self._rect(ox, oy, x, y)
            img = self._sheet_frame("Object boulder.png", col=0, height=TILE - 4)
            screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - 2)))
        for m in sc["movers"] + ([self.ow_stander] if self.ow_stander else []):
            if self._ow_foe is not None and (m["x"], m["y"]) == (self._ow_foe.x, self._ow_foe.y):
                continue  # (the battle draws it, with its HP)
            out.append((m["y"], lambda m=m, r=self._rect(ox, oy, m["x"], m["y"]): self._draw_mover(screen, m, r)))
        return out

    def _pill(self, screen, text, cx, bottom):
        tag = self.game.assets.fonts["caption"].render(text, True, (255, 255, 255))
        pill = tag.get_rect(midbottom=(cx, bottom)).inflate(12, 6)
        pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
        screen.blit(tag, tag.get_rect(center=pill.center))

    def _draw_mover(self, screen, m, r):
        label = self.game.assets.fonts["label"]
        if m["k"] == "w":
            mon = types.SimpleNamespace(id=m["id"], meta_id=m["meta"], form=m["form"], is_shiny=m["shiny"])
            img = self._icon(mon, TILE, flip=m["x"] < self.player[0], facing=tuple(m["f"]))
            if img is not None:
                screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom + 4)))
            if m["shiny"]:
                pygame.draw.circle(screen, (255, 230, 90), (r.right - 8, r.y + 8), 5)
            if m["alert"]:
                theme.shadow_text(screen, "!", label, r.right - 6, r.y - 18, color=(220, 60, 50))
        elif m["k"] == "t":
            img = self._trainer_img({"sprite": m["sprite"]}, tuple(m["f"]))
            if img is not None:
                screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom)))
        else:
            img = self._figure_img(m["look"])
            if img is not None:
                screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - 2)))
            if m.get("town"):
                self._pill(screen, m.get("label", ""), r.centerx, r.y - 34)
            else:
                theme.shadow_text(screen, "!", label, r.right - 4, r.y - 20, color=(250, 210, 60))

    def _draw_reading(self, screen):
        font = self.game.assets.fonts["label"]
        W = self.game.width
        rows = []
        for line in self.reading:
            row = ""
            for word in str(line).split():
                if row and font.size(row + " " + word)[0] > W - 140:
                    rows.append(row)
                    row = word
                else:
                    row = (row + " " + word).strip()
            rows.append(row)
        h = 44 + len(rows) * (font.get_linesize() + 4)
        box = pygame.Rect(40, self.game.height - h - 20, W - 80, h)
        theme.draw_panel(screen, box)
        for i, row in enumerate(rows):
            theme.shadow_text(screen, row, font, box.x + 30, box.y + 22 + i * (font.get_linesize() + 4), color=(255, 255, 255),
                              shadow=(16, 20, 36))

    def draw(self):
        screen = self.game.screen
        screen.fill((10, 14, 24))
        font = self.game.assets.fonts["label"]
        if self.surf:
            ox, oy = self._origin()
            screen.blit(self.surf, (ox, oy))
            h = self.host
            people = self._draw_things(ox, oy)
            for o in self.host.get("others", []):  # (the other guests)
                at = o["at"]
                if o["pid"] != self.link.pid and at[0] == self.area and at[1] == self.floor:
                    who = (o.get("char"), o["name"], ox + at[2] * TILE, oy + at[3] * TILE, (at[4], at[5]))
                    people.append((at[3], lambda w=who: world.draw_person(self.game, *w)))
            if h.get("area") == self.area and h.get("floor") == self.floor:
                who = (h.get("char"), h.get("name", "Host"), ox + h["x"] * TILE, oy + h["y"] * TILE, tuple(h.get("f") or (0, 1)))
                people.append((h["y"], lambda w=who: world.draw_person(self.game, *w)))
            px, py = self.player
            if self.anim > 0:
                k = 1 - self.anim / STEP
                fx, fy = self.anim_from
                px, py = fx + (px - fx) * k, fy + (py - fy) * k
            me = (self.char, self.link.name, int(ox + px * TILE), int(oy + py * TILE), self.facing)
            people.append((py, lambda w=me: world.draw_person(self.game, *w)))
            for _y, paint in sorted(people, key=lambda p: p[0]):
                paint()
        else:
            theme.shadow_text(screen, "Waiting for the host to reach a map...", font, self.game.width // 2, 340,
                              color=(255, 255, 255), shadow=(16, 20, 36), align="center")
        if self._backdrop:
            return
        theme.shadow_text(screen, f"${self.game.story_manager.money:,}", font, 20, 22, color=(255, 255, 255), shadow=(16, 20, 36))
        self.btn_leave.draw(screen)
        if self.feed and not self.fighting:
            self.btn_watch.draw(screen)
        if self._raid_open():
            self.btn_raid.draw(screen)
        target = self._can_help()
        if target:
            self.btn_revive.text = f"REVIVE {target['name']}"[:22]
            self.btn_revive.draw(screen)
        note = "Reconnecting..." if self.link.lost else self.note if self.note_time > 0 else f"{self.host.get('name', 'The host')} is busy (a battle or a menu)" \
            if self.host.get("busy") else ""
        if note:
            tag = font.render(note, True, (255, 255, 255))
            pill = tag.get_rect(midtop=(self.game.width // 2, 20)).inflate(24, 12)
            pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=10)
            screen.blit(tag, tag.get_rect(center=pill.center))
        if self.reading:
            self._draw_reading(screen)
        if self.vote:
            panel = pygame.Rect(0, 230, 620, 160)
            panel.centerx = self.game.width // 2
            theme.draw_panel(screen, panel)
            theme.shadow_text(screen, f"{self.vote['who']} wants to go to {self.vote['label']}."[:48], font, panel.centerx, 262,
                              color=(255, 255, 255), shadow=(16, 20, 36), align="center")
            self.btn_yes.draw(screen)
            self.btn_no.draw(screen)
