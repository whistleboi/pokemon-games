"""Pokestar Studios' movie game (11-20, Jordan: "Place + a movie game"): Black 2 / White 2's moviemaking, simpler.

Pick a script at the studio (only the first at the start; a happy ending opens the next). The set: your co-star across
from you and your rental Pokemon beside you; "Action!". Each beat your co-star says a line and you pick one of three:
the line the script wants (good), a wrong one (bad), or an odd one (strange). All good: a happy ending; two or more odd:
a strange ending; else a sad one. Then the movie is screened: three reviews, your Star Rank (story flag "pokestar_rank",
0-10 stars), and on a happy ending a fan's gift. The scripts are in our own words, after B2W2's films. More scripts: add
to SCRIPTS (each opens after the one before it)."""
import math

import pygame

from src.states.base import GameState
from src.ui import theme

STAR_MAX = 10
FAN_GIFTS = ["LEMONADE", "FRESH_WATER", "SODA_POP", "MOOMOO_MILK", "STAR_PIECE", "BIG_PEARL", "RARE_CANDY"]   # (by Star Rank)

SCRIPTS = [
    {"key": "brycen_man", "title": "Brycen-Man Strikes Back", "costar": "Brycen-Man", "pic": "brycenman.png", "mon": 502,
     "sky": ((40, 30, 70), (120, 70, 140)),
     "intro": "The city is frozen! Brycen-Man has taken it hostage. Only you and Dewott can save it!",
     "beats": [
         {"say": "Brycen-Man: Mwa ha ha! Who dares disturb my frozen city?", "choices": [
             ("I do! Dewott and I will set it free!", "good"), ("Um... sorry, wrong set.", "bad"), ("I'm here for the ice cream.", "odd")]},
         {"say": "Brycen-Man: Then face my icy fury! Will you surrender?", "choices": [
             ("Never! Dewott, Razor Shell!", "good"), ("Okay, you win.", "bad"), ("Can we dance about it instead?", "odd")]},
         {"say": "Brycen-Man: Ugh... You're stronger than I thought. One last chance: join me!", "choices": [
             ("The city's people come first!", "good"), ("Hmm, what's the pay?", "bad"), ("Only if I get a cape too.", "odd")]}],
     "endings": {"good": "Brycen-Man flees, and the city thaws. The crowd cheers its new hero!",
                 "bad": "Brycen-Man wins... The city stays frozen. The end?",
                 "odd": "Brycen-Man and the hero open an ice cream shop together. Nobody saw that coming."}},
    {"key": "full_metal_cop", "title": "Full Metal Cop", "costar": "Robot Boss", "pic": "b2_plasma_grunt_m.png", "mon": 599,
     "sky": ((20, 30, 50), (70, 110, 140)),
     "intro": "In the city of tomorrow, a robot gang runs wild. Officer you, and your partner Klink, are on the case!",
     "beats": [
         {"say": "Robot Boss: Beep boop. Humans and Pokemon cannot stop us.", "choices": [
             ("Klink and I work together. That's our strength!", "good"), ("You're right, we can't.", "bad"), ("Beep boop to you too!", "odd")]},
         {"say": "Robot Boss: Calculating... You have a 1% chance of winning.", "choices": [
             ("Then we'll take that 1%! Klink, Gear Grind!", "good"), ("Let me check my math...", "bad"), ("I only count to 1 anyway.", "odd")]},
         {"say": "Robot Boss: Error... error... What is this feeling?", "choices": [
             ("It's called friendship. Want to try it?", "good"), ("Probably a bug. Bye!", "bad"), ("It's hunger. Have a sandwich.", "odd")]}],
     "endings": {"good": "The robot boss learns about friendship and joins the police. Case closed!",
                 "bad": "The robots take over the city. Officer you is put on traffic duty.",
                 "odd": "The robot boss opens a sandwich stand. Business is booming."}},
    {"key": "mystery_door", "title": "The Mystery Door", "costar": "Ghost Girl", "pic": "b2_guitarist.png", "mon": 562,
     "sky": ((10, 10, 20), (50, 40, 80)),
     "intro": "An old house. A locked door. Something waits behind it... You and Yamask go in.",
     "beats": [
         {"say": "Ghost Girl: Who... is there? Have you come to play with me?", "choices": [
             ("We came to help you. Are you lost?", "good"), ("AAAH! Ghost!", "bad"), ("Do you have a spare key?", "odd")]},
         {"say": "Ghost Girl: I've been waiting so long. Nobody ever stays...", "choices": [
             ("We'll stay with you. Yamask too!", "good"), ("We were just leaving, actually.", "bad"), ("Have you tried knocking?", "odd")]},
         {"say": "Ghost Girl: Will you open the door for me?", "choices": [
             ("Yes. Let's go out together.", "good"), ("No way!", "bad"), ("Only if it's a pull door.", "odd")]}],
     "endings": {"good": "The door opens, and the ghost girl finally goes home. A touching tale!",
                 "bad": "You run out screaming. The door stays locked forever...",
                 "odd": "The door was a pull door all along. Everyone laughs, including the ghost."}},
]


