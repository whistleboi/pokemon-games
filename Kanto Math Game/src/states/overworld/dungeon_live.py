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

LIVE_SPRITE = 1.5    # (as walk_town: a figure's height in tiles, per its picture's tiles)
LEVEL_STEP = 1.5     # (tiles: more than this between two neighbours' ground is a drop, not a step)


class RouteLive:
    # ------------------------------------------------------------------ the scene
    def _dl_live(self):
        """(scene, the map's camera data) when this floor has Black 2's models and the card can draw them, else None."""
        key = (getattr(self, "_floor_index", None), id(getattr(self, "_live_roofs", None)))
        if getattr(self, "_dl_key", None) == key:
            return self._dl_got
        self._dl_key, self._dl_got = key, None
        from src.core import settings as _settings
        if getattr(self.game, "live3d", True) is False or not _settings.get(self.game.story_manager, "live3d"):
            return None
        roofs = getattr(self, "_live_roofs", None) or {}
        pic = str((roofs.get("_picture") or {}).get("f") or "")
        import os
        name = os.path.splitext(os.path.basename(pic))[0]
        if not pic.startswith("b2_ground/") or not name.isdigit():
            return None
        try:   # (any trouble with the card or its libraries: the flat picture, never a crash)
            from src.dungeon import live3d
            if not live3d.has_scene(self.game, int(name)) or not live3d.available(self.game):
                return None
            sc = live3d.scene(self.game, int(name))
        except Exception:
            return None
        if sc is None or sc.cam is None:
            return None
        f = self.run.floor
        if not sc.covers([(x, y) for y in range(f.h) for x in range(f.w) if f.walkable(x, y)]):
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
            memo[mk] = sc.walk_heights([(x, y) for y in range(f.h) for x in range(f.w) if f.walkable(x, y) or (x, y) in f.exits], near)
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
        px, pz = fx + 0.5, fy + 0.5
        py = self._dl_height(fx, fy)
        zone = None if focus else self._cam_zone(fx, fy)
        if zone:   # (a moving strip from the game file: Route 4's, the view slides as you cross it)
            px, pz = px + zone[1][0], pz + zone[1][1]
        base = float((getattr(self, "_live_map", None) or {}).get("camera_zoom") or 1.0)
        closer = max(0.25, float(getattr(self, "zoom", 1.0) or 1.0) / max(0.05, base))
        return live3d.follow(px + c[3], py + c[4], pz + c[5], c[0], c[1] / closer, 0.0, c[2])

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
        if abs(self._dl_height(*a) - self._dl_height(*b)) <= LEVEL_STEP:
            return False
        cam = self._dl_live()[1]
        lift, k = cam.get("lift") or [], float(cam.get("lift_k") or 1.0) or 1.0
        b2 = [lift[t[1]][t[0]] / k if 0 <= t[1] < len(lift) and 0 <= t[0] < len(lift[t[1]]) else None for t in (a, b)]
        return None not in b2 and abs(b2[0] - b2[1]) > LEVEL_STEP

    def _dl_tile_at(self, pos):
        """The tile under the finger, through the live camera (on the ground where you stand)."""
        v = self._view()
        sc = self._dl_live()[0]
        hit = sc.pick(v.size, self._dl_cam(), pos[0] - v.x, pos[1] - v.y, self._dl_height(*self.run.player))
        return (int(hit[0] // 1), int(hit[2] // 1)) if hit else tuple(self.run.player)

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
                sprites.append((img, (fx + 0.5, h(fx, fy) + lift, fy + 0.55), img.get_height() / TILE * LIVE_SPRITE))
                shadows.append((fx + 0.5, h(fx, fy), fy + 0.55))
        for (x, y), key in f.items.items():   # (an item lying about)
            if (x, y) in f.seen:
                put(self._item_img(key) or self._ball_img(), x, y)
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
        if lead and self.partner != self.run.player and me is not None and not self._backdrop:
            (ax, ay), (bx, by) = self.partner_from, self.partner
            way = (self.run.player[0] - bx, self.run.player[1] - by)
            way = (max(-1, min(1, way[0])), 0) if way[0] else (0, max(-1, min(1, way[1])) or 1)
            put(self._icon(lead, TILE, flip=(self.run.player[0] > bx), facing=way), ax + (bx - ax) * k, ay + (by - ay) * k)
        put(me, mfx, mfy, hop)
        screen.fill((0, 0, 0), view)
        screen.blit(sc.render(size, cam, sprites, shadows=shadows if getattr(self, "shadows", False) else ()), view.topleft)

        def at(x, y):
            p = sc.project(size, cam, (x + 0.5, h(x, y), y + 0.55))
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
