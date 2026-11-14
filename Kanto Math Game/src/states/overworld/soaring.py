"""Soaring in the Sky, the flight (Jordan, 11-14): "a behind-the-back 3rd person pov using the purple mega latia/os
sprite facing the opposite way ... the player sprite is the facing up version, on top of the pokemon. it is free
movement along the x axis while the y axis scrolls past to simulate flying movement."

You ride your Mega Latios / Latias (seen from behind) north over Hoenn; the ground scrolls down under you and loops.
Steer left and right (arrows / A D, or hold a finger or the mouse where you want to go); Up / Down or the FAST button
change speed. Wild Pokemon fly across: fly into one to battle it, or steer round it. Gusts of wind knock you aside.
Mirage spots glow on the ground (a red beacon over each while a legend there is still to catch): fly over one and you
can land there. Rifts and black clouds hang in the sky: fly into one to meet its legend. LAND (or Esc) sets you down
at the town below. What is where, and when: src/world/soaring.py.

This is the HOENN_SOARING_IN_THE_SKY area's screen (dungeon.dungeon_for hands it out, as Hyperspace Lumiose's): a
route underneath, so battles are the route's own and come back here, the flight going on where it was."""
import math
import os
import random

import pygame

from src.config import FPS
from src.states.overworld.route import PlayState
from src.ui import theme
from src.world import soaring

MOUNT_SCALE = 5               # Jordan's 31 x 30 sprite, five times
RIDER_H = 70
SPEEDS = (2.0, 3.6, 6.4)      # ground pixels a frame: slow, cruising, fast
STEER = 9.0                   # pixels a frame across at full turn
WILD_EVERY = (FPS * 4, FPS * 7)
GUST_EVERY = (FPS * 5, FPS * 9)
CLOUD_EVERY = (FPS * 2, FPS * 4)
HUD_H = 76
_cache = {}


def _img(game, name):
    if name not in _cache:
        try:
            _cache[name] = pygame.image.load(os.path.join(game.assets.assets_dir, "soaring", name)).convert_alpha()
        except (pygame.error, FileNotFoundError):
            _cache[name] = None
    return _cache[name]


