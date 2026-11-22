"""The live 3D camera on the route maps (11-21, Jordan: "Bring live 3D to the route walker first").

The towns (walk_town.WalkTownState) already walk Black 2's own models through src/dungeon/live3d.py; the routes, caves
and other route-type places (dungeon.DungeonState) drew only the flat picture, so Route 19, Route 20, Pledge Grove and
everything after them never had the live view in play. This mixin gives the route walker the same: the scene from Black
2's camera following you (its moving strips' zoom and pan too), you and everyone else stood in it (trees and buildings
hide them), the ground you walk on worked out from the scene (live3d.Scene.walk_heights), no stepping off one level onto
another (both the 3D ground and Black 2's own heights must agree), and a tap read through the camera.

DungeonState keeps everything else (wild grass, Trainers, partners, scenes, the HUD): _draw_world_live hands back the
same tile-to-screen function the flat drawing does, so the overlays drawn after it land in the right place.
"""
import math

import pygame

from src.ui import theme

SS_THINGS = {"crack": "breakrock", "cut": "tree", "boulder": "rock"}   # (a map's obstacle -> SoulSilver's own picture, assets/tiles/ss/ow_<name>.png)
SS_THING_K = 1.3     # (their height in tiles per 16 of the game's pixels: as tall beside a person as on the DS)
LIVE_SPRITE = 1.5    # (as walk_town: a figure's height in tiles, per its picture's tiles)
LEVEL_STEP = 1.5     # (tiles: more than this between two neighbours' ground is a drop, not a step)
LIFT_STEP = 10.0     # (tiles: more than this is a lift carrying you, not a drop: 11-22, as walk_town)


