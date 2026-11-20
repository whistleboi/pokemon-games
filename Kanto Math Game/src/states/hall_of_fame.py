"""The Hall of Fame (11-19, Jordan): after any region's Champion, the team is shown "1 by 1 like the games do, through the
full team group shot. don't show credits. Have there be an abrupt cut to the music with the player's phone ringing, with
their mom telling them to come home and pack their bags for the move. a sort of comic relief. save a record of all teams
that beat the league for that player number."

  1. each Pokemon in turn, as the games' Hall of Fame machine shows them: it slides in under a spotlight, name, level
     and its trainer (the Hall of Fame theme playing);
  2. the whole team together with you: "Welcome to the Hall of Fame!";
  3. the music stops dead, your phone rings, and Mom is on the line: the phone comes up to fill the screen, Mom on it,
     her words typing out (a tap finishes a line, the next moves on); then she hangs up;
  4. then on to what the region does next (home, or Kanto's walk out of the Hall).
The team is saved first: story_flags["hall_of_fame_records"], a list kept in this save (the player's own slot), one entry
per League win: region, day, player name and look, each Pokemon's species, name, level and shininess.
A tap (or Enter) moves it on at every stage: the next Pokemon, the phone, answering it; the call is an ordinary message."""
import math
import os

import pygame

from src.states.base import GameState
from src.ui import theme

MON_MS = 2600      # (each Pokemon's turn)
SLIDE_MS = 450     # (sliding in under the light)
GROUP_MS = 5200    # (the team together)
QUIET_MS = 700     # (the music cut: a beat of silence before the ring)
RING_MS = 2400     # (the phone ringing before Mom speaks)

MOM_LINES = [   # (the call, played in the scene: Mom on the phone's screen, her words typing out - Jordan 11-19: "all scenes
    "{player}! Oh, honey, I saw the whole thing on TV! You're the Champion! I'm SO proud of you!",   # should be animated")
    "Now, come straight home and pack your bags. The moving van comes first thing in the morning!",
    "Oh, and don't forget to change your underwear. Love you! Bye!",
]
HUNG_UP = "...The line went dead. Moving? Already?"
ANSWER_MS = 350    # (the phone comes up to your ear: it grows to fill the screen)
TYPE_MS = 22       # (each letter of Mom's words)
HANGUP_MS = 1600   # (the call over: the phone goes dark)


def record(game, region, team):
    """Save this League win's team in this save (a list in story_flags; the whole save is the player's own slot)."""
    story = game.story_manager
    rows = []
    for p in team:
        rows.append({"id": int(getattr(p, "id", 0) or 0), "name": str(getattr(p, "display_name", "") or getattr(p, "name", "")),
                     "species": str(getattr(p, "name", "")), "level": int(getattr(p, "level", 0) or 0),
                     "shiny": bool(getattr(p, "is_shiny", False))})
    entry = {"region": str(region).upper(), "day": story._today() if hasattr(story, "_today") else "",
             "player": str(getattr(game, "player_name", "") or ""), "look": str(getattr(game, "player_character", "") or ""),
             "team": rows}
    recs = story.story_flags.setdefault("hall_of_fame_records", [])
    recs.append(entry)
    return entry


def records(game):
    return list(game.story_manager.story_flags.get("hall_of_fame_records") or [])


