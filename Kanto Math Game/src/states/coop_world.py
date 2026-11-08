"""A guest walking the host's map (Jordan, 11-08): the same drawn map, the host beside you. The game files are the same
on both devices, so only positions cross the network. The guest follows when the host changes area, for now."""
import collections
import threading
import time

import pygame

from src.coop import session as sess
from src.coop import world
from src.dungeon import art
from src.states.base import GameState
from src.states.overworld.walk_town import custom
from src.ui import theme
from src.ui.panels import CommandButton

TILE = world.TILE
STEP = 8
KEYS = {pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
        pygame.K_w: (0, -1), pygame.K_s: (0, 1), pygame.K_a: (-1, 0), pygame.K_d: (1, 0)}
RECONNECT_FOR = sess.GRACE_SECONDS
BLOCKED = set("ob")  # (water and boulders: not on foot; Surf and Strength are the host's journey for now)


class CoopWorldState(GameState):
    uses_keyboard = True

    def __init__(self, game, link, lobby):
        super().__init__(game)
        self.link, self.lobby = link, lobby
        self.area, self.floor, self.grid, self.surf = None, 0, None, None
        self.player, self.facing, self.anim, self.anim_from = (0, 0), (0, 1), 0, (0, 0)
        self.host = {}
        self.path = []
        self.char = "female"
        self.reconnecting, self._retry = None, None
        self._busy_retry = False
        self.btn_leave = CommandButton((game.width - 176, 14, 160, 56), "LEAVE", game.assets.fonts["label"], self.leave,
                                       bg_color=theme.FIGHT, autosize=False)

    # ------------------------------------------------------------------ the map
    def _load(self, area, floor):
        self.area, self.floor, self.grid, self.surf = area, floor, None, None
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

    def _open(self, t):
        x, y = t
        return bool(self.grid) and 0 <= y < len(self.grid) and 0 <= x < len(self.grid[0]) \
            and art.walkable(self.grid, x, y) and self.grid[y][x] not in BLOCKED

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
        if "area" not in info:
            return
        if (info["area"], info["floor"]) != (self.area, self.floor):
            self._load(info["area"], info["floor"])
            self.path = []
            self._arrive(info["x"], info["y"])
            self._report()

    def _report(self):
        p = [self.area, self.floor, self.player[0], self.player[1], self.facing[0], self.facing[1]]
        self.link.send_intent({"at": p, "char": self.char})

    # ------------------------------------------------------------------ walking
    def _step(self, d):
        t = (self.player[0] + d[0], self.player[1] + d[1])
        self.facing = d
        if self._open(t):
            self.anim_from, self.player, self.anim = self.player, t, STEP
            self._report()
            return True
        return False

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

    def _origin(self):
        px, py = self.player
        if self.anim > 0:
            k = 1 - self.anim / STEP
            fx, fy = self.anim_from
            px, py = fx + (px - fx) * k, fy + (py - fy) * k
        W, H = self.game.width, self.game.height
        cx, cy = px * TILE + TILE / 2, py * TILE + TILE / 2
        if self.surf:
            mw, mh = self.surf.get_size()
            cx = mw / 2 if mw <= W else min(max(cx, W / 2), mw - W / 2)
            cy = mh / 2 if mh <= H else min(max(cy, H / 2), mh - H / 2)
        return int(W / 2 - cx), int(H / 2 - cy)

    def leave(self):
        self.link.leave()
        self.lobby.link, self.lobby.entered, self.lobby.message = None, False, ""
        self.game.change_state(self.lobby)

    def handle_events(self, events):
        for e in events:
            if self.btn_leave.handle_event(e):
                return
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.grid:
                ox, oy = self._origin()
                self.path = self._route(((e.pos[0] - ox) // TILE, (e.pos[1] - oy) // TILE))

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

    def update(self):
        for msg in self.link.poll():
            if msg.get("t") == "state" and isinstance(msg.get("host"), dict):
                self._on_host(msg["host"])
        if self.link.status == "removed" or self.link.status == "invalid":
            self.lobby.link, self.lobby.entered, self.lobby.message = None, False, "The session has ended."
            self.game.change_state(self.lobby)
            return
        if self.link.lost:
            now = time.monotonic()
            self.reconnecting = self.reconnecting or now
            if now - self.reconnecting > RECONNECT_FOR:
                self.lobby.link, self.lobby.entered, self.lobby.message = None, False, "Lost the connection to the host."
                self.game.change_state(self.lobby)
                return
            if self._retry is not None:
                self._retry.poll()
                if self._retry.status == "allowed":  # (only once the host has taken the token back)
                    old, self.link = self.link, self._retry
                    self._retry = None
                    old.close()
                    self.reconnecting = None
                    self._report()
                elif self._retry.status != "connecting" or self._retry.lost:
                    self._retry.close()
                    self._retry = None
            elif not self._busy_retry:
                self._try_reconnect()
        if self.anim > 0:
            self.anim -= 1
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

    def draw(self):
        screen = self.game.screen
        screen.fill((10, 14, 24))
        font = self.game.assets.fonts["label"]
        if self.surf:
            ox, oy = self._origin()
            screen.blit(self.surf, (ox, oy))
            h = self.host
            people = []
            if h.get("area") == self.area and h.get("floor") == self.floor:
                people.append((h["y"], h.get("char"), h.get("name", "Host"), ox + h["x"] * TILE, oy + h["y"] * TILE))
            px, py = self.player
            if self.anim > 0:
                k = 1 - self.anim / STEP
                fx, fy = self.anim_from
                px, py = fx + (px - fx) * k, fy + (py - fy) * k
            people.append((py, self.char, self.link.name, int(ox + px * TILE), int(oy + py * TILE)))
            for _y, char, name, sx, sy in sorted(people, key=lambda p: p[0]):
                world.draw_person(self.game, char, name, sx, sy)
        else:
            theme.shadow_text(screen, "Waiting for the host to reach a map...", font, self.game.width // 2, 340,
                              color=(255, 255, 255), shadow=(16, 20, 36), align="center")
        self.btn_leave.draw(screen)
        note = "Reconnecting..." if self.link.lost else f"{self.host.get('name', 'The host')} is busy (a battle or a menu)" \
            if self.host.get("busy") else ""
        if note:
            tag = font.render(note, True, (255, 255, 255))
            pill = tag.get_rect(midtop=(self.game.width // 2, 20)).inflate(24, 12)
            pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=10)
            screen.blit(tag, tag.get_rect(center=pill.center))
