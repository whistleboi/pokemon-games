"""The Pokemon Musical (Black 2 / White 2's, simpler; Unova batch 4c, 11-24, Jordan: "a simple show game").

Pick a Pokemon and one of the four shows (Stardom: cool, A Sweet Soiree: elegant, Exciting Nimbasa: quirky, Forest
Stroll: cute; each with its own audience). Dress Up: tap a Prop from your Prop Case and it snaps to its spot on the
Pokemon (Black 2's eight: head, face, body, waist, two ears, two arms; Jordan's call "Snap to spots"); tap it again on
the Pokemon to take it off. The show: your Pokemon and three others dance to the show's song on Black 2's own stage;
three times a math question pops up (Jordan's call "Math for the spotlight"): a right answer turns the spotlight on
your Pokemon and the crowd cheers, a wrong one lets another dancer steal it. Then the curtain, the photo, and the
owner's review. Scoring after Black 2's: each kind of Prop pleases its part of the 200-strong audience (the show's own
kind 80, the opposite 20, the others 40, 20 at random), shared with the other dancers' Props of that kind; the
spotlights add to it. src/world/musical.py keeps the Prop Case, the fans and the owner's gifts."""
import math
import os
import random

import pygame

from src.states.base import GameState
from src.ui import theme

KIND_COLOR = {"Cool": (70, 120, 230), "Cute": (240, 110, 170), "Elegant": (160, 90, 210), "Quirky": (240, 190, 40)}
SLOTS = ["head", "ear0", "ear1", "face", "body", "waist", "arm0", "arm1"]
SPOTLIGHTS = 3
SPOT_POINTS = 15
RIVAL_NAMES = ["Lady Ava", "Rich Boy Kent", "Socialite Nell", "Dancer Mika", "Gentleman Ross", "Lass Pippa", "Artist Juno",
               "Harlequin Bo", "Parasol Lady Ines", "Pokefan Ollie"]
RIVAL_MONS = [506, 509, 511, 513, 515, 517, 519, 522, 527, 529, 531, 532, 535, 540, 546, 548, 550, 551, 554, 556, 557, 562,
              570, 572, 574, 577, 580, 582, 585, 587, 588, 590, 592, 594, 595, 597, 602, 605, 607, 610, 613, 616, 618, 619]
# (the show, in ms of show time: the curtain, each rival's solo, your three spotlight questions, the finale)
TIMELINE = [(1500, "open"), (5000, "solo:1"), (9000, "ask"), (14000, "solo:2"), (18000, "ask"), (23000, "solo:3"),
            (27000, "ask"), (32000, "finale"), (35500, "snap"), (36000, "close"), (37500, "end")]


def _slot_of(spot, k=0):
    return spot + str(k) if spot in ("ear", "arm") else spot


class Performer:
    def __init__(self, name, mon, img, worn, is_player=False):
        self.name, self.mon, self.img, self.worn, self.is_player = name, mon, img, dict(worn), is_player
        self.spot = 0      # (spotlights won)
        self.score = 0