class HallOfFameState(GameState):
    def __init__(self, game, region, then):
        super().__init__(game)
        self.region = str(region or "").upper()
        self.then = then
        story = game.story_manager
        self.team = [p for p in (story.player_team or []) if p is not None and not getattr(p, "is_egg", False)]
        record(game, self.region, self.team)
        self.t0 = pygame.time.get_ticks()
        self.skip = 0          # (time skipped ahead by taps)
        self.phase = "mon"
        self.rang = False
        self.called = False
        self.hung_up = False
        self.finished = False
        self.call_i, self.line_t, self.typed_all, self.hung_t = 0, 0, False, 0
        self._mom = None
        self.trainer = game.assets.get_player_image(str(getattr(game, "player_character", "") or "red"))
        self._big = {}
        if hasattr(game, "music"):
            try:
                game.music.hall_of_fame()
            except Exception:
                pass

    # ---- timing
    def _t(self):
        speed = 40 if getattr(self.game, "quick_scenes", False) else 1   # (the checks fast-forward it: harness_head)
        return (pygame.time.get_ticks() - self.t0) * speed + self.skip

    def _mons_end(self):
        return MON_MS * len(self.team)

    def handle_events(self, events):
        for e in events:
            tap = (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or \
                  (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER))
            if not tap:
                continue
            t = self._t()
            if t < self._mons_end():   # (on to the next Pokemon)
                self.skip += MON_MS - (t % MON_MS)
            elif t < self._mons_end() + GROUP_MS:   # (the group shot: on to the phone)
                self.skip += self._mons_end() + GROUP_MS - t
            elif self.rang and not self.called:   # (answer the phone)
                self.skip += max(0, getattr(self, "_ring_at", t) + RING_MS - t)
            elif self.called and not self.hung_up:   # (Mom talking: a tap finishes her line, the next moves on)
                if self._typed() < len(self._mom_line()):
                    self.typed_all = True
                else:
                    self._next_line()

    def update(self):
        t = self._t()
        end_group = self._mons_end() + GROUP_MS
        if t >= end_group and not self.rang:   # (the music stops dead: the phone)
            self.rang = True
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                music = getattr(self.game, "music", None)
                if music is not None:
                    music.kind, music.path, music.pending = None, None, None
                    music.hof_until = 0
            except Exception:
                pass
            self._ring_at = t + QUIET_MS
        if self.rang and not getattr(self, "_ringing", False) and t >= getattr(self, "_ring_at", 0):
            self._ringing = True
            path = os.path.join(self.game.assets.sounds_dir, "phone_ring.wav")
            try:
                if pygame.mixer.get_init() and os.path.isfile(path):
                    pygame.mixer.Sound(path).play()
            except Exception:
                pass
        if self.rang and not self.called and t >= getattr(self, "_ring_at", 0) + RING_MS:
            self.called = True   # (answered: Mom on the line)
            self.call_i, self.line_t, self.typed_all = 0, t, False
        if self.hung_up and not self.finished and t - self.hung_t >= HANGUP_MS:
            self.finished = True
            self.then([])

    @property
    def call_lines(self):
        name = str(getattr(self.game, "player_name", "") or "honey")
        return [l.replace("{player}", name) for l in MOM_LINES]

    def _mom_line(self):
        return self.call_lines[min(self.call_i, len(MOM_LINES) - 1)]

    def _typed(self):
        if self.typed_all:
            return len(self._mom_line())
        return max(0, min(len(self._mom_line()), (self._t() - self.line_t - ANSWER_MS) // TYPE_MS))

    def _next_line(self):
        if self.call_i < len(MOM_LINES) - 1:
            self.call_i += 1
            self.line_t, self.typed_all = self._t() - ANSWER_MS, False
        else:
            self.hung_up, self.hung_t = True, self._t()

    # ---- drawing
    def _mom_img(self, h):
        if self._mom is None:
            img = None
            p = os.path.join(self.game.assets.assets_dir, "sprites", "png", "mom.png")
            try:
                img = pygame.image.load(p).convert_alpha() if os.path.isfile(p) else None
            except Exception:
                img = None
            if img is not None:
                box = img.get_bounding_rect()
                img = img.subsurface(box) if box.w and box.h else img
                k = h / max(1, img.get_height())
                img = pygame.transform.scale(img, (max(1, int(img.get_width() * k)), int(h)))
            self._mom = img or False
        return self._mom or None

    def _draw_call(self, screen, t, f):
        """The call: the phone comes up and fills the screen, Mom on it, her words typing out; then it goes dark."""
        w, h = screen.get_size()
        screen.fill((8, 8, 14))
        k = min(1.0, (t - self.line_t) / ANSWER_MS) if self.call_i == 0 else 1.0
        ph = pygame.Rect(0, 0, int(90 + (w * 0.46 - 90) * k), int(150 + (h * 0.62 - 150) * k))
        ph.center = (w // 2, int(h // 2 - 40 - 50 * k))
        pygame.draw.rect(screen, (40, 44, 60), ph, border_radius=int(16 + 12 * k))
        scr = ph.inflate(-int(16 + 20 * k), -int(34 + 40 * k))
        lit = not self.hung_up or (t - self.hung_t) < 500
        pygame.draw.rect(screen, (150, 205, 255) if lit else (30, 34, 46), scr, border_radius=10)
        if k >= 1 and lit:
            mom = self._mom_img(int(scr.h * 1.9))   # (head and shoulders, as on a video call)
            talking = not self.hung_up and self._typed() < len(self._mom_line())
            bob = int(3 * math.sin(t / 90)) if talking else int(2 * math.sin(t / 400))   # (she bobs as she talks)
            if mom is not None:
                screen.set_clip(scr)
                screen.blit(mom, mom.get_rect(midtop=(scr.centerx, scr.y + 34 + bob)))
                screen.set_clip(None)
            theme.shadow_text(screen, "MOM", f["label"], scr.centerx, scr.y + 16, color=(30, 30, 50),
                              shadow=(200, 230, 255), align="center")
        box = pygame.Rect(16, h - 150, w - 32, 134)
        if k >= 1:
            theme.draw_textbox(screen, box)
            font = f["button"]
            if self.hung_up:
                text, shown = HUNG_UP, HUNG_UP[:max(0, (t - self.hung_t) // TYPE_MS)]
            else:
                text, shown = "Mom: " + self._mom_line(), "Mom: " + self._mom_line()[:self._typed()]
            words, lines, cur = text.split(), [], ""
            for wd in words:
                trial = (cur + " " + wd).strip()
                if font.size(trial)[0] > box.w - 56 and cur:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = trial
            lines.append(cur)
            left = len(shown)
            for n, ln in enumerate(lines[:3]):
                part = ln[:max(0, left)]
                left -= len(ln) + 1
                if part:
                    theme.shadow_text(screen, part, font, box.x + 28, box.y + 18 + n * 36)
            if not self.hung_up and self._typed() >= len(self._mom_line()) and (t // 400) % 2 == 0:
                pygame.draw.polygon(screen, theme.TEXT_ARROW, [(box.right - 40, box.bottom - 30), (box.right - 24, box.bottom - 30),
                                                               (box.right - 32, box.bottom - 20)])

    def _mon_img(self, p, h):
        key = (id(p), h)
        if key not in self._big:
            img = getattr(p, "image", None)
            if img is None:
                self._big[key] = None
            else:
                box = img.get_bounding_rect()
                part = img.subsurface(box) if box.w and box.h else img
                k = h / max(1, part.get_height())
                self._big[key] = pygame.transform.scale(part, (max(1, int(part.get_width() * k)), int(h)))
        return self._big[key]

    def _backdrop(self, screen, t, light_x=None):
        w, h = screen.get_size()
        screen.fill((12, 14, 30))
        for i in range(0, h, 4):   # (the hall's dark gradient)
            c = 12 + int(26 * i / h)
            pygame.draw.rect(screen, (c, c + 2, c + 22), (0, i, w, 4))
        lx = light_x if light_x is not None else w // 2
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(glow, (255, 246, 210, 46), [(lx - 40, 0), (lx + 40, 0), (lx + 260, h), (lx - 260, h)])
        pygame.draw.ellipse(glow, (255, 240, 190, 60), (lx - 230, h - 190, 460, 90))
        screen.blit(glow, (0, 0))
        for k in range(14):   # (sparkles drifting up)
            sx = (k * 137 + t // 9) % w
            sy = h - ((k * 89 + t // 5) % h)
            a = 120 + int(100 * math.sin((t / 300) + k))
            pygame.draw.circle(screen, (255, 240, 180, max(0, min(255, a))), (int(sx), int(sy)), 2)

    def draw(self):
        screen = self.game.screen
        w, h = screen.get_size()
        t = self._t()
        f = self.game.assets.fonts
        if self.called:   # (on the phone with Mom)
            self._draw_call(screen, t, f)
            return
        if self.rang:   # (after the cut: the hall goes dark, the phone buzzes)
            screen.fill((8, 8, 14))
            if t >= getattr(self, "_ring_at", 0):
                shake = int(6 * math.sin(t / 25)) if (t // 300) % 2 == 0 else 0
                ph = pygame.Rect(0, 0, 90, 150)
                ph.center = (w // 2 + shake, h // 2 - 40)
                pygame.draw.rect(screen, (40, 44, 60), ph, border_radius=16)
                pygame.draw.rect(screen, (140, 200, 255), ph.inflate(-16, -34), border_radius=8)
                theme.shadow_text(screen, "MOM", f["label"], ph.centerx, ph.centery - 8, color=(30, 30, 50),
                                  shadow=(200, 230, 255), align="center")
                theme.shadow_text(screen, "Ring... ring...", f["button"], w // 2, ph.bottom + 24, color=(250, 250, 250),
                                  shadow=(40, 40, 60), align="center")
            return
        if t < self._mons_end():
            i = t // MON_MS
            p = self.team[i]
            lt = t % MON_MS
            k = min(1.0, lt / SLIDE_MS)
            x = int(w + 160 - (w // 2 + 160) * (1 - (1 - k) ** 3))
            self._backdrop(screen, t, light_x=x)
            img = self._mon_img(p, int(h * 0.42))
            if img is not None:
                r = img.get_rect(midbottom=(x, int(h * 0.68)))
                shadow = pygame.Surface((r.w, 22), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow, (0, 0, 0, 110), shadow.get_rect())
                screen.blit(shadow, (r.x, r.bottom - 12))
                screen.blit(img, r)
            if k >= 1:
                name = str(getattr(p, "display_name", "") or "")
                box = pygame.Rect(0, 0, int(w * 0.56), 96)
                box.midbottom = (w // 2, h - 22)
                theme.draw_textbox(screen, box)
                theme.shadow_text(screen, f"{name}   Lv. {int(getattr(p, 'level', 0) or 0)}", f["button"], box.x + 24, box.y + 14)
                ot = str(getattr(self.game, "player_name", "") or "")
                theme.shadow_text(screen, f"Trainer: {ot}" + ("   (shiny!)" if getattr(p, "is_shiny", False) else ""),
                                  f["label"], box.x + 24, box.y + 56)
            theme.shadow_text(screen, "HALL OF FAME", f["button"], w // 2, 30, color=(250, 226, 120),
                              shadow=(60, 40, 10), align="center")
            return
        # the whole team, and you
        gt = t - self._mons_end()
        self._backdrop(screen, t)
        n = len(self.team)
        size = int(h * (0.26 if n > 3 else 0.32))
        base_y = int(h * 0.70)
        trainer = self.trainer
        if trainer is not None:
            th = int(h * 0.44)
            ti = pygame.transform.scale(trainer, (int(trainer.get_width() * th / trainer.get_height()), th))
            screen.blit(ti, ti.get_rect(midbottom=(w // 2, base_y + 8)))
        slots = []
        for j in range(n):   # (an arc either side of you)
            side = -1 if j % 2 == 0 else 1
            step = j // 2 + 1
            slots.append((w // 2 + side * step * int(w * 0.13), base_y - int(18 * (3 - step))))
        for j, p in enumerate(self.team):
            img = self._mon_img(p, size)
            if img is None:
                continue
            appear = min(1.0, max(0.0, (gt - j * 120) / 300))
            if appear <= 0:
                continue
            x, y = slots[j]
            screen.blit(img, img.get_rect(midbottom=(x, y + int(30 * (1 - appear)))))
        if gt > 900:
            box = pygame.Rect(0, 0, int(w * 0.72), 96)
            box.midbottom = (w // 2, h - 22)
            theme.draw_textbox(screen, box)
            theme.shadow_text(screen, "Welcome to the Hall of Fame!", f["button"], w // 2, box.y + 30, align="center")   # (centred text: y is its middle)
            theme.shadow_text(screen, f"{getattr(self.game, 'player_name', '')} and team, Champions of {self.region.title()}!",
                              f["label"], w // 2, box.y + 68, align="center")
        theme.shadow_text(screen, "HALL OF FAME", f["button"], w // 2, 30, color=(250, 226, 120),
                          shadow=(60, 40, 10), align="center")