def unlocked(story):
    """The scripts you may shoot: the first, and each after one you finished with a happy ending."""
    out = []
    for i, s in enumerate(SCRIPTS):
        if i == 0 or story.story_flags.get("pokestar_happy_" + SCRIPTS[i - 1]["key"]):
            out.append(s)
    return out


def rank(story):
    return int(story.story_flags.get("pokestar_rank", 0) or 0)


class MovieState(GameState):
    """One movie, shot and screened. back: the state to return to; then(lines): called after, with lines to show."""

    def __init__(self, game, back, script, then=None):
        super().__init__(game)
        self.back, self.script, self.then = back, script, then
        self.stage = "slate" if script else "pick"     # (no script given: the assistant director's list first)
        self.t0 = pygame.time.get_ticks()
        self.stage_t = 0
        self.beat = 0
        self.picks = []
        self.ending = None
        self.reviews = []
        self.gift = None
        self._pics = {}
        self.buttons = []

    def _now(self):
        return pygame.time.get_ticks() - self.t0

    def _go(self, stage):
        self.stage, self.stage_t = stage, self._now()

    # ---- input
    def handle_events(self, events):
        for e in events:
            pos = e.pos if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 else None
            key = e.key if e.type == pygame.KEYDOWN else None
            if self.stage == "pick" and self._now() - self.stage_t > 200:
                pick = None
                if pos:
                    pick = next((i for i, r in enumerate(self.buttons) if r.collidepoint(pos)), None)
                elif key and pygame.K_1 <= key <= pygame.K_9:
                    pick = key - pygame.K_1
                elif key == pygame.K_ESCAPE:
                    pick = len(self.buttons) - 1
                if pick is not None and pick < len(self.buttons):
                    films = unlocked(self.game.story_manager)
                    if pick >= len(films):   # ("Not now")
                        if self.then:
                            self.then(["Assistant director: Come back whenever you're ready to shoot!"])
                        return
                    self.script = films[pick]
                    self._go("slate")
                continue
            if self.stage == "beat" and self._now() - self.stage_t > 300:
                pick = None
                if pos:
                    pick = next((i for i, r in enumerate(self.buttons) if r.collidepoint(pos)), None)
                elif key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    pick = key - pygame.K_1
                if pick is not None:
                    self._choose(pick)
            elif (pos or key in (pygame.K_RETURN, pygame.K_SPACE)) and self._now() - self.stage_t > 350:
                self._next()

    def _order(self):
        """This beat's three lines in a shuffled order (the same each take: the right line isn't always first)."""
        import random
        beat = self.script["beats"][self.beat]
        order = list(range(len(beat["choices"])))
        random.Random("%s/%d" % (self.script["key"], self.beat)).shuffle(order)
        return [beat["choices"][i] for i in order]

    def _choose(self, i):
        choices = self._order()
        if i >= len(choices):
            return
        self.picks.append(choices[i][1])
        self._go("reaction")

    def _next(self):
        if self.stage == "slate":
            self._go("intro")
        elif self.stage == "intro":
            self._go("beat")
        elif self.stage == "reaction":
            self.beat += 1
            if self.beat < len(self.script["beats"]):
                self._go("beat")
            else:
                self._finish()
                self._go("theend")
        elif self.stage == "theend":
            self._go("theater")
        elif self.stage == "theater":
            self._done()

    def _finish(self):
        story = self.game.story_manager
        odd, good = self.picks.count("odd"), self.picks.count("good")
        self.ending = "odd" if odd >= 2 else "good" if good == len(self.picks) else "bad"
        before = rank(story)
        gain = {"good": 2, "odd": 1, "bad": 0}[self.ending]
        story.story_flags["pokestar_rank"] = min(STAR_MAX, before + gain)
        story.story_flags["pokestar_films"] = int(story.story_flags.get("pokestar_films", 0) or 0) + 1
        from src.world import feats as _feats
        _feats.note(story, "films")   # (a Feat: movies shot at Pokestar Studios)
        if self.ending == "good":
            story.story_flags["pokestar_happy_" + self.script["key"]] = True
            self.gift = FAN_GIFTS[min(len(FAN_GIFTS) - 1, rank(story) // 2)]
            story.inventory[self.gift] = story.inventory.get(self.gift, 0) + 1
        self.reviews = {
            "good": ["\"A heartwarming triumph! Two thumbs up!\"", "\"The hero's lines were perfect.\"", "\"I'd watch it again tomorrow!\""],
            "bad": ["\"Hmm... not the ending I hoped for.\"", "\"The hero seemed a little lost.\"", "\"Maybe next time!\""],
            "odd": ["\"What did I just watch?! I loved it!\"", "\"Totally unexpected. A cult classic!\"", "\"Nobody will forget THAT ending.\""],
        }[self.ending]

    def _done(self):
        story = self.game.story_manager
        lines = ["%s: %s ending!" % (self.script["title"], {"good": "A happy", "bad": "A sad", "odd": "A strange"}[self.ending]),
                 "Your Star Rank: %d of %d stars." % (rank(story), STAR_MAX)]
        if self.gift:
            lines.append("A fan gave you %s!" % self.gift.replace("_", " ").title())
        nxt = [s for s in unlocked(story) if not story.story_flags.get("pokestar_happy_" + s["key"])]
        if self.ending == "good" and nxt and nxt[0] is not self.script:
            lines.append("A new script is ready: %s!" % nxt[0]["title"])
        if self.back is not None:
            self.game.change_state(self.back)
        if self.then:
            self.then(lines)

    def update(self):
        if self.stage == "slate" and self._now() - self.stage_t > 1400:
            self._go("intro")

    # ---- drawing
    def _pic(self, key, h, flip=False):
        k = (key, h, flip)
        if k not in self._pics:
            img = None
            try:
                if isinstance(key, int):
                    raw = self.game.loader.fetch_specific(key)
                    from src.pokemon.data import Pokemon
                    img = Pokemon(raw, self.game.assets, size_mult=3.125).image
                else:
                    img = self.game.assets.get_trainer_image(key)
            except Exception:
                img = None
            if img is not None:
                box = img.get_bounding_rect()
                img = img.subsurface(box) if box.w and box.h else img
                s = h / max(1, img.get_height())
                img = pygame.transform.scale(img, (max(1, int(img.get_width() * s)), int(h)))
                if flip:
                    img = pygame.transform.flip(img, True, False)
            self._pics[k] = img
        return self._pics[k]

    def _set(self, screen):
        w, h = screen.get_size()
        top, bot = self.script["sky"]
        for y in range(0, h, 4):
            k = y / h
            c = tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3))
            pygame.draw.rect(screen, c, (0, y, w, 4))
        pygame.draw.rect(screen, (60, 50, 40), (0, int(h * 0.68), w, h))
        t = self._now()
        for i in range(0, w, 160):   # (the studio's lights along the top)
            pygame.draw.circle(screen, (255, 240, 200), (i + 80, 18), 10)
        costar = self._pic(self.script["pic"], int(h * 0.42))
        if costar is not None:
            screen.blit(costar, costar.get_rect(midbottom=(int(w * 0.30), int(h * 0.70) + int(3 * math.sin(t / 300)))))
        mon = self._pic(self.script["mon"], int(h * 0.26), flip=False)
        if mon is not None:
            screen.blit(mon, mon.get_rect(midbottom=(int(w * 0.70), int(h * 0.70))))

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

    def draw(self):
        screen = self.game.screen
        w, h = screen.get_size()
        f = self.game.assets.fonts
        t = self._now() - self.stage_t
        self.buttons = []
        if self.stage == "pick":   # (the assistant director's scripts: the ones you may shoot now)
            screen.fill((30, 22, 18))
            theme.shadow_text(screen, "POKESTAR STUDIOS: PICK A SCRIPT", f["button"], w // 2, 30, align="center")
            theme.shadow_text(screen, "Star Rank: %d of %d" % (rank(self.game.story_manager), STAR_MAX), f["label"], w // 2, 76,
                              align="center")
            films = unlocked(self.game.story_manager)
            for i, s in enumerate(films + [None]):
                r = pygame.Rect(w // 2 - 300, 120 + i * 72, 600, 60)
                pygame.draw.rect(screen, (250, 240, 214) if s else (200, 190, 180), r, border_radius=12)
                pygame.draw.rect(screen, (110, 70, 30), r, 3, border_radius=12)
                label = ("%d.  %s%s" % (i + 1, s["title"], "  (happy ending!)" if self.game.story_manager.story_flags.get(
                    "pokestar_happy_" + s["key"]) else "")) if s else "%d.  Not now" % (i + 1)
                theme.shadow_text(screen, label, f["button"], r.x + 22, r.y + 14, color=(40, 26, 14), shadow=(255, 255, 255))
                self.buttons.append(r)
            return
        if self.stage == "slate":   # (the clapperboard comes down: "Scene 1, take 1... Action!")
            screen.fill((14, 14, 20))
            k = min(1.0, t / 500)
            board = pygame.Rect(0, 0, 420, 240)
            board.center = (w // 2, int(-200 + (h // 2 + 200) * k))
            pygame.draw.rect(screen, (30, 30, 34), board, border_radius=8)
            top = pygame.Rect(board.x, board.y - 46, board.w, 46)
            ang = 0 if t > 900 else 18
            stripes = pygame.Surface(top.size, pygame.SRCALPHA)
            for i in range(0, top.w, 60):
                pygame.draw.polygon(stripes, (240, 240, 240), [(i, 0), (i + 30, 0), (i + 60, 46), (i + 30, 46)])
            stripes = pygame.transform.rotate(stripes, ang)
            screen.blit(stripes, stripes.get_rect(bottomleft=top.bottomleft))
            theme.shadow_text(screen, self.script["title"].upper(), f["button"], board.centerx, board.y + 60, align="center")
            theme.shadow_text(screen, "SCENE 1   TAKE 1", f["label"], board.centerx, board.y + 120, align="center")
            if t > 900:
                theme.shadow_text(screen, "ACTION!", f["title"] if "title" in f else f["button"], w // 2, board.bottom + 50,
                                  color=(255, 220, 90), align="center")
            return
        self._set(screen)
        box = pygame.Rect(16, h - 150, w - 32, 134)
        if self.stage == "intro":
            theme.draw_textbox(screen, box)
            self._text(screen, self.script["intro"], box, f["button"])
        elif self.stage == "beat":
            beat = self.script["beats"][self.beat]
            say = pygame.Rect(16, 16, w - 32, 96)
            theme.draw_textbox(screen, say)
            self._text(screen, beat["say"], say, f["button"])
            for i, (txt, _kind) in enumerate(self._order()):
                r = pygame.Rect(40, h - 210 + i * 66, w - 80, 56)
                pygame.draw.rect(screen, (250, 246, 236), r, border_radius=12)
                pygame.draw.rect(screen, (90, 70, 40), r, 3, border_radius=12)
                theme.shadow_text(screen, "%d.  %s" % (i + 1, txt), f["button"], r.x + 20, r.y + 12, color=(40, 30, 20),
                                  shadow=(255, 255, 255))
                self.buttons.append(r)
        elif self.stage == "reaction":
            theme.draw_textbox(screen, box)
            kind = self.picks[-1]
            self._text(screen, {"good": "Director: Perfect! Keep rolling!", "bad": "Director: Hmm... that's not in the script...",
                                "odd": "Director: ...Wait, what? Keep going, keep going!"}[kind], box, f["button"])
        elif self.stage == "theend":
            veil = pygame.Surface((w, h), pygame.SRCALPHA)
            veil.fill((0, 0, 0, min(220, t // 3)))
            screen.blit(veil, (0, 0))
            theme.shadow_text(screen, "THE END", f["button"], w // 2, h // 2 - 60, color=(255, 230, 150), align="center")
            r = pygame.Rect(60, h // 2 - 10, w - 120, 110)
            theme.draw_textbox(screen, r)
            self._text(screen, self.script["endings"][self.ending], r, f["button"])
        elif self.stage == "theater":   # (the screening: the audience's reviews, your stars)
            screen.fill((24, 10, 16))
            pygame.draw.rect(screen, (120, 20, 30), (0, 0, w, 60))
            theme.shadow_text(screen, "POKESTAR THEATER: " + self.script["title"], f["button"], w // 2, 16, align="center")
            for i, rv in enumerate(self.reviews):
                if t > 400 * (i + 1):
                    theme.shadow_text(screen, rv, f["button"], w // 2, 120 + i * 60, align="center")
            stars = rank(self.game.story_manager)
            for i in range(STAR_MAX):
                cx, cy = w // 2 - 4.5 * 44 + i * 44, h - 170
                col = (255, 214, 60) if i < stars else (80, 70, 60)
                pts = [(cx + 16 * math.cos(math.pi / 2 + k * math.pi / 5) * (1 if k % 2 == 0 else 0.45),
                        cy - 16 * math.sin(math.pi / 2 + k * math.pi / 5) * (1 if k % 2 == 0 else 0.45)) for k in range(10)]
                pygame.draw.polygon(screen, col, pts)
            theme.shadow_text(screen, "STAR RANK", f["label"], w // 2, h - 140, align="center")
