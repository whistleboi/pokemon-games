"""Co-op's front door (Jordan, 11-08): the host opens a session from Options; a friend's device picks JOIN SESSION on
the title screen. For now it connects the two devices and shows the link working; the shared map comes next."""
import threading

import pygame

from src.coop import session as sess
from src.coop import world
from src.net import discovery
from src.states.base import GameState
from src.ui import theme
from src.ui.panels import CommandButton

WHY = {"invalid": "That name or password didn't match.", "full": "That session is full.",
       "closed": "That session isn't taking new players.", "denied": "The host said no.",
       "expired": "The host didn't answer in time.", "rate_limited": "Too many wrong tries. Wait a minute.",
       "version": "Your game and the host's don't match. Update both.", "removed": "You left the session.",
       "unreachable": "Couldn't reach the host. Try typing the host's address.",
       "not found": "Couldn't find that session. Try typing the host's address."}


class CoopState(GameState):
    uses_keyboard = True
    keep_keyboard = True  # (Enter on a phone moves to the next box: the keyboard stays up)

    def __init__(self, game, back, mode):
        super().__init__(game)
        self.back, self.mode = back, mode  # "host" or "join"
        f = game.assets.fonts
        self.f = f
        self.title = game.assets._load_font(40, bold=True)
        self.small = game.assets._load_font(22, bold=False)
        self.text = game.assets._load_font(28, bold=True)
        self.fields = []
        y = 130
        names = (("Session name", "name"), ("Password", "password")) if mode == "host" else \
            (("Session name", "name"), ("Password", "password"), ("Your name", "me"), ("Host address (optional)", "address"))
        for label, key in names:
            self.fields.append({"label": label, "key": key, "text": "", "rect": pygame.Rect(440, y, 500, 54)})
            y += 72
        self.active = 0
        self.message = ""
        self.reveal = False
        self.link = None                  # (a guest's)
        self.busy = False
        self.entered = False
        self._found = None
        w = game.width
        self.btn_back = CommandButton((16, 14, 140, 56), "BACK", f["button"], self.go_back, bg_color=theme.BACK, autosize=False)
        label = "OPEN SESSION" if mode == "host" else "JOIN"
        self.btn_go = CommandButton((440, y + 12, 300, 66), label, f["label"], self.go, bg_color=theme.POKEMON, autosize=False)
        self.btn_reveal = CommandButton((960, 202, 170, 54), "REVEAL", f["label"], self.toggle_reveal, bg_color=theme.RUN, autosize=False)
        self.btn_close = CommandButton((w - 340, 620, 300, 66), "CLOSE SESSION" if mode == "host" else "LEAVE",
                                       f["label"], self.end, bg_color=theme.FIGHT, autosize=False)
        self.btn_allow = CommandButton((640, 330, 170, 60), "ALLOW", f["label"], lambda: self.answer(True), bg_color=theme.POKEMON, autosize=False)
        self.btn_deny = CommandButton((830, 330, 170, 60), "DENY", f["label"], lambda: self.answer(False), bg_color=theme.FIGHT, autosize=False)

    # ------------------------------------------------------------------ typing
    def text_input_rect(self):  # (a phone's keyboard opens on a tap: src/core/android.py)
        """All the boxes together: a tap on any of them brings up the keyboard."""
        return self.fields[0]["rect"].unionall([f["rect"] for f in self.fields[1:]]) if self._form_showing() else None

    def _form_showing(self):
        if self.mode == "host":
            return getattr(self.game, "coop_host", None) is None
        return self.link is None and not self.busy

    # ------------------------------------------------------------------ actions
    def value(self, key):
        return next(f["text"].strip() for f in self.fields if f["key"] == key)

    def go_back(self):
        self.game.change_state(self.back)  # (a host's session stays open; a guest's link too, till LEAVE)

    def toggle_reveal(self):
        self.reveal = not self.reveal

    def go(self):
        if not self.value("name") or not self.value("password"):
            self.message = "Type a session name and a password first."
            return
        if self.mode == "host":
            self._open()
        else:
            self._join()

    def _open(self):
        name = self.value("name")
        if discovery.find(name, timeout=0.5):
            self.message = "That session name is already in use nearby."
            return
        try:
            self.game.coop_host = sess.HostSession(name, self.value("password"), seats=1)
            self.message = ""
        except OSError:
            self.message = "Couldn't open the session on this network."

    def _join(self):
        self.busy, self._found, self.message = True, None, "Looking for the session..."
        name, password, me, address = self.value("name"), self.value("password"), self.value("me") or "Friend", self.value("address")

        def work():  # (finding and connecting can take seconds: off the main thread)
            try:
                where = sess.find_host(name, address)
                if where is None:
                    self._found = "not found"
                    return
                self._found = sess.GuestLink(where[0], where[1], name, password, me)
            except (OSError, ValueError):
                self._found = "unreachable"
        threading.Thread(target=work, daemon=True).start()

    def answer(self, allow):
        host = self.game.coop_host
        waiting = host.waiting()
        if waiting:
            (host.allow if allow else host.deny)(waiting[0][0])

    def end(self):
        host = getattr(self.game, "coop_host", None)
        if self.mode == "host" and host:
            from src.coop import roster
            roster.close_out(self.game, host)
            self.game.coop_vote = None
            host.close()
            self.game.coop_host = None
        elif self.link:
            self.link.leave()
            self.link = None
            self.message = ""

    # ------------------------------------------------------------------ every frame
    def handle_events(self, events):
        host = getattr(self.game, "coop_host", None)
        for e in events:
            if self.btn_back.handle_event(e):
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return self.go_back()
            if self._form_showing():
                self._form_event(e)
            elif self.mode == "host" and host:
                self.btn_close.handle_event(e)
                if host.waiting():
                    self.btn_allow.handle_event(e)
                    self.btn_deny.handle_event(e)
            elif self.link:
                self.btn_close.handle_event(e)

    def _form_event(self, e):
        self.btn_go.handle_event(e)
        if self.mode == "host" or len(self.fields) > 1:
            self.btn_reveal.handle_event(e)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, f in enumerate(self.fields):
                if f["rect"].collidepoint(e.pos):
                    self.active = i
        elif e.type == pygame.KEYDOWN:
            field = self.fields[self.active]
            if e.key == pygame.K_BACKSPACE:
                field["text"] = field["text"][:-1]
            elif e.key == pygame.K_TAB:
                self.active = (self.active + 1) % len(self.fields)
            elif e.key == pygame.K_RETURN:
                if self.active == len(self.fields) - 1:
                    self.go()
                else:
                    self.active += 1
            elif e.unicode and e.unicode.isprintable() and len(field["text"]) < 24:
                field["text"] += e.unicode

    coop_ticks = True  # (it runs the session itself: see Game's loop)

    def update(self):
        world.tick(self.game)
        if self.busy and self._found is not None:
            self.busy = False
            if isinstance(self._found, str):
                self.message = WHY[self._found]
            else:
                self.link, self.message = self._found, ""
        if self.link:
            self.link.poll()
            if self.link.status not in ("connecting", "pending", "allowed"):
                self.message = WHY.get(self.link.status, "That didn't work.")
                self.link.close()
                self.link = None
            elif self.link.lost:
                self.message = "Lost the connection to the host."
                self.link.close()
                self.link = None
            elif self.link.status == "allowed" and not self.entered:
                self.entered = True
                from src.states.coop_world import CoopWorldState
                self.game.change_state(CoopWorldState(self.game, self.link, self))

    # ------------------------------------------------------------------ the screen
    def _say(self, text, x, y, font=None, color=(255, 255, 255)):
        theme.shadow_text(self.game.screen, text, font or self.text, x, y, color=color, shadow=(16, 20, 36))

    def draw(self):
        screen = self.game.screen
        screen.fill((28, 36, 62))
        theme.draw_panel(screen, pygame.Rect(40, 86, self.game.width - 80, 610))
        self.btn_back.draw(screen)
        title = "CO-OP: OPEN A SESSION" if self.mode == "host" else "JOIN A SESSION"
        theme.shadow_text(screen, title, self.title, self.game.width // 2, 20, color=(255, 255, 255), shadow=(16, 20, 36), align="center")
        if self._form_showing():
            self._draw_form()
        elif self.mode == "host":
            self._draw_host()
        else:
            self._draw_guest()
        if self.message:
            theme.shadow_text(screen, self.message, self.text, self.game.width // 2, 640, color=(255, 214, 110), shadow=(16, 20, 36), align="center")

    def _draw_form(self):
        screen = self.game.screen
        for i, f in enumerate(self.fields):
            r = f["rect"]
            self._say(f["label"], 90, r.y + 12)
            pygame.draw.rect(screen, (250, 250, 250), r, border_radius=8)
            pygame.draw.rect(screen, theme.RUN if i == self.active else theme.TEXTBOX_FRAME, r, 4, border_radius=8)
            shown = "*" * len(f["text"]) if f["key"] == "password" and not self.reveal else f["text"]
            cursor = "_" if i == self.active and pygame.time.get_ticks() // 500 % 2 == 0 else ""
            theme.shadow_text(screen, shown + cursor, self.text, r.x + 14, r.y + 12)
        if getattr(getattr(self.game, "android", None), "typing", False):  # (the phone's keyboard may cover the box)
            f = self.fields[self.active]
            shown = "*" * len(f["text"]) if f["key"] == "password" and not self.reveal else f["text"]
            strip = pygame.Rect(170, 16, self.game.width - 340, 58)
            pygame.draw.rect(screen, (250, 250, 250), strip, border_radius=8)
            pygame.draw.rect(screen, theme.RUN, strip, 4, border_radius=8)
            theme.shadow_text(screen, f"{f['label']}: {shown}_", self.text, strip.x + 14, strip.y + 13)
        self.btn_go.draw(screen)
        self.btn_reveal.text = "HIDE" if self.reveal else "REVEAL"
        self.btn_reveal.draw(screen)

    def _draw_host(self):
        host = self.game.coop_host
        self._say(f"Session: {host.name}", 90, 120)
        ips = discovery.local_ips()
        where = ", ".join(f"{ip}:{host.port}" for ip in ips) or "no network found"
        self._say(f"Host address: {where}", 90, 160)
        self._say("If a friend can't find you, they can type this address. On a PC, allow the game through the firewall.",
                  90, 200, self.small, (200, 214, 240))
        waiting = host.waiting()
        if waiting:
            self._say(f"{waiting[0][1]} wants to join (name not verified)", 90, 345)
            self.btn_allow.draw(self.game.screen)
            self.btn_deny.draw(self.game.screen)
        here = [g for g in host.guests.values()]
        y = 430
        if not here and not waiting:
            self._say("Waiting for a friend to join...", 90, y)
        for g in here:
            state = f"connected, {g['ms']} ms" if g["cid"] is not None and g.get("ms") is not None else \
                "connected" if g["cid"] is not None else "disconnected (seat held 2 minutes)"
            self._say(f"{g['name']}: {state}", 90, y)
            y += 44
        self.btn_close.draw(self.game.screen)

    def _draw_guest(self):
        if self.busy or not self.link:
            self._say(self.message or "Connecting...", 90, 200)
            return
        if self.link.status == "pending":
            self._say("Waiting for the host to say yes...", 90, 200)
        elif self.link.status == "allowed":
            ms = f"{self.link.ms} ms" if self.link.ms is not None else "measuring..."
            self._say(f"Connected to {self.link.session}!", 90, 200)
            self._say(f"Link speed: {ms}", 90, 250)
            self._say("The shared map is on its way. For now this proves your devices can talk.", 90, 300, self.small, (200, 214, 240))
        else:
            self._say("Connecting...", 90, 200)
        self.btn_close.draw(self.game.screen)