class RouteLive:
    # ------------------------------------------------------------------ the scene
    def _dl_live(self):
        """(scene, the map's camera data) when this floor has Black 2's models and the card can draw them, else None."""
        roofs = getattr(self, "_live_roofs", None) or {}
        _p = roofs.get("_picture") or {}
        pic = str(_p.get("f") or "")
        if _p.get("when") or _p.get("until"):   # (a picture that changes with a flag has its own scene too: Cianwood Gym's
            from src.dungeon import art          #  waterfall, stopped by the switch at the top, 11-22)
            pic = str(art._version_file(_p) or pic)
        key = (getattr(self, "_floor_index", None), id(getattr(self, "_live_roofs", None)), pic)
        if getattr(self, "_dl_key", None) == key:
            return self._dl_got
        self._dl_key, self._dl_got = key, None
        from src.core import settings as _settings
        if getattr(self.game, "live3d", True) is False or not _settings.get(self.game.story_manager, "live3d"):
            return None
        if not pic.startswith(("b2_ground/", "ss_ground/")):
            return None
        try:   # (any trouble with the card or its libraries: the flat picture, never a crash)
            from src.dungeon import live3d
            if not live3d.available(self.game):
                return None
            sc = live3d.scene_of(self.game, pic, _p.get("at"), bool(roofs.get("_screen")) and pic.startswith("ss_ground/"))
        except Exception:
            return None
        if sc is None or sc.cam is None:
            return None
        f = self.run.floor
        if not sc.covers([(x, int(round(sc.wz(x, y)))) for y in range(f.h) for x in range(f.w) if f.walkable(x, y)]):   # (wz: a Johto room's moved grid, 11-21)
            return None
        self._dl_got = (sc, roofs.get("_cam") or {})
        self._dl_yaw = None
        return self._dl_got

    def _dl_height(self, fx, fy):
        """The ground's height (tiles) under (fx, fy), blended between tiles (a kerb a slope mid-step)."""
        sc, cam = self._dl_live()
        lift, k = cam.get("lift") or [], float(cam.get("lift_k") or 1.0) or 1.0
        base = float(cam.get("base") or 0.0)
        memo = self.__dict__.setdefault("_dl_ground", {})
        mk = (id(sc), self.area_key, self.run.index)
        if mk not in memo:
            f = self.run.floor
            near = lambda a, b: float(lift[b][a]) / k + base if 0 <= b < len(lift) and 0 <= a < len(lift[b]) else None
            _g = getattr(self, "_live_grid", None) or []
            _ch = lambda t: _g[t[1]][t[0]] if t[1] < len(_g) and t[0] < len(_g[t[1]]) else "."
            _ts = [(x, y) for y in range(f.h) for x in range(f.w) if f.walkable(x, y) or (x, y) in f.exits]
            memo[mk] = sc.walk_heights(_ts, near, high=[t for t in _ts if _ch(t) in "|;"], low=[t for t in _ts if _ch(t) in "o~x"])   # (a bridge's deck, the water: 11-22)
        G = memo[mk]
        x, y = int(round(fx)), int(round(fy))
        own = G.get((x, y))
        if own is None:
            if 0 <= y < len(lift) and 0 <= x < len(lift[y]):
                return float(lift[y][x]) / k + base
            return base
        x0, y0 = int(math.floor(fx)), int(math.floor(fy))
        ax, ay = fx - x0, fy - y0
        c = [[G.get((x0 + i, y0 + j), own) for i in (0, 1)] for j in (0, 1)]
        return (c[0][0] * (1 - ax) + c[0][1] * ax) * (1 - ay) + (c[1][0] * (1 - ax) + c[1][1] * ax) * ay

    def _dl_feet(self):
        """Where you are now (tiles, mid-step too)."""
        from src.states.overworld.dungeon import STEP_FRAMES
        k = 1 - self.anim / STEP_FRAMES if self.anim > 0 else 1
        (fx, fy), (tx, ty) = (self.anim_from if self.anim > 0 else self.run.player), self.run.player
        return fx + (tx - fx) * k, fy + (ty - fy) * k

    def _dl_cam(self):
        """Black 2's camera for this place, following you (a moving strip's zoom and pan, a scene's look elsewhere)."""
        from src.dungeon import live3d
        sc, _cam = self._dl_live()
        c = [float(v) for v in sc.cam]
        focus = getattr(self, "_cam_focus", None)
        fx, fy = focus if focus else self._dl_feet()
        px, pz = fx + 0.5, sc.wz(fx, fy) + 0.5
        py = self._dl_height(fx, fy)
        zone = None if focus else self._cam_zone(fx, fy)
        if zone:   # (a moving strip from the game file: Route 4's, the view slides as you cross it)
            px, pz = px + zone[1][0], pz + zone[1][1]
        base = float((getattr(self, "_live_map", None) or {}).get("camera_zoom") or 1.0)
        closer = max(0.25, float(getattr(self, "zoom", 1.0) or 1.0) / max(0.05, base))
        return live3d.follow(px + c[3], py + c[4], pz + c[5], c[0], c[1] / closer, 0.0, c[2])

    def _ss_thing(self, name):
        """SoulSilver's own picture of a thing on the map (a cracked rock, a boulder, a small tree), four times its size, crisp."""
        cache = self.game.__dict__.setdefault("_ss_things", {})
        if name not in cache:
            import os
            try:
                img = pygame.image.load(os.path.join(self.game.assets.assets_dir, "tiles", "ss", f"ow_{name}.png")).convert_alpha()
                cache[name] = pygame.transform.scale(img, (img.get_width() * 4, img.get_height() * 4))
            except Exception:
                cache[name] = None
        return cache[name]

    # ------------------------------------------------------------------ walking
    def _level_edge(self, a, b):
        """True when a -> b steps off one level onto another: Black 2 never lets you step between two tiles at different
        heights; the 3D ground and Black 2's own heights must both say it's a drop. Ledges, bridges and the tiles beside
        them, ways out, water are never edges (11-21, as walk_town._level_edge)."""
        if not self._dl_live():
            return False
        f = self.run.floor
        grid = getattr(self, "_live_grid", None) or []
        for t in (a, b):
            if not (0 <= t[0] < f.w and 0 <= t[1] < f.h) or t in f.exits or f.decor.get(t):
                return False
            ch = grid[t[1]][t[0]] if t[1] < len(grid) and t[0] < len(grid[t[1]]) else "."
            if ch not in ".\"":
                return False
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                q = (t[0] + dx, t[1] + dy)
                if 0 <= q[1] < len(grid) and 0 <= q[0] < len(grid[q[1]]) and grid[q[1]][q[0]] in "|;":
                    return False
        _diff = abs(self._dl_height(*a) - self._dl_height(*b))
        if _diff <= LEVEL_STEP:
            return False
        if getattr(self._dl_live()[0], "bdhc", None) is not None:
            # (SoulSilver's places, 11-22: the heights ARE the game's own floors, so the drop is real with no second
            # opinion needed. The DS never lets you step between two floors far apart; our walk grid only says walkable,
            # so in Goldenrod Gym you stepped straight from the floor up onto a walkway three levels over it. A LIFT is
            # the one place the game carries you between far levels: more than LIFT_STEP apart is one (Violet Gym's
            # platform, 29 levels), never an edge. Nor is a tile where the game has two floors, one over the other
            # (Goldenrod Gym's walkway over the arch you pass under on the way to Whitney, Tohjo Falls' path behind the
            # water): our grid has one tile for both, so levels cross there.)
            if self._dl_live()[0].stacked(*a) or self._dl_live()[0].stacked(*b):
                return False
            return _diff <= LIFT_STEP
        cam = self._dl_live()[1]
        lift, k = cam.get("lift") or [], float(cam.get("lift_k") or 1.0) or 1.0
        b2 = [lift[t[1]][t[0]] / k if 0 <= t[1] < len(lift) and 0 <= t[0] < len(lift[t[1]]) else None for t in (a, b)]
        return None not in b2 and abs(b2[0] - b2[1]) > LEVEL_STEP

    def _dl_tile_at(self, pos):
        """The tile under the finger, through the live camera (on the ground where you stand)."""
        v = self._view()
        sc = self._dl_live()[0]
        hit = sc.pick(v.size, self._dl_cam(), pos[0] - v.x, pos[1] - v.y, self._dl_height(*self.run.player))
        return sc.tile_of(hit[0], hit[2], tuple(self.run.player)) if hit else tuple(self.run.player)

    # ------------------------------------------------------------------ drawing
    def _draw_world_live(self, screen, view, fonts):
        """The map from Black 2's camera with everyone stood in it; returns at(x, y) -> the tile's screen rect."""
        from src.states.overworld.dungeon import STEP_FRAMES, TILE
        from src.dungeon import core
        sc, _cam = self._dl_live()
        cam = self._dl_cam()
        size = view.size
        f = self.run.floor
        h = self._dl_height
        sprites, shadows, emotes = [], [], []

        def put(img, fx, fy, lift=0.0):
            if img is not None:
                sprites.append((img, (fx + 0.5, h(fx, fy) + lift, sc.wz(fx, fy) + 0.55), img.get_height() / TILE * LIVE_SPRITE))
                shadows.append((fx + 0.5, h(fx, fy), sc.wz(fx, fy) + 0.55))
        for (x, y), key in f.items.items():   # (an item lying about)
            if (x, y) in f.seen:
                put(self._item_img(key) or self._ball_img(), x, y)
        if getattr(sc, "bdhc", None) is not None:   # (SoulSilver's own obstacles: to the game they are people, not part of the map's
            for (x, y), what in f.decor.items():      #  model, so the scene has none; 11-22: Tohjo Falls' hidden room had lost its rocks)
                thing = SS_THINGS.get(str(what).split(":")[0])
                img = self._ss_thing(thing) if thing and (x, y) in f.seen else None
                if img is not None:   # (on the game's own floor there: our map calls the tile a wall, whose height is under it)
                    near = [h(*q) for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if f.walkable(*q)]
                    want = sum(near) / len(near) if near else h(x, y)
                    hy = min(sc.surfaces(x, y) or [h(x, y)], key=lambda v: abs(v - want))
                    sprites.append((img, (x + 0.5, hy, sc.wz(x, y) + 0.55), img.get_height() / 4 / 16 * SS_THING_K))
        for m in f.movers:
            if not self.run.visible(m.x, m.y) or m is self._ow_foe or getattr(m, "_vs_hidden", False):
                continue
            mo = getattr(m, "motion", None)
            fx, fy = mo.at() if mo is not None else (m.x, m.y)
            if mo is not None and mo.emote > 0:
                emotes.append((fx, fy))
            if m.kind == "wild":
                img = self._icon(m.payload, TILE, flip=(m.x < self.run.player[0]), facing=getattr(m, "facing", None))
            elif m.kind == "escort":
                from src.world import escorts as _esc
                _lm = getattr(_esc.leader_of(m), "motion", None)
                img = _esc.image(self, m, _lm.frame() if _lm is not None else 0)
            elif m.kind == "figure":
                img = self._figure_img(m.payload, mo.facing, mo.frame()) if mo is not None else self._figure_img(m.payload)
            else:
                img = self._trainer_img(m.payload[1], m.facing, mo.frame() if mo is not None else 0)
            put(img, fx, fy)
        for a in self._scenes().actors:   # (a scene's cast)
            ax, ay = a["m"].at()
            put(self._actor_img(a["sheet"], a["m"].facing, a["m"].frame(), native=bool(a.get("native"))), ax, ay)
        # you, with your lead Pokemon a step behind (a hop over a ledge: up and down again)
        k = 1 - self.anim / STEP_FRAMES if self.anim > 0 else 1
        mfx, mfy = self._dl_feet()
        hop = math.sin(math.pi * k) * 0.55 if self.hop and self.anim > 0 else 0.0
        me = self._player_img()
        lead = self.follower()
        surfing = self._on_surf() or (self.anim > 0 and self._on_surf(self.anim_from))
        if surfing and me is not None:   # (on the water you ride your Pokemon, as the flat map draws it: 11-22, the Johto
            # review: "no Surf mount, you stand on the water". The same sheet, bobbing; you sit a little up on it.)
            ride = self._sheet_frame("base_surf.png", self.facing, col=(pygame.time.get_ticks() // 160) % 4, height=int(TILE * 0.95))
            me = self._extra_frame("surf", self.facing, 0) or me
            if ride is not None:
                put(ride, mfx, mfy - 0.02, 0.03 * math.sin(pygame.time.get_ticks() / 180))
                hop += 0.3
            lead = None
        if lead and self.partner != self.run.player and me is not None and not self._backdrop:
            (ax, ay), (bx, by) = self.partner_from, self.partner
            way = (self.run.player[0] - bx, self.run.player[1] - by)
            way = (max(-1, min(1, way[0])), 0) if way[0] else (0, max(-1, min(1, way[1])) or 1)
            put(self._icon(lead, TILE, flip=(self.run.player[0] > bx), facing=way), ax + (bx - ax) * k, ay + (by - ay) * k)
        put(me, mfx, mfy, hop)
        screen.fill((0, 0, 0), view)
        screen.blit(sc.render(size, cam, sprites, shadows=shadows if getattr(self, "shadows", False) else (), you=me), view.topleft)

        def at(x, y):
            p = sc.project(size, cam, (x + 0.5, h(x, y), sc.wz(x, y) + 0.55))
            if p is None:
                return pygame.Rect(-999, -999, TILE, TILE)
            return pygame.Rect(int(view.x + p[0] - TILE / 2), int(view.y + p[1] - TILE), TILE, TILE)
        screen.set_clip(view)
        self._draw_tap_marks(screen, at)
        # the ways out: one sign over each road saying where it goes (as the flat map does)
        ways = {}
        for (x, y), target in f.exits.items():
            if str(target).startswith("WARP:") or target == "BOSS":
                continue
            ways.setdefault(target, []).append((x, y))
        for target, tiles in ways.items():
            tiles.sort()
            r = at(*tiles[len(tiles) // 2])
            name = (self._floor_name(self.run.index + (1 if target == core.STAIRS else -1))
                    if target in (core.STAIRS, core.STAIRS_UP) else self._area_name(target))
            tag = fonts["caption"].render(theme.pokemon_word(str(name).upper()), True, (255, 255, 255))
            pill = tag.get_rect(center=r.center).inflate(12, 6)
            if view.inflate(120, 120).colliderect(pill):
                pill.clamp_ip(view.inflate(-8, -8))
                pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
                screen.blit(tag, tag.get_rect(center=pill.center))
        from src.world import poke_radar as _radar, dexnav as _dexnav, phenomena as _phen
        _radar.draw(self, screen, at)
        _dexnav.draw(self, screen, at)
        _phen.draw(self, screen, at)
        for ex, ey in emotes:
            r = at(int(round(ex)), int(round(ey)))
            theme.shadow_text(screen, "!", fonts["label"], r.centerx - 4, r.y - 34, color=(230, 60, 50))
        screen.set_clip(None)
        return at