class MusicalState(GameState):
    """back: the state to return to; then(lines): called after, with lines to show (the lobby's speech box)."""

    def __init__(self, game, back, then=None):
        super().__init__(game)
        from src.world import musical as M
        self.M = M
        self.back, self.then = back, then
        self.data = M.data(game)
        self.stage = "pick_mon"
        self.t0 = pygame.time.get_ticks()
        self.stage_t = 0
        self.buttons = []
        self.mon = None
        self.show = None
        self.worn = {}      # slot -> prop id
        self.page = 0
        self._imgs = {}
        self.performers = []
        self.show_t = 0     # (show time: stops while a question waits)
        self._last_tick = None
        self.events_done = set()
        self.math_ui = None
        self.asked = 0
        self.light = None   # (performer index, until show time)
        self.banner = ("", 0)
        self.cheers = []    # (x, y, born, colour)
        self.photo = None
        self.review = []
        self.result = None
        self.game.music.play_file("unova/msl_dressup")

    def _now(self):
        return pygame.time.get_ticks() - self.t0

    def _go(self, stage):
        self.stage, self.stage_t = stage, self._now()

    # ------------------------------------------------------------------------------------------------- pictures
    def _asset(self, *parts):
        return os.path.join(getattr(self.game.assets, "assets_dir", "assets"), *parts)

    def _prop_img(self, pid, size):
        k = ("p", pid, size)
        if k not in self._imgs:
            try:
                img = pygame.image.load(self._asset("musical", "props", "p%02d.png" % pid)).convert_alpha()
                img = pygame.transform.scale(img, (size, size))
            except Exception:
                img = None
            self._imgs[k] = img
        return self._imgs[k]

    def _stage_img(self, w, h):
        k = ("stage", self.show["key"], w, h)
        if k not in self._imgs:
            try:
                img = pygame.image.load(self._asset("musical", self.show["stage"])).convert()
                s = max(w / img.get_width(), h / img.get_height())
                img = pygame.transform.smoothscale(img, (int(img.get_width() * s), int(img.get_height() * s)))
            except Exception:
                img = None
            self._imgs[k] = img
        return self._imgs[k]

    def _mon_img(self, mon, h):
        k = ("mon", id(mon), h)
        if k not in self._imgs:
            img = getattr(mon, "image", None)
            if img is not None:
                box = img.get_bounding_rect()
                img = img.subsurface(box) if box.w and box.h else img
                s = h / max(1, img.get_height())
                img = pygame.transform.scale(img, (max(1, int(img.get_width() * s)), int(h)))
            self._imgs[k] = img
        return self._imgs[k]

    def _anchors(self, img):
        """Where each spot sits on a Pokemon's picture (Black 2 keeps them per Pokemon; ours are found from its shape)."""
        k = ("anchor", id(img))
        if k not in self._imgs:
            w, h = img.get_size()
            mask = pygame.mask.from_surface(img)
            top_rows = max(1, h // 8)
            xs = [x for y in range(top_rows) for x in range(w) if mask.get_at((x, y))]
            cx_top = sum(xs) / len(xs) if xs else w / 2
            cx = w / 2
            self._imgs[k] = {"head": (cx_top, h * 0.06, "bottom"), "ear0": (w * 0.2, h * 0.12, "center"),
                             "ear1": (w * 0.8, h * 0.12, "center"), "face": (cx, h * 0.33, "center"),
                             "body": (cx, h * 0.58, "center"), "waist": (cx, h * 0.78, "center"),
                             "arm0": (w * 0.04, h * 0.58, "center"), "arm1": (w * 0.96, h * 0.58, "center")}
        return self._imgs[k]

    def _draw_mon(self, screen, perf, midbottom, h, t=0.0, dance=False):
        img = perf.img if perf.img is not None and perf.img.get_height() == h else None
        if img is None and perf.mon is not None:
            img = self._mon_img(perf.mon, h)
        if img is None:
            return
        dx = dy = 0
        if dance:   # (bounce on the beat, sway between)
            beat = t / 500.0
            dy = -abs(math.sin(beat * math.pi)) * h * 0.08
            dx = math.sin(beat * math.pi / 2) * h * 0.05
        rect = img.get_rect(midbottom=(midbottom[0] + dx, midbottom[1] + dy))
        screen.blit(img, rect)
        anchors = self._anchors(img)
        size = max(24, int(h * 0.32))
        for slot, pid in perf.worn.items():
            p = self._prop_img(pid, size)
            if p is None:
                continue
            if slot == "arm0":
                p = pygame.transform.flip(p, True, False)
            ax, ay, how = anchors[slot]
            pos = (rect.x + ax, rect.y + ay)
            r = p.get_rect(midbottom=(pos[0], pos[1] + size * 0.25)) if how == "bottom" else p.get_rect(center=pos)
            screen.blit(p, r)

    # ------------------------------------------------------------------------------------------------- scoring
    def _audience(self):
        kind = self.show["kind"]
        opp = self.data["opposite"][kind]
        aud = {k: 40 for k in KIND_COLOR}
        aud[kind], aud[opp] = 80, 20
        rng = random.Random(self.show["key"])
        for _ in range(20):
            aud[rng.choice(list(KIND_COLOR))] += 1
        return aud

    def _kinds(self, worn):
        out = {k: 0 for k in KIND_COLOR}
        for pid in worn.values():
            out[self.data["props"][pid]["kind"]] += 1
        return out

    def _score_all(self):
        aud = self._audience()
        total = {k: sum(self._kinds(p.worn)[k] for p in self.performers) for k in KIND_COLOR}
        for p in self.performers:
            mine = self._kinds(p.worn)
            p.score = int(sum(mine[k] / total[k] * aud[k] for k in KIND_COLOR if total[k])) + p.spot * SPOT_POINTS

    # ------------------------------------------------------------------------------------------------- set-up
    def _team(self):
        return [p for p in self.game.story_manager.player_team if self.M.can_dress(p)]

    def _rivals(self):
        rng = random.Random()
        out = []
        names = rng.sample(RIVAL_NAMES, 3)
        from src.pokemon.data import Pokemon
        pool = [pid for pid in range(len(self.data["props"])) if pid not in self.M.SPECIAL]
        for name in names:
            sid = rng.choice(RIVAL_MONS)
            mon = None
            try:
                mon = Pokemon(self.game.loader.fetch_specific(sid), self.game.assets, size_mult=3.125)
            except Exception:
                mon = None
            worn = {}
            fav = rng.choice(list(KIND_COLOR))
            for _ in range(rng.randint(2, 6)):
                choices = [p for p in pool if self.data["props"][p]["kind"] == fav] if rng.random() < 0.5 else pool
                pid = rng.choice(choices)
                self._wear(worn, pid)
            out.append(Performer(name, mon, None, worn))
        return out

    def _wear(self, worn, pid):
        """Put a Prop on its spot (the second ear / arm if the first is taken; its other spot if both are; else swap)."""
        if pid in worn.values():
            return
        p = self.data["props"][pid]
        spots = [p["spot"]] + ([p["alt"]] if p.get("alt") else [])
        for spot in spots:
            for k in (0, 1) if spot in ("ear", "arm") else (0,):
                s = _slot_of(spot, k)
                if s not in worn:
                    worn[s] = pid
                    return
        worn[_slot_of(p["spot"], 0)] = pid

    # ------------------------------------------------------------------------------------------------- input
    def handle_events(self, events):
        for e in events:
            pos = e.pos if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 else None
            key = e.key if e.type == pygame.KEYDOWN else None
            if self._now() - self.stage_t < 250:
                continue
            if self.stage in ("pick_mon", "pick_show", "dress"):
                hit = next((b for b in self.buttons if pos and b[0].collidepoint(pos)), None)
                if key == pygame.K_ESCAPE:
                    hit = (None, "back")
                elif key and pygame.K_1 <= key <= pygame.K_9:
                    n = key - pygame.K_1
                    opts = [b for b in self.buttons if isinstance(b[1], tuple) and b[1][0] in ("mon", "show")]
                    hit = opts[n] if n < len(opts) else None
                if hit:
                    self._click(hit[1])
            elif self.stage in ("photo", "review") and (pos or key in (pygame.K_RETURN, pygame.K_SPACE)):
                self._next()

    def _click(self, what):
        if what == "back":
            if self.stage == "dress":
                self._go("pick_show")
            elif self.stage == "pick_show":
                self._go("pick_mon")
            else:
                self._leave(["Receptionist: Come back any time you want to perform!"])
            return
        kind = what[0]
        if kind == "mon":
            self.mon = what[1]
            self._go("pick_show")
        elif kind == "show":
            self.show = what[1]
            self.worn = {}
            self._go("dress")
        elif kind == "prop":
            pid = what[1]
            if pid in self.worn.values():
                self.worn = {s: p for s, p in self.worn.items() if p != pid}
            else:
                self._wear(self.worn, pid)
        elif kind == "off":
            self.worn.pop(what[1], None)
        elif kind == "page":
            self.page = max(0, self.page + what[1])
        elif kind == "clear":
            self.worn = {}
        elif kind == "done":
            self._start_show()

    def _start_show(self):
        me = Performer(self.game.player_name or "You", self.mon, None, self.worn, is_player=True)
        self.performers = [me] + self._rivals()
        self.order = [1, 0, 2, 3]   # (left to right on stage: you second)
        self.show_t, self._last_tick = 0, pygame.time.get_ticks()
        self.events_done = set()
        self.asked = 0
        self._go("show")
        self.game.music.play_file(self.show["song"])

    # ------------------------------------------------------------------------------------------------- the show
    def update(self):
        if self.stage != "show":
            return
        tick = pygame.time.get_ticks()
        if self.math_ui is None:
            self.show_t += tick - (self._last_tick or tick)
        self._last_tick = tick
        for at, what in TIMELINE:
            if self.show_t >= at and at not in self.events_done and self.math_ui is None:
                self.events_done.add(at)
                self._cue(what)
                break

    def _cue(self, what):
        if what.startswith("solo:"):
            i = int(what[5:])
            self.light = (i, self.show_t + 2800)
            self.banner = ("%s's %s takes a solo!" % (self.performers[i].name, self._mon_name(self.performers[i])), self.show_t + 2600)
            self._cheer(i, 6)
        elif what == "ask":
            self._ask()
        elif what == "finale":
            self.light = None
            self.banner = ("The finale! Everyone dances together!", self.show_t + 3500)
            for i in range(4):
                self._cheer(i, 3)
        elif what == "snap":   # (the photo: the last frame drawn, before the curtain falls)
            self.photo = self.game.screen.copy()
        elif what == "end":
            self._score_all()
            self._go("photo")

    def _mon_name(self, perf):
        m = perf.mon
        return getattr(m, "display_name", None) or getattr(m, "name", None) or "Pokemon"

    def _ask(self):
        from src.ui.widgets import MathBattleUI
        self.asked += 1
        self.problem, self.answer, self.options = self.game.math.generate(self.game.story_manager.get_math_level(), num_options=4)
        self.math_ui = MathBattleUI(self.game, self.problem, self.options, self._answer)
        self.game.ui_manager.add_element(self.math_ui)
        self.banner = ("Spotlight chance %d of %d! Answer to win the spotlight!" % (self.asked, SPOTLIGHTS), self.show_t + 100000)

    def _answer(self, idx):
        right = self.options[idx] == self.answer
        if self.math_ui in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(self.math_ui)
        self.math_ui = None
        me = self.performers[0]
        if right:
            me.spot += 1
            self.light = (0, self.show_t + 3200)
            self.banner = ("The spotlight's on %s's %s! The crowd goes wild!" % (me.name, self._mon_name(me)), self.show_t + 3000)
            self._cheer(0, 10)
        else:
            thief = random.choice([1, 2, 3])
            self.performers[thief].spot += 1
            self.light = (thief, self.show_t + 3200)
            self.banner = ("It was %s. %s's %s stole the spotlight!" % (self.answer, self.performers[thief].name,
                                                                        self._mon_name(self.performers[thief])), self.show_t + 3000)
            self._cheer(thief, 5)

    def _cheer(self, i, n):
        self.cheers += [(i, random.random(), self.show_t + k * 120, random.choice(list(KIND_COLOR.values()))) for k in range(n)]

    # ------------------------------------------------------------------------------------------------- the end
    def _next(self):
        if self.stage == "photo":
            self._make_review()
            self._go("review")
        elif self.stage == "review":
            self.review.pop(0)
            if not self.review:
                self._finish()

    def _look(self, worn):
        kinds = self._kinds(worn)
        n = sum(kinds.values())
        if not n:
            return "natural", None, None
        top = max(kinds, key=kinds.get)
        low = min((k for k in KIND_COLOR), key=lambda k: kinds[k])
        look = top.lower() if kinds[top] / n > 0.45 else "balanced"
        accent = next((self.data["props"][p]["name"] for p in worn.values() if self.data["props"][p]["kind"] == top), None)
        return look, accent, low.lower()

    def _make_review(self):
        ranked = sorted(self.performers, key=lambda p: (-p.score, not p.is_player))
        me = self.performers[0]
        place = ranked.index(me) + 1
        look, accent, weak = self._look(me.worn)
        excite = sum(p.spot for p in self.performers)
        intro = ["Owner: Good job! The Pokemon were in perfect sync! The best Musical ever!" if place == 1 and me.spot == SPOTLIGHTS
                 else "Owner: Good job! It was a great Musical! The audience sent in comments!" if excite >= 3
                 else "Owner: Good job! A Musical with some very exciting moments!"]
        lines = intro + ["Owner: %s's Dress Up was very %s!" % (p.name, self._look(p.worn)[0]) for p in reversed(ranked[1:])]
        comment = {1: "In this Musical, it's no overstatement to say %s's Pokemon had the lead role!" % me.name,
                   2: "Your Pokemon used its Props like a real actor!",
                   3: "Your Pokemon played its part very well.",
                   4: "It wasn't very noticeable... but I liked it! Keep it up!"}[place]
        lines += ["Owner: And %s! Your Pokemon's Dress Up was very %s!" % (me.name, look), "Owner: " + comment,
                  "Owner: Thank you for taking part today! Please join another Musical!"]
        self.review = lines
        self.result = {"show": self.show["name"], "kind": self.show["kind"], "place": place, "look": look, "accent": accent,
                       "weak": weak, "points": me.score}

    def _finish(self):
        from src.world import feats as _feats
        try:
            _feats.note(self.game.story_manager, "musicals")
        except Exception:
            pass
        lines = ["%s: %s place in %s!" % (self.game.player_name or "You", ["", "First", "Second", "Third", "Fourth"][self.result["place"]],
                                          self.show["name"])]
        lines += self.M.after_show(self.game, self.result)
        self._leave(lines)

    def _leave(self, lines):
        if self.math_ui is not None and self.math_ui in self.game.ui_manager.elements:
            self.game.ui_manager.elements.remove(self.math_ui)
        self.math_ui = None
        if self.back is not None:
            self.game.change_state(self.back)
        try:
            self.game.music.for_state(self.back)
        except Exception:
            pass
        if self.then:
            self.then(lines)

    # ------------------------------------------------------------------------------------------------- drawing
    def _button(self, screen, rect, label, what, fill=(250, 244, 236), edge=(150, 60, 110), font=None):
        pygame.draw.rect(screen, fill, rect, border_radius=12)
        pygame.draw.rect(screen, edge, rect, 3, border_radius=12)
        f = font or self.game.assets.fonts["label" if rect.h < 70 and rect.w < 260 else "button"]
        theme.shadow_text(screen, label, f, rect.centerx, rect.centery - f.get_height() // 2, color=(50, 30, 40),
                          shadow=(255, 255, 255), align="center")
        self.buttons.append((rect, what))

    def _curtain_bg(self, screen):
        w, h = screen.get_size()
        screen.fill((60, 10, 30))
        for x in range(0, w, 40):   # (the theater's red curtain)
            shade = 120 + int(40 * math.sin(x / 40))
            pygame.draw.rect(screen, (shade, 20, 50), (x, 0, 40, h))
        pygame.draw.rect(screen, (230, 190, 90), (0, 0, w, 10))

    def draw(self):
        screen = self.game.screen
        w, h = screen.get_size()
        f = self.game.assets.fonts
        self.buttons = []
        if self.stage == "pick_mon":
            self._curtain_bg(screen)
            theme.shadow_text(screen, "POKEMON MUSICAL: WHO WILL PERFORM?", f["button"], w // 2, 30, align="center")
            for i, mon in enumerate(self._team()[:6]):
                r = pygame.Rect(w // 2 - 360 + (i % 3) * 245, 110 + (i // 3) * 250, 230, 230)
                pygame.draw.rect(screen, (250, 240, 236), r, border_radius=16)
                pygame.draw.rect(screen, (150, 60, 110), r, 3, border_radius=16)
                img = self._mon_img(mon, 150)
                if img is not None:
                    screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - 50)))
                theme.shadow_text(screen, "%d. %s" % (i + 1, str(getattr(mon, "display_name", "")).upper()), f["label"], r.centerx,
                                  r.bottom - 40, color=(50, 30, 40), shadow=(255, 255, 255), align="center")
                self.buttons.append((r, ("mon", mon)))
            self._button(screen, pygame.Rect(w // 2 - 120, h - 90, 240, 60), "NOT NOW", "back")
            return
        if self.stage == "pick_show":
            self._curtain_bg(screen)
            theme.shadow_text(screen, "PICK A SHOW", f["button"], w // 2, 30, align="center")
            for i, s in enumerate(self.data["shows"]):
                r = pygame.Rect(w // 2 - 330, 100 + i * 100, 660, 84)
                pygame.draw.rect(screen, (250, 244, 236), r, border_radius=14)
                pygame.draw.rect(screen, KIND_COLOR[s["kind"]], r, 5, border_radius=14)
                theme.shadow_text(screen, "%d.  %s" % (i + 1, s["name"]), f["button"], r.x + 24, r.y + 10, color=(50, 30, 40),
                                  shadow=(255, 255, 255))
                theme.shadow_text(screen, "A %s show. Popular with %s." % (s["kind"].lower(), s["audience"].lower()), f["label"],
                                  r.x + 24, r.y + 50, color=(90, 60, 70), shadow=(255, 255, 255))
                self.buttons.append((r, ("show", s)))
            self._button(screen, pygame.Rect(w // 2 - 120, h - 90, 240, 60), "BACK", "back")
            return
        if self.stage == "dress":
            self._draw_dress(screen, w, h, f)
            return
        if self.stage == "show":
            self._draw_show(screen, w, h, f)
            self.game.ui_manager.draw(screen)
            return
        if self.stage in ("photo", "review"):
            screen.fill((20, 14, 24))
            if self.photo is not None:
                ph = pygame.transform.smoothscale(self.photo, (int(w * 0.62), int(h * 0.62)))
                r = ph.get_rect(center=(w // 2, int(h * 0.38)))
                pygame.draw.rect(screen, (250, 246, 236), r.inflate(28, 60).move(0, 14))
                screen.blit(ph, r)
                theme.shadow_text(screen, "%s  -  a Pokemon Musical" % self.show["name"], f["label"], w // 2, r.bottom + 12,
                                  color=(60, 40, 50), shadow=(255, 255, 255), align="center")
            if self.stage == "review" and self.review:
                box = pygame.Rect(16, h - 150, w - 32, 134)
                theme.draw_textbox(screen, box)
                self._text(screen, self.review[0], box, f["button"])
            elif self.stage == "photo":
                theme.shadow_text(screen, "Click to go on", f["label"], w // 2, h - 60, align="center")

    def _text(self, screen, text, box, font):
        words, lines, cur = str(text).split(), [], ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if font.size(trial)[0] > box.w - 56 and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = trial
        lines.append(cur)
        for n, ln in enumerate(lines[:3]):
            theme.shadow_text(screen, ln, font, box.x + 28, box.y + 18 + n * 36)

    def _draw_dress(self, screen, w, h, f):
        screen.fill((255, 228, 238))
        for y in range(0, h, 48):   # (the dressing room's striped wall)
            pygame.draw.rect(screen, (255, 214, 228), (0, y, w // 2, 24))
        theme.shadow_text(screen, "DRESS UP: %s (%s)" % (self.show["name"], self.show["kind"]), f["button"], w // 4, 18, align="center",
                          color=(120, 30, 80), shadow=(255, 255, 255))
        me = Performer("", self.mon, None, self.worn)
        mon_h = int(h * 0.46)
        self._draw_mon(screen, me, (w // 4, int(h * 0.72)), mon_h)
        # the worn Props: tap one to take it off
        x = 24
        for slot in SLOTS:
            r = pygame.Rect(x, h - 150, 64, 64)
            pygame.draw.rect(screen, (255, 255, 255), r, border_radius=10)
            pid = self.worn.get(slot)
            pygame.draw.rect(screen, KIND_COLOR[self.data["props"][pid]["kind"]] if pid is not None else (200, 170, 190), r, 3,
                             border_radius=10)
            if pid is not None:
                img = self._prop_img(pid, 56)
                if img:
                    screen.blit(img, img.get_rect(center=r.center))
                self.buttons.append((r, ("off", slot)))
            theme.shadow_text(screen, slot.rstrip("01").upper(), f["label"], r.centerx, r.bottom + 4, align="center",
                              color=(120, 60, 90), shadow=(255, 255, 255))
            x += 70
        kinds = self._kinds(self.worn)
        theme.shadow_text(screen, "  ".join("%s %d" % (k, kinds[k]) for k in KIND_COLOR), f["label"], w // 4, h - 200, align="center",
                          color=(90, 40, 70), shadow=(255, 255, 255))
        # the Prop Case
        have = self.M.props(self.game)
        per = 24
        pages = max(1, (len(have) + per - 1) // per)
        self.page = min(self.page, pages - 1)
        x0, y0, cell = w // 2 + 20, 70, 84
        theme.shadow_text(screen, "PROP CASE  (page %d of %d)" % (self.page + 1, pages), f["label"], x0, 30, color=(120, 30, 80),
                          shadow=(255, 255, 255))
        mouse = pygame.mouse.get_pos()
        tip = None
        for i, pid in enumerate(have[self.page * per:(self.page + 1) * per]):
            r = pygame.Rect(x0 + (i % 6) * (cell + 8), y0 + (i // 6) * (cell + 8), cell, cell)
            p = self.data["props"][pid]
            on = pid in self.worn.values()
            pygame.draw.rect(screen, (255, 250, 210) if on else (255, 255, 255), r, border_radius=12)
            pygame.draw.rect(screen, KIND_COLOR[p["kind"]], r, 4 if on else 2, border_radius=12)
            img = self._prop_img(pid, 64)
            if img:
                screen.blit(img, img.get_rect(center=r.center))
            self.buttons.append((r, ("prop", pid)))
            if r.collidepoint(mouse):
                tip = p
        if tip:
            theme.shadow_text(screen, "%s  -  %s, worn on the %s" % (tip["name"], tip["kind"], tip["spot"]), f["label"], x0,
                              y0 + 4 * (cell + 8) + 8, color=(60, 30, 50), shadow=(255, 255, 255))
        by = h - 90
        if pages > 1:
            self._button(screen, pygame.Rect(x0, by - 76, 150, 56), "< PAGE", ("page", -1))
            self._button(screen, pygame.Rect(x0 + 160, by - 76, 150, 56), "PAGE >", ("page", 1))
        self._button(screen, pygame.Rect(x0, by, 150, 60), "BACK", "back")
        self._button(screen, pygame.Rect(x0 + 160, by, 150, 60), "CLEAR", ("clear",))
        self._button(screen, pygame.Rect(x0 + 320, by, 200, 60), "ON STAGE!", ("done",), fill=(255, 236, 160))

    def _draw_show(self, screen, w, h, f):
        stage = self._stage_img(w, h)
        if stage is not None:
            screen.blit(stage, stage.get_rect(center=(w // 2, h // 2)))
        else:
            screen.fill((40, 20, 50))
        t = self.show_t
        lit = self.light if self.light and self.light[1] > t else None
        if lit is None and self.light:
            self.light = None
        mon_h = int(h * 0.24)
        floor = int(h * 0.80)
        xs = [int(w * (0.17 + 0.22 * k)) for k in range(4)]
        if lit is not None:
            veil = pygame.Surface((w, h), pygame.SRCALPHA)
            veil.fill((0, 0, 20, 110))
            screen.blit(veil, (0, 0))
        for slot, i in enumerate(self.order):
            perf = self.performers[i]
            if lit is not None and lit[0] == i:   # (the spotlight's cone)
                cone = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.polygon(cone, (255, 250, 200, 90), [(xs[slot] - 30, 0), (xs[slot] + 30, 0), (xs[slot] + 120, floor + 10),
                                                                 (xs[slot] - 120, floor + 10)])
                pygame.draw.ellipse(cone, (255, 250, 210, 120), (xs[slot] - 120, floor - 16, 240, 40))
                screen.blit(cone, (0, 0))
            self._draw_mon(screen, perf, (xs[slot], floor), mon_h, t + slot * 120, dance=10 < t < 36000)
            theme.shadow_text(screen, perf.name, f["label"], xs[slot], floor + 14, align="center",
                              color=(255, 230, 120) if perf.is_player else (255, 255, 255))
        for i, rx, born, col in self.cheers:   # (hearts and stars rising from the crowd)
            age = t - born
            if 0 <= age < 1600:
                slot = self.order.index(i)
                x = xs[slot] + int((rx - 0.5) * 160)
                y = floor - int(age * 0.25) - mon_h // 2
                pygame.draw.circle(screen, col, (x, y), 9)
                pygame.draw.circle(screen, (255, 255, 255), (x - 3, y - 3), 3)
        self.cheers = [c for c in self.cheers if t - c[2] < 1600]
        for k in range(28):   # (the audience's heads along the bottom, bobbing to the beat)
            x = int(w * (k + 0.5) / 28)
            bob = int(4 * abs(math.sin(t / 500.0 * math.pi + k)))
            pygame.draw.circle(screen, (20, 14, 30), (x, h - 18 - bob), 26)
        if t < 1500 or t > 36000:   # (the curtain opens, and closes at the end)
            k = min(1.0, t / 1500) if t < 1500 else max(0.0, 1 - (t - 36000) / 1500)
            cw = int(w / 2 * (1 - k))
            pygame.draw.rect(screen, (150, 20, 50), (0, 0, cw, h))
            pygame.draw.rect(screen, (150, 20, 50), (w - cw, 0, cw, h))
        text, until = self.banner
        if text and until > t:
            box = pygame.Rect(16, 16, w - 32, 70)
            theme.draw_textbox(screen, box)
            self._text(screen, text, box, f["button"])
