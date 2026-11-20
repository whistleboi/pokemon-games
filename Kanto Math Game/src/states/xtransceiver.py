"""The Xtransceiver: Black 2 / White 2's wrist video phone (Jordan 11-20: "Animated video calls").

A story call: the map dims, the Xtransceiver rings on your wrist, it comes up and fills the screen, the caller on its
video screen (their picture, bobbing as they talk), their words typing out; a tap finishes a line, the next moves on;
then it hangs up and you're back on the map. No calling out. Played by a story event {"scene": "xtransceiver", "caller":
"Mom", "pic": "sheet:b2_mom.png" (an overworld sheet's front frame) or a trainer picture ("hugh.png"), "lines": [...]}
(src/states/overworld/common.py)."""
import math
import os

import pygame

from src.states.base import GameState
from src.ui import theme

RING_MS = 1300      # the ringing, before it comes up
UP_MS = 420         # coming up to fill the screen
TYPE_MS = 22        # a character
DOWN_MS = 700       # hanging up
FRAME = (236, 112, 40)      # (the B2W2 Xtransceiver's orange casing)
FRAME_DARK = (120, 52, 16)
SCREEN = (176, 222, 255)


class XtransceiverCallState(GameState):
    def __init__(self, game, back, caller, pic, lines, then=None):
        super().__init__(game)
        self.back = back                # (the state underneath: drawn dimmed while it rings)
        self.caller = caller
        self.pic_key = pic
        self.lines = [str(x) for x in (lines or ["..."])]
        self.then = then
        self.t0 = pygame.time.get_ticks()
        self.stage = "ring"             # ring -> up -> talk -> down
        self.i = 0
        self.line_t = 0
        self.down_t = 0
        self._pic = None
        self._under = None

    # ---- the caller's picture
    def _picture(self, h):
        if self._pic is None:
            img = None
            key = str(self.pic_key or "")
            try:
                if key.startswith("sheet:"):
                    p = os.path.join(self.game.assets.assets_dir, "dungeon", "characters", key[6:])
                    sheet = pygame.image.load(p).convert_alpha()
                    cw, ch = sheet.get_width() // 4, sheet.get_height() // 4
                    img = sheet.subsurface((0, 0, cw, ch)).copy()   # (facing you)
                elif key:
                    img = self.game.assets.get_trainer_image(key)
            except (pygame.error, OSError):
                img = None
            if img is not None:
                box = img.get_bounding_rect()
                img = img.subsurface(box) if box.w and box.h else img
                k = max(1, int(h / max(1, img.get_height())))   # (whole steps: crisp pixels)
                img = pygame.transform.scale(img, (img.get_width() * k, img.get_height() * k))
            self._pic = img or False
        return self._pic or None

    # ---- input
    def _now(self):
        return pygame.time.get_ticks() - self.t0

    def _typed(self):
        return max(0, (self._now() - self.line_t) // TYPE_MS)

    def _tap(self):
        if self.stage == "ring":
            self.stage, self.line_t = "up", self._now()
        elif self.stage == "talk":
            if self._typed() < len(self._line()):
                self.line_t = -10 ** 6     # (finish the line)
            elif self.i < len(self.lines) - 1:
                self.i += 1
                self.line_t = self._now()
            else:
                self.stage, self.down_t = "down", self._now()

    def handle_events(self, events):
        for e in events:
            if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z)):
                self._tap()

    def _line(self):
        return self.lines[min(self.i, len(self.lines) - 1)]

    def update(self):
        t = self._now()
        if self.stage == "ring" and t >= RING_MS:
            self.stage, self.line_t = "up", t
        elif self.stage == "up" and t - self.line_t >= UP_MS:
            self.stage, self.line_t = "talk", t
        elif self.stage == "down" and t - self.down_t >= DOWN_MS:
            self.stage = "done"
            if self.then:
                self.then()

    # ---- drawing
    def _draw_under(self, screen):
        if self._under is None and self.back is not None:
            try:
                self.back.draw()
                self._under = screen.copy()
            except Exception:
                self._under = False
        if self._under:
            screen.blit(self._under, (0, 0))
        dim = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 10, 150))
        screen.blit(dim, (0, 0))

    def draw(self):
        screen = self.game.screen
        w, h = screen.get_size()
        t = self._now()
        f = self.game.assets.fonts
        self._draw_under(screen)
        if self.stage == "ring":   # (the wrist device buzzing in the corner, rings spreading out)
            shake = int(4 * math.sin(t / 30))
            dev = pygame.Rect(0, 0, 120, 92)
            dev.center = (w // 2 + shake, h // 2)
            pygame.draw.rect(screen, FRAME, dev, border_radius=18)
            pygame.draw.rect(screen, FRAME_DARK, dev, 4, border_radius=18)
            pygame.draw.rect(screen, SCREEN, dev.inflate(-34, -34), border_radius=8)
            for k in range(3):
                ph = ((t / 600.0) + k / 3) % 1.0
                r = int(70 + 120 * ph)
                ring = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(ring, (255, 200, 120, int(200 * (1 - ph))), (r, r), r, 3)
                screen.blit(ring, ring.get_rect(center=dev.center))
            theme.shadow_text(screen, "The Xtransceiver is ringing!", f["button"], w // 2, dev.bottom + 40, align="center")
            return
        k = 1.0 if self.stage != "up" else min(1.0, (t - self.line_t) / UP_MS)
        if self.stage in ("down", "done"):
            k = max(0.0, 1 - (t - self.down_t) / DOWN_MS)
        dev = pygame.Rect(0, 0, int(140 + (w * 0.56 - 140) * k), int(110 + (h * 0.60 - 110) * k))
        dev.center = (w // 2, int(h // 2 - 46 * k))
        pygame.draw.rect(screen, FRAME, dev, border_radius=int(18 + 14 * k))
        pygame.draw.rect(screen, FRAME_DARK, dev, 5, border_radius=int(18 + 14 * k))
        scr = dev.inflate(-int(30 + 26 * k), -int(30 + 34 * k))
        pygame.draw.rect(screen, SCREEN, scr, border_radius=10)
        for y in range(scr.y, scr.bottom, 4):   # (video lines)
            pygame.draw.line(screen, (160, 206, 244), (scr.x + 4, y), (scr.right - 4, y))
        if k >= 1 and self.stage == "talk":
            pic = self._picture(int(scr.h * 0.92))
            talking = self._typed() < len(self._line())
            bob = int(3 * math.sin(t / 90)) if talking else int(2 * math.sin(t / 400))
            if pic is not None:
                screen.set_clip(scr)
                screen.blit(pic, pic.get_rect(midtop=(scr.centerx, scr.y + 30 + bob)))
                screen.set_clip(None)
            theme.shadow_text(screen, self.caller.upper(), f["label"], scr.centerx, scr.y + 14, color=(30, 30, 50),
                              shadow=(220, 240, 255), align="center")
            box = pygame.Rect(16, h - 150, w - 32, 134)
            theme.draw_textbox(screen, box)
            font = f["button"]
            text = self._line()
            shown = text[:self._typed()]
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
            if not talking and (t // 400) % 2 == 0:
                pygame.draw.polygon(screen, theme.TEXT_ARROW, [(box.right - 40, box.bottom - 30), (box.right - 24, box.bottom - 30),
                                                               (box.right - 32, box.bottom - 20)])