def follower(game, pid, facing, height=84):
    """A Pokemon's following sheet (assets/dungeon/followers, Jordan 11-14: every overworld Pokemon), its row for the way
    it faces (down, left, right, up), stepping; whole-number scaled to about `height`. None if it has none."""
    key = ("follower", int(pid), height)
    if key not in _cache:
        frames = None
        try:
            img = pygame.image.load(os.path.join(game.assets.assets_dir, "dungeon", "followers", f"{int(pid)}.png")).convert_alpha()
            cw, ch = img.get_width() // 4, img.get_height() // 4
            box = None
            for c in range(4):
                for r in range(4):
                    b = img.subsurface((c * cw, r * ch, cw, ch)).get_bounding_rect()
                    if b.w and b.h:
                        box = b if box is None else box.union(b)
            box = box or pygame.Rect(0, 0, cw, ch)
            k = max(1, round(height / max(1, box.h)))
            frames = [[pygame.transform.scale(img.subsurface((c * cw + box.x, r * ch + box.y, box.w, box.h)), (box.w * k, box.h * k))
                       for c in range(4)] for r in range(4)]
        except (pygame.error, FileNotFoundError, ValueError):
            pass
        _cache[key] = frames
    frames = _cache[key]
    if not frames:
        return None
    row = {(0, 1): 0, (-1, 0): 1, (1, 0): 2, (0, -1): 3}.get(tuple(facing), 0)
    return frames[row][(pygame.time.get_ticks() // 160) % 4]


def cloud_picture(w, h, seed, dark=False):
    """A puffy pixel cloud of our own: round puffs, a shaded underside."""
    rng = random.Random(seed)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    body, shade = ((84, 80, 104), (52, 48, 70)) if dark else ((250, 252, 255), (206, 220, 238))
    puffs = [(rng.randint(w // 5, 4 * w // 5), rng.randint(h // 3, 2 * h // 3), rng.randint(h // 4, h // 2 - 2))
             for _ in range(7)]
    for x, y, r in puffs:
        pygame.draw.circle(s, shade, (x, y + 4), r)
    for x, y, r in puffs:
        pygame.draw.circle(s, body, (x, y), r - 2)
    small = pygame.transform.scale(s, (max(1, w // 4), max(1, h // 4)))   # (chunky, like the rest of the art)
    return pygame.transform.scale(small, (w, h))


class SoaringState(PlayState):

    def __init__(self, game, restore_data=None, classic=False):
        if getattr(self, "_soar_ready", False):   # back from a battle: the flight goes on where it was
            self._back_from_battle()
            return
        super().__init__(game, restore_data=restore_data, classic=True)
        self._soar_ready = True
        game.soaring_state = self
        story = game.story_manager
        self.area_key = story.current_area_key
        self.W, self.H = game.width, game.height
        self.rng = random.Random()
        self.ground = _img(game, "hoenn_ground.png")
        if self.ground is None:                   # (no picture: open sea)
            self.ground = pygame.Surface((1908, 1600))
            self.ground.fill((40, 112, 200))
        self.GW, self.GH = self.ground.get_size()
        self.minimap = pygame.transform.smoothscale(self.ground, (200, int(200 * self.GH / self.GW)))
        self.eon_id, self.eon_name = soaring.mount(game)
        base = _img(game, soaring.mount_picture(self.eon_id))
        self.mount_img = (pygame.transform.scale(base, (base.get_width() * MOUNT_SCALE, base.get_height() * MOUNT_SCALE))
                          if base else None)
        self.rider = self._rider()
        # where you are: on the ground picture (x across, y down); you start over the town you played the flute in
        came = getattr(story, "last_area_key", None) or "MOSSDEEP_CITY"
        self.spots = soaring.spots(story)
        start = (self._town_point(came) or next((s["at"] for s in self.spots if s.get("area") == came), None)
                 or soaring.ground_xy((401, 129)))
        self.wx, self.wy = float(start[0]), float(start[1])
        self.speed_i = 1
        self.speed = SPEEDS[1]
        self.tilt = 0.0
        self.knock = 0.0          # a gust's shove, wearing off
        self.t = 0
        self.mode = "FLY"         # FLY, ASK (a spot: land / fly in?), PAUSE (a line on screen)
        self.ask = None           # (spot, [(rect, label, colour, fn)])
        self.skip = set()         # spots you said no to (till you leave them)
        self.held = None          # where a finger / the mouse is held (steering)
        self.fast_held = False
        self.wilds, self.gusts, self.clouds = [], [], []
        self.next_wild = self.rng.randint(*WILD_EVERY)
        self.next_gust = self.rng.randint(*GUST_EVERY)
        self.next_cloud = FPS
        self.flash_text, self.flash_t = f"You're soaring on {self.eon_name}!", FPS * 3
        self.pool = self._get_wild_pool(self.area_data) or {"278": 1}
        self.spots = soaring.spots(story)

    # ---------------------------------------------------------------- the route underneath
    def _back_from_battle(self):
        self.mode = "FLY"
        self.ask = None
        self.held = None
        self.fast_held = False
        self.wilds = []
        self.spots = soaring.spots(self.game.story_manager)   # (a legend caught: its rift or beacon goes)
        self.next_wild = self.rng.randint(*WILD_EVERY)

    def _play_data(self):
        return {"balls_left": self.balls_left, "current_streak": self.current_streak,
                "rounds_completed": self.rounds_completed, "pending_wild_encounters": 0,
                "initial_round_active": False, "soaring": True}

    def start(self):
        self.game.ui_manager.elements.clear()
        pygame.event.clear()
        story = self.game.story_manager
        story.story_flags[f"visited_{self.area_key}"] = True

    def show_progression_menu(self):
        """A battle or its catch is over: fly on."""
        self.is_progression_paused = True
        self.p_data = [None] * 3
        self.catch_selection_active = False
        self.dialogue_box.visible = False
        self.mode = "FLY"
        self.ask = None

    def say(self, lines, then=None):
        def done():
            self.dialogue_box.visible = False
            if then:
                then()
            elif self.mode == "PAUSE":
                self.mode = "FLY"
        self.mode = "PAUSE"
        self.dialogue_box.reset(lines)
        self.dialogue_box.callback = done

    # ---------------------------------------------------------------- pictures
    def _rider(self):
        """You, from behind (your trainer's facing-up frame), cut off at the waist: sat on its back."""
        from src.coop import world
        char = str(getattr(self.game, "player_character", "") or "red")
        img = world.person_img(self.game, char, (0, -1), height=RIDER_H)
        if img is None:
            return None
        keep = int(img.get_height() * 0.74)
        return img.subsurface((0, 0, img.get_width(), keep)).copy()

    def _town_point(self, key):
        import json
        try:
            with open(os.path.join(self.game.assets.assets_dir, "map_points.json"), encoding="utf-8") as f:
                pts = (json.load(f).get("region_maps", {}).get("HOENN") or {}).get("points") or {}
        except (OSError, ValueError):
            return None
        return soaring.ground_xy(pts[key]) if key in pts else None

    # ---------------------------------------------------------------- where things are on screen
    def _me_screen(self):
        return self.W // 2 + int(self.wx - self._cam_x() - self.W // 2), int(self.H * 0.66)

    def _cam_x(self):
        return max(0.0, min(self.GW - self.W, self.wx - self.W / 2))

    def _cam_top(self):
        return self.wy - self.H * 0.66

    def _to_screen(self, gx, gy):
        """A ground point on screen (the ground loops north: the nearest copy)."""
        dy = (gy - self._cam_top()) % self.GH
        if dy > self.GH - self.H:
            dy -= self.GH
        return gx - self._cam_x(), dy

    def _me_rect(self):
        x, y = self._me_screen()
        return pygame.Rect(x - 50, y - 46, 100, 92)

    # ---------------------------------------------------------------- input
    def handle_events(self, events):
        for e in events:
            if self.dialogue_box.visible:
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.dialogue_box.advance()
                elif e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    self.dialogue_box.advance()
                continue
            if self.mode == "ASK":
                self._ask_event(e)
                continue
            if self.mode != "FLY":
                continue
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_l, pygame.K_AC_BACK):
                    self._ask_land()
                elif e.key in (pygame.K_UP, pygame.K_w):
                    self.speed_i = min(2, self.speed_i + 1)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.speed_i = max(0, self.speed_i - 1)
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self._land_rect().collidepoint(e.pos):
                    self._ask_land()
                elif self._fast_rect().collidepoint(e.pos):
                    self.fast_held = True
                else:
                    self.held = e.pos
            elif e.type == pygame.MOUSEMOTION and self.held is not None:
                self.held = e.pos
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self.held = None
                self.fast_held = False

    def _ask_event(self, e):
        _spot, buttons = self.ask
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for rect, _label, _c, fn in buttons:
                if rect.collidepoint(e.pos):
                    return fn()
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER, pygame.K_y):
                return buttons[0][3]()
            if e.key in (pygame.K_ESCAPE, pygame.K_n, pygame.K_AC_BACK):
                return buttons[-1][3]()

    def _land_rect(self):
        return pygame.Rect(self.W - 190, 12, 172, HUD_H - 24)

    def _fast_rect(self):
        return pygame.Rect(self.W - 190, self.H - 120, 172, 96)

    # ---------------------------------------------------------------- choices
    def _ask_box(self, spot, line, yes, yes_fn, no="FLY ON"):
        cx, y = self.W // 2, HUD_H + 30   # (high up: the spot below stays in sight)
        buttons = [(pygame.Rect(cx - 330, y + 70, 300, 76), yes, theme.POKEMON, yes_fn),
                   (pygame.Rect(cx + 30, y + 70, 300, 76), no, theme.BACK, self._fly_on)]
        self.ask = (spot, buttons)
        self.ask_line = line
        self.mode = "ASK"

    def _fly_on(self):
        spot = self.ask[0] if self.ask else None
        if spot is not None:
            self.skip.add(spot["key"])
        self.ask = None
        self.mode = "FLY"

    def _ask_land(self):
        key, name = soaring.nearest_town(self.game, self.wx, self.wy)
        self._ask_box(None, f"Land at {name}?", "LAND", lambda: self._land(key, f"{self.eon_name} set you down at {name}."),
                      no="KEEP FLYING")

    def _land(self, key, line=None):
        self.game.soaring_state = None
        self.mode = "GONE"
        from src.states.overworld.area_transition import AreaTransitionState
        from src.coop import travel
        if travel.held(self.game, travel.area_name(self.game, key), lambda: self._land(key, line)):
            return
        self.game.change_state(AreaTransitionState(self.game, key, initial_message=line))

    def _reach(self, spot):
        if spot["kind"] == "land":
            self._ask_box(spot, f"{spot['name']} is below you!", "LAND", lambda: self._land_on(spot))
            return
        what = "A huge gap has opened in the sky!" if spot["look"] == "rift" else "A black cloud is crackling with power!"
        self._ask_box(spot, what, "FLY IN", lambda: self._legend(spot))

    def _land_on(self, spot):
        """Down onto a Mirage spot: which legend is out is settled now, for this visit."""
        line = f"{self.eon_name} landed on {spot['name']}."
        if spot.get("place"):
            soaring.mark_place(self.game.story_manager, *spot["place"])
        if spot.get("legends"):
            if soaring.roll_visit(self.game.story_manager, spot, self.rng) is None and not soaring.caught_all(
                    self.game.story_manager, spot):
                line += " It's very quiet here this time..."
        self._land(spot["area"], line)

    def _legend(self, spot):
        self.ask = None
        boss = soaring.next_legend(self.game.story_manager, spot, self.area_data, self.rng)
        if not boss:
            self.mode = "FLY"
            return
        self.mode = "PAUSE"
        self.action_challenge_boss(dict(boss))

    def _wild(self, pid):
        """Into a wild Pokemon: a battle with it (the route's own, back here after)."""
        from src.pokemon.data import Pokemon
        from src.states.battle import WildBattleState
        from src.world import levels
        self.mode = "PAUSE"
        self.rounds_completed += 1
        pokemon = Pokemon(self.game.loader.fetch_specific(int(pid)), self.game.assets, size_mult=3.125)
        levels.set_wild(self.game, pokemon, self.area_key)
        self.game.data.mark_seen(pokemon.id)
        battle = WildBattleState(self.game, pokemon, self.area_key, background_image=self._get_battle_background_for_area())
        battle.play_state_data = self._play_data()
        pygame.event.clear()
        self.game.change_state(battle)

    # ---------------------------------------------------------------- the flight
    def update(self):
        self.t += 1
        if self.dialogue_box.visible:
            self.dialogue_box.update()
            return
        if self.flash_t > 0:
            self.flash_t -= 1
        if self.mode != "FLY":
            return
        keys = pygame.key.get_pressed()
        steer = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            steer -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            steer += 1
        if self.held is not None and not steer:
            dx = self.held[0] - self._me_screen()[0]
            steer = max(-1.0, min(1.0, dx / 120.0))
        fast = self.fast_held or (self.held is not None and self.held[1] < self.H * 0.3)
        want = SPEEDS[2] if fast else SPEEDS[self.speed_i]
        self.speed += (want - self.speed) * 0.08
        self.tilt += (steer - self.tilt) * 0.2
        self.wx = max(60.0, min(self.GW - 60.0, self.wx + self.tilt * STEER + self.knock))
        self.knock *= 0.88
        self.wy = (self.wy - self.speed) % self.GH
        self._spawn()
        self._move_things()
        self._check_spots()

    def _spawn(self):
        top = self._cam_top() - 120
        self.next_wild -= 1
        if self.next_wild <= 0:
            self.next_wild = self.rng.randint(*WILD_EVERY)
            from src.utils import Utils
            pid = int(Utils.weighted_random_choice(self.pool))
            side = self.rng.choice((-1, 1))
            x = self._cam_x() + (self.W + 80 if side < 0 else -80)
            self.wilds.append({"pid": pid, "x": x, "y": top + self.rng.randint(0, int(self.H * 0.35)),
                               "vx": side * self.rng.uniform(1.8, 3.4),
                               "vy": self.rng.uniform(-0.8, 0.6), "ph": self.rng.random() * 6})
        self.next_gust -= 1
        if self.next_gust <= 0:
            self.next_gust = self.rng.randint(*GUST_EVERY)
            self.gusts.append({"x": self._cam_x() + self.rng.randint(120, self.W - 120), "y": top,
                               "push": self.rng.choice((-1, 1)) * self.rng.uniform(9, 14), "hit": False})
        self.next_cloud -= 1
        if self.next_cloud <= 0:
            self.next_cloud = self.rng.randint(*CLOUD_EVERY)
            w = self.rng.randint(160, 320)
            self.clouds.append({"x": self._cam_x() + self.rng.randint(-100, self.W), "y": top - 80, "w": w,
                                "h": w // 2, "seed": self.rng.randint(0, 9999), "alpha": self.rng.randint(120, 190),
                                "drift": self.rng.uniform(-0.5, 0.5)})

    def _screen_y(self, wy):
        return wy - self._cam_top()

    def _move_things(self):
        me = self._me_rect()
        keep = []
        for w in self.wilds:
            w["x"] += w["vx"]
            w["y"] += w["vy"]
            sx, sy = w["x"] - self._cam_x(), self._screen_y(w["y"])
            if pygame.Rect(sx - 34, sy - 30, 68, 60).colliderect(me):
                return self._wild(w["pid"])
            if -140 < sx < self.W + 140 and sy < self.H + 100:
                keep.append(w)
        self.wilds = keep
        keep = []
        for g in self.gusts:
            sx, sy = g["x"] - self._cam_x(), self._screen_y(g["y"])
            if not g["hit"] and pygame.Rect(sx - 70, sy - 40, 140, 80).colliderect(me):
                g["hit"] = True
                self.knock = g["push"]
                self.speed = SPEEDS[0]
                self.flash_text, self.flash_t = "A gust of wind!", FPS
            if sy < self.H + 100:
                keep.append(g)
        self.gusts = keep
        self.clouds = [c for c in self.clouds if self._screen_y(c["y"]) < self.H + 200]
        for c in self.clouds:
            c["x"] += c["drift"]
        # (things are kept in ground y; when the ground loops, so do they)
        for group in (self.wilds, self.gusts, self.clouds):
            for o in group:
                if o["y"] - self._cam_top() > self.GH / 2:
                    o["y"] -= self.GH
                elif o["y"] - self._cam_top() < -self.GH / 2:
                    o["y"] += self.GH

    def _check_spots(self):
        mx, my = self._me_screen()
        for spot in self.spots:
            sx, sy = self._to_screen(*spot["at"])
            near = (sx - mx) ** 2 + (sy - my) ** 2 < (64 if spot["kind"] == "land" else 80) ** 2
            if not near:
                self.skip.discard(spot["key"])
            elif spot["key"] not in self.skip:
                return self._reach(spot)

    # ---------------------------------------------------------------- drawing
    def draw(self):
        screen = self.game.screen
        cx, top = self._cam_x(), self._cam_top()
        y0 = -(top % self.GH)
        y = y0
        while y < self.H:
            screen.blit(self.ground, (-int(cx), int(y)))
            y += self.GH
        for spot in self.spots:
            if spot["kind"] == "land":
                self._draw_land_spot(screen, spot)
        self._draw_shadows(screen)
        for g in self.gusts:
            self._draw_gust(screen, g)
        for spot in self.spots:
            if spot["kind"] == "sky":
                self._draw_sky_spot(screen, spot)
        for w in self.wilds:
            self._draw_wild(screen, w)
        self._draw_me(screen)
        for c in self.clouds:
            img = _cache.get(("cloud", c["seed"], c["w"]))
            if img is None:
                img = _cache[("cloud", c["seed"], c["w"])] = cloud_picture(c["w"], c["h"], c["seed"])
            img.set_alpha(c["alpha"])
            screen.blit(img, (int(c["x"] - cx), int(self._screen_y(c["y"]))))
        self._draw_hud(screen)
        if self.mode == "ASK" and self.ask:
            self._draw_ask(screen)
        if self.dialogue_box.visible:
            self.dialogue_box.draw(screen)

    def _draw_shadows(self, screen):
        sh = pygame.Surface((90, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
        mx, my = self._me_screen()
        screen.blit(sh, sh.get_rect(center=(mx + 40, my + 120)))
        for w in self.wilds:
            small = pygame.transform.scale(sh, (44, 16))
            screen.blit(small, small.get_rect(center=(int(w["x"] - self._cam_x()) + 30, int(self._screen_y(w["y"])) + 90)))

    def _draw_land_spot(self, screen, spot):
        sx, sy = self._to_screen(*spot["at"])
        if not (-120 < sx < self.W + 120 and -160 < sy < self.H + 120):
            return
        sx, sy = int(sx), int(sy)
        self._landmark(screen, spot["look"], sx, sy)
        pulse = 0.5 + 0.5 * math.sin(self.t / 6)
        ring = pygame.Surface((160, 100), pygame.SRCALPHA)
        pygame.draw.ellipse(ring, (255, 240, 160, int(90 + 120 * pulse)), ring.get_rect(), 5)
        screen.blit(ring, ring.get_rect(center=(sx, sy)))
        if spot.get("beacon"):                       # the red beacon floating over it (ORAS)
            by = sy - 70 - int(8 * math.sin(self.t / 5))
            pts = [(sx, by - 18), (sx + 12, by), (sx, by + 18), (sx - 12, by)]
            pygame.draw.polygon(screen, (230, 40, 50), pts)
            pygame.draw.polygon(screen, (255, 170, 170), [(sx, by - 12), (sx + 5, by - 2), (sx, by + 2)])
            pygame.draw.polygon(screen, (90, 10, 20), pts, 2)

    def _landmark(self, screen, look, x, y):
        """A small drawing of the place seen from high up (ours, in the ground's style)."""
        if look in ("island", "crescent", "plain"):
            if look == "crescent":
                pygame.draw.circle(screen, (232, 212, 136), (x, y), 34)
                pygame.draw.circle(screen, (40, 112, 200), (x + 16, y - 8), 30)
                pygame.draw.circle(screen, (112, 192, 80), (x - 6, y + 4), 18)
                pygame.draw.circle(screen, (40, 112, 200), (x + 12, y - 6), 20)
            else:
                pygame.draw.ellipse(screen, (232, 212, 136), (x - 46, y - 28, 92, 56))
                pygame.draw.ellipse(screen, (150, 210, 100) if look == "plain" else (112, 192, 80), (x - 38, y - 22, 76, 44))
        elif look == "forest":
            for dx, dy in ((-22, -6), (0, -14), (20, -4), (-8, 10), (14, 12)):
                pygame.draw.circle(screen, (30, 96, 40), (x + dx, y + dy + 3), 15)
                pygame.draw.circle(screen, (48, 136, 56), (x + dx, y + dy), 14)
        elif look in ("cave", "den"):
            rock = (120, 108, 100) if look == "cave" else (150, 170, 190)
            pygame.draw.ellipse(screen, rock, (x - 40, y - 26, 80, 52))
            pygame.draw.ellipse(screen, (20, 18, 26), (x - 14, y - 2, 28, 18))
        elif look == "mountain":
            pygame.draw.polygon(screen, (136, 104, 64), [(x - 44, y + 24), (x, y - 36), (x + 44, y + 24)])
            pygame.draw.polygon(screen, (240, 240, 250), [(x - 12, y - 20), (x, y - 36), (x + 12, y - 20)])

    def _draw_sky_spot(self, screen, spot):
        sx, sy = self._to_screen(*spot["at"])
        if not (-200 < sx < self.W + 200 and -200 < sy < self.H + 200):
            return
        sx, sy = int(sx), int(sy)
        if spot["look"] == "rift":                    # a dark ring, turning
            for i in range(4):
                a = self.t / 9 + i * math.pi / 2
                r = pygame.Rect(0, 0, 150 - i * 22, 90 - i * 14)
                r.center = (sx + int(4 * math.cos(a)), sy + int(4 * math.sin(a)))
                pygame.draw.ellipse(screen, ((120, 60, 200), (70, 20, 130), (40, 10, 80), (10, 0, 20))[i], r, 0 if i == 3 else 8)
        else:                                          # a black cloud with lightning
            img = _cache.get(("storm", spot["key"]))
            if img is None:
                img = _cache[("storm", spot["key"])] = cloud_picture(240, 130, hash(spot["key"]) % 999, dark=True)
            screen.blit(img, img.get_rect(center=(sx, sy)))
            if (self.t // 4) % 9 == 0:
                pts = [(sx - 10, sy + 20), (sx + 6, sy + 44), (sx - 6, sy + 48), (sx + 10, sy + 80)]
                pygame.draw.lines(screen, (255, 240, 120), False, pts, 4)

    def _draw_gust(self, screen, g):
        sx, sy = int(g["x"] - self._cam_x()), int(self._screen_y(g["y"]))
        if not (-100 < sy < self.H + 100):
            return
        for i in range(3):
            a = self.t / 4 + i * 2.1
            r = pygame.Rect(0, 0, 120 - i * 28, 46 - i * 10)
            r.center = (sx + int(10 * math.cos(a)), sy + int(6 * math.sin(a)))
            pygame.draw.arc(screen, (236, 244, 255), r, a, a + 4.2, 4)

    def _draw_wild(self, screen, w):
        img = follower(self.game, w["pid"], (1, 0) if w["vx"] > 0 else (-1, 0))
        if img is None:
            from src.minigames.base import icon
            img = icon(self.game, w["pid"], 76, flip=w["vx"] > 0)
        bob = int(6 * math.sin(self.t / 5 + w["ph"]))
        screen.blit(img, img.get_rect(center=(int(w["x"] - self._cam_x()), int(self._screen_y(w["y"])) + bob)))

    def _draw_me(self, screen):
        mx, my = self._me_screen()
        bob = int(5 * math.sin(self.t / 6))
        if self.mount_img is not None:
            img = pygame.transform.rotate(self.mount_img, -self.tilt * 12) if abs(self.tilt) > 0.05 else self.mount_img
            screen.blit(img, img.get_rect(center=(mx, my + bob)))
        else:
            pygame.draw.circle(screen, (150, 110, 210), (mx, my + bob), 50)
        if self.rider is not None:
            r = pygame.transform.rotate(self.rider, -self.tilt * 10) if abs(self.tilt) > 0.05 else self.rider
            screen.blit(r, r.get_rect(midbottom=(mx + int(self.tilt * 4), my + bob - 4)))

    def _draw_hud(self, screen):
        fonts = self.game.assets.fonts
        bar = pygame.Rect(12, 8, self.W - 214, HUD_H - 16)
        theme.draw_textbox(screen, bar)
        theme.shadow_text(screen, "Soaring in the Sky", fonts["button"], bar.x + 20, bar.centery - fonts["button"].get_height() // 2)
        _key, near = soaring.nearest_town(self.game, self.wx, self.wy)
        theme.shadow_text(screen, f"Over: near {near}", fonts["label"], bar.right - 20, bar.centery - 12, align="right")
        mouse = pygame.mouse.get_pos()
        r = self._land_rect()
        theme.command_button(screen, r, "LAND", fonts["button"], theme.BACK, hover=r.collidepoint(mouse))
        r = self._fast_rect()
        theme.command_button(screen, r, "FAST", fonts["button"], theme.POKEMON, hover=self.fast_held)
        # the mini-map: the ground, small, with you and the spots
        mm = self.minimap
        at = pygame.Rect(16, self.H - mm.get_height() - 16, mm.get_width(), mm.get_height())
        screen.blit(mm, at)
        pygame.draw.rect(screen, theme.TEXTBOX_FRAME, at.inflate(4, 4), 3)
        k = mm.get_width() / self.GW
        for spot in self.spots:
            col = (230, 40, 50) if spot.get("beacon") else (255, 230, 120)
            if spot["kind"] == "sky":
                col = (130, 70, 210)
            pygame.draw.circle(screen, col, (at.x + int(spot["at"][0] * k), at.y + int(spot["at"][1] * k)), 4)
        if (self.t // 6) % 2:
            pygame.draw.circle(screen, (255, 255, 255), (at.x + int(self.wx * k), at.y + int(self.wy * k)), 5)
        pygame.draw.circle(screen, (20, 20, 30), (at.x + int(self.wx * k), at.y + int(self.wy * k)), 5, 2)
        if self.flash_t > 0 and self.mode == "FLY":
            t = fonts["button"].render(self.flash_text, True, (255, 255, 255))
            pill = t.get_rect(center=(self.W // 2, HUD_H + 40)).inflate(30, 14)
            pygame.draw.rect(screen, (40, 30, 80), pill, border_radius=12)
            pygame.draw.rect(screen, (190, 150, 255), pill, 2, border_radius=12)
            screen.blit(t, t.get_rect(center=pill.center))

    def _draw_ask(self, screen):
        fonts = self.game.assets.fonts
        _spot, buttons = self.ask
        card = pygame.Rect(0, 0, 760, 200)
        card.center = (self.W // 2, HUD_H + 90)
        theme.draw_textbox(screen, card)
        theme.shadow_text(screen, self.ask_line, fonts["button"], card.centerx, card.y + 26, align="center")
        mouse = pygame.mouse.get_pos()
        for rect, label, colour, _fn in buttons:
            theme.command_button(screen, rect, label, fonts["button"], colour, hover=rect.collidepoint(mouse))
