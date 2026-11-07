"""Real-time battles on the walked maps (Jordan, 11-06), Legends: Z-A's way: Options > BATTLES: REAL-TIME
(every walked route), and always in Hyperspace Lumiose. Max Raids stay traditional.

The battle is the traditional one, one for one: the same TrainerBattleState / WildBattleState is made
(its Pokemon, their levels, its rewards) but not shown. A trainer's intro lines come first in the map's text
box (no intro animation), then straight into it (Jordan, 11-06: no math question first): both sides
attack in real time: each move recharges on its own (stronger moves take longer), a short pause after every
attack, a quick animation (an orb of the move's type's colour, or a lunge), small HP bars over the two
Pokemon.

You keep walking while it goes on (keys, or a tap on the map): your Pokemon follows you loosely (it stays
where it is until you're FOLLOW tiles away), and the foe follows your Pokemon, so you can lead the fight
somewhere else. A move reaches REACH tiles; a hit on the foe's side or back (where it isn't looking: it
looks the way it last stepped or struck) does more.

MEGA (with a Key Stone and the Pokemon's stone): your lead Mega Evolves for a minute, between fights too,
then the Key Stone rests 30 seconds (src/pokemon/mega_clock.py). On the map too, as in Legends: Z-A: the
MEGA button is there whenever the Pokemon following you can Mega Evolve.

POKEMON (or Tab), on the right, on the map and in a fight: your party in a list above it. Tap one to send
it out (in a fight) or to have it follow you (on the map); right-click it, or tap its potion, to heal it with
your strongest potion (a Revive if it's fainted). In a fight, pick another Pokemon; it comes out where the last one stood (it leads
your party from then on, and follows you), its moves fresh, after a moment's pause. A trainer throws its Pokemon out onto the tile in front of it, one after another. Each knock-out
gives the battle's own XP (_award_battle_xp: Exp. Share, the level cap, new moves); a win the battle's own
rewards and story steps (its victory text, then exit_battle), and back on the map as after any battle."""
import math
import random

import pygame

from src.config import FPS
from src.pokemon import balance, forms, mega_clock, moves as mv
from src.pokemon.mechanics import TypeAdvantage
from src.ui import theme

TYPE_COLOR = {"NORMAL": (168, 168, 120), "FIRE": (240, 128, 48), "WATER": (104, 144, 240), "GRASS": (120, 200, 80),
              "ELECTRIC": (248, 208, 48), "ICE": (152, 216, 216), "FIGHTING": (192, 48, 40), "POISON": (160, 64, 160),
              "GROUND": (224, 192, 104), "FLYING": (168, 144, 240), "PSYCHIC": (248, 88, 136), "BUG": (168, 184, 32),
              "ROCK": (184, 160, 56), "GHOST": (112, 88, 152), "DRAGON": (112, 56, 248), "DARK": (112, 88, 72),
              "STEEL": (184, 184, 208), "FAIRY": (238, 153, 172)}
_MOVES = {}


def move_info(game, name):
    if not _MOVES:
        import json
        import os
        with open(os.path.join(game.assets.assets_dir, "moves.json"), encoding="utf-8") as f:
            _MOVES.update(json.load(f))
    return _MOVES.get(str(name).upper().replace(" ", "-")) or {}


class RealTime:
    RT_MODES = ("RT", "RTCATCH")
    PAUSE = 0.8   # seconds after any attack before the next (breathing room)
    SHOT = 0.35   # the attack's quick animation
    FOLLOW = 3    # your Pokemon lets you get this many tiles away before it follows
    CLOSE = 2     # the foe comes this close to your Pokemon
    REACH = 4     # how far a move reaches (tiles)
    LEASH = 8     # how far from the foe you can walk (a trainer battle: you stay in it)
    PARTNER_STEP = 0.24  # seconds a step takes: your Pokemon (an easy pace), the foe (slower)
    FOE_STEP = 0.42
    SIDE, BACK = 1.15, 1.3  # a hit on the foe's side, on its back
    rt = None

    # ---------------------------------------------------------------- when
    def _rt_on(self):
        story = self.game.story_manager
        return getattr(story, "battle_style", "") == "REALTIME" and not getattr(self, "contest", None)

    # ---------------------------------------------------------------- the battle behind it
    def _capture_state(self, fn):
        """Run fn and catch the screen it would change to (the battle), without changing to it."""
        caught = []
        orig = self.game.change_state
        self.game.change_state = lambda state, *a, **k: caught.append(state)
        try:
            with self._ui_kept():
                fn()
        finally:
            self.game.change_state = orig
        return caught[-1] if caught else None

    def _ui_kept(self):
        """While the hidden battle is made: the buttons it adds (its FIGHT / BAG / POKEMON / RUN) don't stay
        on the map's screen (Jordan, 11-06: RUN opened its Bag, and closing the Bag started it)."""
        import contextlib
        ui = self.game.ui_manager

        @contextlib.contextmanager
        def kept():
            before = list(ui.elements)
            try:
                yield
            finally:
                ui.elements[:] = [e for e in ui.elements if e in before]
        return kept()

    def _rt_wild(self, mover):
        from src.states.battle import WildBattleState
        self.walk_goal = None
        self.rounds_completed += 1
        with self._ui_kept():
            battle = WildBattleState(self.game, mover.payload, self.area_key,
                                     background_image=self._get_battle_background_for_area())
        battle.play_state_data = self._play_data()
        self._rt_start(mover, battle, wild=True)

    def _rt_trainer(self, mover):
        """The route's own trainer battle (made as the traditional one is), its intro lines, then real time."""
        from src.states.battle import TrainerBattleState, TrainerIntroState
        self.pending = ("trainer", mover)
        self.mode = "MAP"
        self.rounds_completed += 1
        state = self._capture_state(lambda: self.trigger_trainer_battle(specific_index=mover.payload[0]))
        battle = state.next_state if isinstance(state, TrainerIntroState) else state
        if not isinstance(battle, TrainerBattleState):  # (anything else: as it would have gone)
            if state is not None:
                self.game.change_state(state)
            return
        lines = list(getattr(state.dialogue_box, "text_lines", []) or []) if isinstance(state, TrainerIntroState) else []
        name = getattr(battle, "trainer_name", "") or (mover.payload[1] or {}).get("name", "A trainer")
        lines = [f"{name}: {l}" if l and str(name).upper() not in str(l).upper() and ":" not in str(l)[:24] else l
                 for l in lines]
        self.say(lines or [f"{name} wants to battle!"], then=lambda: self._rt_start(mover, battle, wild=False))

    # ---------------------------------------------------------------- the fight
    def _rt_start(self, mover, battle, wild):
        foes = [p for p in (battle.opponent_team or []) if p]
        for p in foes:
            mv.ensure_moves(self.game, p)
        self.encounter = mover
        self.chart = TypeAdvantage(self.game.loader.area_data.get("TYPE_CHART", {}))
        spot = (mover.x, mover.y) if wild else self._throw_spot(mover)
        self._partner_beside(spot)
        self.walk_goal = None
        self.rt = {"mover": mover, "battle": battle, "foes": foes, "i": 0, "wild": wild, "cd": [0, 0, 0, 0],
                   "foe_cd": int(FPS * 1.4), "power": 1.0, "fx": [], "focus": 1.0, "spot": spot, "busy": 0,
                   "shot": None, "throw": 0 if wild else int(FPS * 0.6), "fought": [],
                   "f_from": spot, "f_anim": 0, "p_anim": 0, "face": self._toward(spot, self.partner)}
        self.mode = "RT"
        who = f"A wild {foes[0].display_name.upper()}" if wild else (battle.trainer_name or "The trainer")
        self.flash(f"{who}! Walk to move the fight.", 120)

    # ---------------------------------------------------------------- moving about in it
    @staticmethod
    def _dist(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @staticmethod
    def _toward(a, b):
        """The way from tile a to tile b, as one of the four directions."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        if abs(dx) >= abs(dy) and dx:
            return (1 if dx > 0 else -1, 0)
        return (0, 1 if dy >= 0 else -1)

    def _rt_blocked(self):
        """Tiles no one in the fight steps onto: everyone else on the map, the ways out, the three of you."""
        rt = self.rt
        f = self.run.floor
        out = set(f.exits)
        for m in f.movers:
            if m is rt["mover"] and rt["wild"]:
                continue  # (its place is rt["spot"])
            k = getattr(m, "size", 1)
            out |= {(m.x + i, m.y + j) for i in range(k) for j in range(k)}
        return out | {rt["spot"], self.partner, self.run.player}

    def _rt_path_step(self, start, goal):
        """The next tile from start on the way to goal (not goal itself), or None."""
        from src.dungeon import core
        steps = core.path(self.run.floor, start, goal, self._rt_blocked() - {start})
        return steps[0] if steps and steps[0] != goal else None

    def _rt_step(self, dx, dy):
        """You take a step while the battle goes on."""
        from src.states.overworld.dungeon import STEP_FRAMES
        rt = self.rt
        if not rt or self.mode != "RT" or self.anim > 0 or self.dialogue_box.visible:
            return False
        self.facing = (dx, dy)
        px, py = self.run.player
        to = (px + dx, py + dy)
        f = self.run.floor
        if not f.walkable(*to) or to in self._rt_blocked() - {self.partner}:
            self.walk_goal = None
            return False
        if self._dist(to, rt["spot"]) > self.LEASH:
            self.walk_goal = None
            self.flash("Too far! Tap RUN to get away." if rt["wild"] else "Stay close to the battle!", 60)
            return False
        if to == self.partner:  # (you swap places with your Pokemon)
            self.partner_from, self.partner = self.partner, (px, py)
            rt["p_anim"] = int(FPS * self.PARTNER_STEP)
        self.anim_from, self.anim = (px, py), STEP_FRAMES
        self.run.player = to
        self.run.reveal()
        if to in f.items:
            self._pick_up(f.items.pop(to))
        return True

    def _rt_walk(self):
        """Each frame: your walk to a tapped tile, your Pokemon following you, the foe following it."""
        rt = self.rt
        if self.walk_goal and self.anim == 0:
            here = self.run.player
            if self.walk_goal == here:
                self.walk_goal = None
            else:
                nxt = self.walk_goal if self._dist(self.walk_goal, here) == 1 else \
                    self._rt_path_step(here, self.walk_goal)
                if nxt is None or not self._rt_step(nxt[0] - here[0], nxt[1] - here[1]):
                    self.walk_goal = None
        attacking = rt["shot"] and rt["shot"]["from"] == "me"
        if rt["p_anim"] > 0:
            rt["p_anim"] -= 1
        elif not attacking and self._dist(self.partner, self.run.player) > self.FOLLOW:
            nxt = self._rt_path_step(self.partner, self.run.player)
            self.partner_from = self.partner
            if nxt:
                self.partner = nxt
            rt["p_anim"] = int(FPS * self.PARTNER_STEP)
        foe = self._foe()
        if rt["f_anim"] > 0:
            rt["f_anim"] -= 1
        elif not (rt["shot"] and rt["shot"]["from"] == "foe") and rt["throw"] <= 0 and foe is not None \
                and foe.current_hp > 0 and self._dist(rt["spot"], self.partner) > self.CLOSE:
            nxt = self._rt_path_step(rt["spot"], self.partner)
            rt["f_from"] = rt["spot"]
            if nxt:
                rt["face"] = self._toward(rt["spot"], nxt)
                rt["spot"] = nxt
                if rt["wild"]:
                    rt["mover"].x, rt["mover"].y = nxt
            rt["f_anim"] = int(FPS * self.FOE_STEP)

    def _angle(self):
        """Where your Pokemon is, for the foe: "front", "side" or "back" (of the way it looks)."""
        rt = self.rt
        fx, fy = rt["face"]
        vx, vy = self.partner[0] - rt["spot"][0], self.partner[1] - rt["spot"][1]
        dot = fx * vx + fy * vy
        return "back" if dot < 0 else "side" if dot == 0 else "front"

    def _throw_spot(self, mover):
        """The tile a trainer's Pokemon lands on: in front of it, toward you."""
        f = self.run.floor
        px, py = self.run.player
        near = [(mover.x + dx, mover.y + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
        near = [t for t in near if t != (px, py) and f.walkable(*t) and not f.occupied(*t)]
        return min(near, key=lambda t: abs(t[0] - px) + abs(t[1] - py)) if near else (mover.x, mover.y)

    def _partner_beside(self, at):
        """Your lead Pokemon steps up beside the foe (it fights; you stand back)."""
        f = self.run.floor
        px, py = self.run.player
        ax, ay = at
        spots = [(ax + dx, ay + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
        spots = [s for s in spots if s != (px, py) and f.walkable(*s) and not f.occupied(*s)]
        if spots:
            self.partner = self.partner_from = min(spots, key=lambda s: abs(s[0] - px) + abs(s[1] - py))

    # ---------------------------------------------------------------- Mega Evolution (a minute, then a rest)
    def _rt_mega_option(self):
        me = self._me()
        if not me or mega_clock.active(self.game) or mega_clock.cooling(self.game):
            return None
        return forms.player_form(self.game.assets, me, self.game.story_manager.inventory, False)

    def _rt_mega(self):
        rt = self.rt
        form = self._rt_mega_option()
        if not rt or self.mode != "RT" or not form:
            return
        me = self._me()
        lines = mega_clock.start(self.game, me, form)
        self.flash(lines[-1], 120)
        self._fx("me", "MEGA!", (255, 140, 220), str((form.get("types") or ["NORMAL"])[0]).upper())
        if me.cry:
            me.cry.play()

    # ---------------------------------------------------------------- Mega Evolution on the map (Legends: Z-A)
    def _map_mega_button(self):
        """The map's MEGA button (rect, label, colour, action, enabled, small text), or None (no Key Stone, or
        the Pokemon following you has no Mega Stone)."""
        lead = self.lead()
        story = self.game.story_manager
        if not lead or lead.current_hp <= 0 or not self._rt_on():
            return None
        m = mega_clock.state(self.game)
        r = self._rt_mega_rect()
        if mega_clock.active(self.game):
            return (r, "MEGA", (200, 70, 160), self._map_mega, False, f"{(m['left'] + FPS - 1) // FPS}s left")
        form = forms.player_form(self.game.assets, lead, story.inventory, False)
        if form is None:
            return None
        if mega_clock.cooling(self.game):
            return (r, "MEGA", (200, 70, 160), self._map_mega, False, f"ready in {(m['cool'] + FPS - 1) // FPS}s")
        return (r, "MEGA", (220, 80, 180), self._map_mega, True, "Mega Evolve")

    def _map_mega(self):
        lead = self.lead()
        if not lead or mega_clock.active(self.game) or mega_clock.cooling(self.game) or not self._rt_on():
            return
        form = forms.player_form(self.game.assets, lead, self.game.story_manager.inventory, False)
        if not form:
            return
        lines = mega_clock.start(self.game, lead, form)
        self.flash(lines[-1], 120)
        if lead.cry:
            lead.cry.play()

    # ---------------------------------------------------------------- the POKEMON button's party list
    qp_open = False
    HEALS = ("MAX_POTION", "HYPER_POTION", "SUPER_POTION", "POTION")  # (strongest first)
    REVIVES = ("MAX_REVIVE", "REVIVE")

    def _qp_button_rect(self):
        W, H = self.game.width, self.game.height
        return pygame.Rect(W - 280, H - 162, 126, 70)

    def _qp_rects(self):
        """A card a row, above the POKEMON button (the first at the top)."""
        b = self._qp_button_rect()
        n = len(self.game.story_manager.player_team)
        w, h, gap = 300, 56, 6
        x = self.game.width - 20 - w
        y0 = b.y - 10 - n * h - (n - 1) * gap
        return [pygame.Rect(x, y0 + k * (h + gap), w, h) for k in range(n)]

    def _qp_party_rect(self):
        """The list's top line: the full party screen (on the map)."""
        rects = self._qp_rects()
        top = rects[0].y if rects else self._qp_button_rect().y
        return pygame.Rect(self.game.width - 320, top - 44, 300, 36)

    @staticmethod
    def _qp_heal_rect(r):
        return pygame.Rect(r.right - 42, r.y + (r.h - 36) // 2, 36, 36)

    def _qp_best(self, p):
        """The item a quick heal would use on p (its strongest), or None."""
        inv = self.game.story_manager.inventory
        if p is None or getattr(p, "is_egg", False):
            return None
        if p.current_hp <= 0:
            return next((k for k in self.REVIVES if inv.get(k, 0) > 0), None)
        if p.current_hp >= p.get_max_hp():
            return None
        return next((k for k in self.HEALS if inv.get(k, 0) > 0), None)

    def _quick_heal(self, i):
        from src.pokemon import items as itemlib
        team = self.game.story_manager.player_team
        p = team[i] if i < len(team) else None
        if p is None or getattr(p, "is_egg", False):
            return
        item = self._qp_best(p)
        if item is None:
            name = p.display_name.upper()
            if p.current_hp <= 0:
                self.flash("No Revives in the Bag!", 60)
            elif p.current_hp >= p.get_max_hp():
                self.flash(f"{name}'s HP is full!", 60)
            else:
                self.flash("No potions in the Bag!", 60)
            return
        used, lines = itemlib.medicine_effect(item, p)
        if not used:
            return
        inv = self.game.story_manager.inventory
        inv[item] = inv.get(item, 0) - 1
        if inv[item] <= 0:
            inv.pop(item, None)
        if self.game.assets.heal_sfx:
            self.game.assets.heal_sfx.play()
        self.flash(f"{forms.item_label(item).upper()}: {lines[-1]}", 90)
        if self.rt and self.mode == "RT":  # (it takes a moment in a fight)
            self.rt["busy"] = max(self.rt["busy"], int(FPS * 0.8))

    def _qp_pick(self, i):
        """Tap a Pokemon in the list: in a fight it comes out; on the map it follows you."""
        if self.rt and self.mode == "RT":
            return self._rt_switch_to(i)
        team = self.game.story_manager.player_team
        p = team[i] if i < len(team) else None
        if p is None or getattr(p, "is_egg", False) or p.current_hp <= 0:
            self.flash("That one can't walk with you right now.", 60)
            return
        if p is not self.lead():
            team[0], team[i] = team[i], team[0]
            self.flash(f"{p.display_name.upper()} is following you now!", 60)
            if p.cry:
                p.cry.play()
        self.qp_open = False

    def _qp_toggle(self):
        self.qp_open = not self.qp_open

    def _qp_event(self, e):
        """The POKEMON button and its list (on the map and in a fight). True if it used the event."""
        if self.dialogue_box.visible or self.mode not in ("MAP", "RT"):
            return False
        if e.type == pygame.MOUSEBUTTONDOWN and e.button in (1, 3):
            if self._qp_button_rect().collidepoint(e.pos):
                if e.button == 1:
                    self._qp_toggle()
                return True
            if not self.qp_open:
                return False
            for i, r in enumerate(self._qp_rects()):
                if r.collidepoint(e.pos):
                    if e.button == 3 or self._qp_heal_rect(r).collidepoint(e.pos):
                        self._quick_heal(i)
                    else:
                        self._qp_pick(i)
                    return True
            if self.mode == "MAP" and e.button == 1 and self._qp_party_rect().collidepoint(e.pos):
                self.qp_open = False
                self._open_party()
                return True
            self.qp_open = False  # (a tap anywhere else closes it)
            return True
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_TAB:
                self._qp_toggle()
                return True
            if self.qp_open and pygame.K_1 <= e.key <= pygame.K_6:
                self._qp_pick(e.key - pygame.K_1)
                return True
            if self.qp_open and e.key == pygame.K_ESCAPE:
                self.qp_open = False
                return True
        return False

    def _draw_qparty(self, screen):
        """The POKEMON button (in a fight; on the map it's one of the map's buttons) and its list."""
        if self.dialogue_box.visible or self.mode not in ("MAP", "RT"):
            return
        fonts = self.game.assets.fonts
        mouse = pygame.mouse.get_pos()
        b = self._qp_button_rect()
        if self.mode == "RT" or self.qp_open:
            theme.command_button(screen, b, theme.pokemon_word("POKEMON"), fonts["caption"], theme.POKEMON,
                                 hover=self.qp_open or b.collidepoint(mouse))
        if not self.qp_open:
            return
        from src.minigames.base import icon
        me = self.lead()
        if self.mode == "MAP":
            pr = self._qp_party_rect()
            theme.command_button(screen, pr, "PARTY SCREEN", fonts["small"], theme.BAG, hover=pr.collidepoint(mouse))
        for i, (p, r) in enumerate(zip(self.game.story_manager.player_team, self._qp_rects())):
            if p is None:
                continue
            ok = p.current_hp > 0 and not getattr(p, "is_egg", False)
            theme.card(screen, r, hover=r.collidepoint(mouse), selected=p is me, accent=theme.POKEMON)
            img = icon(self.game, p.id, 48)
            if not ok:
                img = img.copy()
                img.set_alpha(90)
            screen.blit(img, img.get_rect(center=(r.x + 30, r.centery)))
            heal = self._qp_heal_rect(r)
            best = self._qp_best(p)
            pygame.draw.rect(screen, (220, 240, 225) if best else (225, 225, 230), heal, border_radius=8)
            pygame.draw.rect(screen, (90, 200, 120) if best else (180, 180, 190), heal, 2, border_radius=8)
            pimg = self._item_img(best or "POTION", 28)
            if pimg is not None:
                if not best:
                    pimg = pimg.copy()
                    pimg.set_alpha(70)
                screen.blit(pimg, pimg.get_rect(center=heal.center))
            ink = (40, 40, 60) if ok else (160, 160, 170)
            lv = fonts["small"].render(f"Lv{p.level}" if ok else "fainted", True, (110, 110, 130))
            right = heal.x - 8
            name = p.display_name.upper()  # (the whole top line: MEGA VENUSAUR fits)
            while len(name) > 3 and fonts["small"].size(name)[0] > right - (r.x + 58):
                name = name[:-1]
            screen.blit(fonts["small"].render(name, True, ink), (r.x + 58, r.y + 7))
            screen.blit(lv, lv.get_rect(bottomright=(right, r.bottom - 6)))
            k = max(0, p.current_hp) / max(1, p.get_max_hp())
            bar = pygame.Rect(r.x + 58, r.bottom - 16, right - lv.get_width() - 8 - (r.x + 58), 8)
            pygame.draw.rect(screen, (20, 20, 30), bar, border_radius=3)
            col = (90, 220, 110) if k > 0.5 else (240, 200, 60) if k > 0.2 else (230, 70, 60)
            pygame.draw.rect(screen, col, (bar.x, bar.y, int(bar.w * k), bar.h), border_radius=3)
            n = fonts["small"].render(str(i + 1), True, (150, 150, 170))
            screen.blit(n, (r.x + 4, r.y + 2))

    def _rt_switch_to(self, i):
        rt = self.rt
        team = self.game.story_manager.player_team
        if not rt or self.mode != "RT" or i >= len(team) or rt["shot"]:
            return
        p = team[i]
        if p is None or p.current_hp <= 0 or getattr(p, "is_egg", False):
            self.flash("That one can't battle!", 45)
            return
        if p is self._me():
            self.qp_open = False
            return
        team[0], team[i] = team[i], team[0]  # (it leads, and follows you, from now on)
        mv.ensure_moves(self.game, p)
        rt["cd"] = [0, 0, 0, 0]
        rt["busy"] = int(FPS * 1.0)
        rt["focus"] = 1.0
        self.qp_open = False
        self.flash(f"Go, {p.display_name.upper()}!", 60)
        if p.cry:
            p.cry.play()

    def _rt_mega_rect(self):
        H = self.game.height
        return pygame.Rect(20, H - 74 - 110, 170, 60)

    def _me(self):
        lead = self.lead()
        return lead if lead and lead.current_hp > 0 else None

    def _foe(self):
        rt = self.rt
        return rt["foes"][rt["i"]] if rt and rt["i"] < len(rt["foes"]) else None

    def _my_moves(self, me):
        mv.ensure_moves(self.game, me)
        return list(me.moves or [])[:4] or ["TACKLE"]

    def _cooldown(self, name, poke):
        """A move's recharge (like Legends: Z-A's): stronger moves take longer; a fast Pokemon a bit less."""
        power = move_info(self.game, name).get("power") or 0
        speed = poke.stat_value("SPEED")
        base = 1.6 + power / 45 if power else 3.0
        return int(FPS * base * (1.15 - min(0.3, speed / 400)))

    def _hit(self, att, dfn, name, mult=1.0):
        info = move_info(self.game, name)
        power = info.get("power") or 0
        kind = str(info.get("type") or "NORMAL").upper()
        special = str(info.get("category") or "").upper() == "SPECIAL"
        attack = att.stat_value("SPATK" if special else "ATTACK")
        defense = dfn.stat_value("SPDEF" if special else "DEFENSE")
        eff = self.chart.get_multiplier(kind, dfn.types or [])
        if eff == 0:
            return 0, eff, kind
        dmg, _crit = balance.damage(att.level, power, attack, defense, stab=kind in (att.types or []), effectiveness=eff)
        dmg = max(1, int(dmg * mult))
        dfn.current_hp = max(0, dfn.current_hp - dmg)
        return dmg, eff, kind

    def _fx(self, who, text, color, kind=None):
        self.rt["fx"].append({"who": who, "text": text, "color": color, "t": int(FPS * 0.9), "kind": kind})

    def _shoot(self, who, kind, physical, then):
        rt = self.rt
        rt["shot"] = {"from": who, "t": 0, "dur": int(FPS * self.SHOT), "kind": kind, "physical": physical, "then": then}
        rt["busy"] = int(FPS * (self.SHOT + self.PAUSE))

    def _rt_use(self, k):
        me, foe = self._me(), self._foe()
        rt = self.rt
        if not rt or not me or not foe or rt["cd"][k] > 0 or rt["busy"] > 0 or rt["throw"] > 0 or rt["shot"]:
            return
        moves = self._my_moves(me)
        if k >= len(moves):
            return
        name = moves[k]
        info = move_info(self.game, name)
        if info.get("power") and self._dist(self.partner, rt["spot"]) > self.REACH:
            self.flash("Too far away! Walk closer.", 45)
            return
        rt["cd"][k] = self._cooldown(name, me)
        if not any(p is me for p in rt["fought"]):
            rt["fought"].append(me)
        if not info.get("power"):  # a status move: the next hit lands harder
            rt["focus"] = 1.5
            rt["busy"] = int(FPS * self.PAUSE)
            self._fx("me", "Focused!", (255, 230, 120))
            return

        angle = self._angle()

        def land():
            bonus = self.BACK if angle == "back" else self.SIDE if angle == "side" else 1.0
            got = self._hit(me, foe, name, rt["power"] * rt["focus"] * bonus)
            rt["focus"] = 1.0
            dmg, eff, kind = got
            self._fx("foe", f"-{dmg}" if dmg else "No effect", (255, 255, 255), kind)
            if dmg and angle != "front":
                self._fx("foe", "From behind!" if angle == "back" else "From the side!", (150, 230, 255))
            if eff > 1:
                self._fx("foe", "Super effective!", (255, 220, 90))
            elif 0 < eff < 1:
                self._fx("foe", "Not very effective", (200, 200, 210))
        self._shoot("me", str(info.get("type") or "NORMAL").upper(),
                    str(info.get("category") or "").upper() == "PHYSICAL", land)

    def _rt_foe_turn(self):
        me, foe = self._me(), self._foe()
        moves = [m for m in (foe.moves or []) if (move_info(self.game, m).get("power") or 0) > 0] or ["TACKLE"]
        name = random.choice(moves)
        info = move_info(self.game, name)
        self.rt["foe_cd"] = int(self._cooldown(name, foe) * random.uniform(1.0, 1.4))
        self.rt["face"] = self._toward(self.rt["spot"], self.partner)  # (it turns to strike)

        def land():
            dmg, eff, kind = self._hit(foe, me, name)
            self._fx("me", f"-{dmg}", (255, 120, 110), kind)
            if me.current_hp <= 0:
                self.flash(f"{me.display_name.upper()} fainted!", 90)
                self.rt["cd"] = [0, 0, 0, 0]
        self._shoot("foe", str(info.get("type") or "NORMAL").upper(),
                    str(info.get("category") or "").upper() == "PHYSICAL", land)

    def _rt_update(self):
        rt = self.rt
        if not rt:
            return
        for f in rt["fx"]:
            f["t"] -= 1
        rt["fx"] = [f for f in rt["fx"] if f["t"] > 0]
        if self.mode != "RT" or self.dialogue_box.visible:
            return
        self._rt_walk()
        if rt["throw"] > 0:
            rt["throw"] -= 1
            return
        shot = rt["shot"]
        if shot:
            shot["t"] += 1
            if shot["t"] >= shot["dur"]:
                rt["shot"] = None
                shot["then"]()
        rt["busy"] = max(0, rt["busy"] - 1)
        me, foe = self._me(), self._foe()
        if me is None:
            if not any(p and p.current_hp > 0 for p in self.game.story_manager.player_team):
                return self._rt_lost()
            return
        if foe is None:
            return self._rt_won()
        if foe.current_hp <= 0:
            if rt["shot"]:
                return
            self._rt_ko(me, foe)
            return
        rt["cd"] = [max(0, c - 1) for c in rt["cd"]]
        rt["foe_cd"] -= 1
        if rt["foe_cd"] <= 0 and rt["busy"] <= 0 and not rt["shot"]:
            if self._dist(rt["spot"], self.partner) > self.REACH:
                rt["foe_cd"] = int(FPS * 0.3)  # (out of its reach: it comes closer first)
            else:
                self._rt_foe_turn()

    def _rt_ko(self, me, foe):
        """A knock-out: the battle's own XP (Exp. Share, the level cap, new moves), then the next one."""
        rt = self.rt
        b = rt["battle"]
        b.player_pokemon, b.opponent_pokemon = me, foe
        b._xp_participants = [p for p in rt["fought"] if p.current_hp > 0] or [me]
        try:
            lines = b._award_battle_xp()
        except Exception as e:  # (never stop the fight on it)
            print("Real-time XP failed:", e)
            lines = []
        rt["fought"] = []
        if rt["wild"]:  # (like Legends: Z-A: a catch window once it's down)
            self.mode, self.walk_goal = "RTCATCH", None
            if lines:
                self.flash(lines[0], 120)
            return
        for k, line in enumerate(lines[:3]):
            self._fx("me", line.replace(me.display_name.upper() + " ", "")[:24], (140, 230, 140))
        if lines:
            self.flash(lines[0], 90)
        rt["i"] += 1
        rt["foe_cd"] = int(FPS * 1.6)
        if self._foe() is None:
            return self._rt_won()
        rt["throw"] = int(FPS * 0.6)  # (the next one thrown out)
        self.flash(f"{b.trainer_name or 'The trainer'} sent out {self._foe().display_name.upper()}!", 90)

    def _rt_won(self):
        """The battle's own win: its victory lines and rewards, then exit_battle (money, items, TMs, story
        steps, the trainer beaten) and back on the map as after any battle."""
        rt = self.rt
        b = rt["battle"]
        mover = rt["mover"]
        self.rt, self.mode, self.walk_goal = None, "MAP", None
        self.pending = ("wild" if rt["wild"] else "trainer", mover)
        b.player_won = True
        lines = []
        if not rt["wild"]:
            won = (getattr(b, "custom_dialogue", None) or {}).get("player_won")
            lines += won if isinstance(won, list) else ([won] if won else [f"You beat {b.trainer_name}!"])
            try:
                b.phase = "VICTORY_TEXT"
                with self._ui_kept():
                    b.advance_victory_sequence()  # (it lists the rewards in its text box)
                lines += list(b.dialogue_box.text_lines or [])
            except Exception as e:
                print("Real-time rewards text failed:", e)
        else:
            lines.append(f"The wild {rt['foes'][0].display_name.upper()} fainted!")
        self.say(lines, then=lambda: mega_clock.keep_through(self.game, b.exit_battle))  # (a Mega's minute goes on)

    def _rt_lost(self):
        rt = self.rt
        b = rt["battle"]
        self.rt, self.mode, self.walk_goal = None, "MAP", None
        if mega_clock.active(self.game):
            mega_clock._end(self.game, say=False)
        lost = (getattr(b, "custom_dialogue", None) or {}).get("player_lost")
        lines = lost if isinstance(lost, list) else ([lost] if lost else [])
        self.say(lines + ["Your Pokemon are out of energy!", "You hurried back to safety..."], then=b.perform_battle_black_out)

    def _rt_catch_rects(self):
        W, H = self.game.width, self.game.height
        return pygame.Rect(W // 2 - 330, int(H * 0.66), 300, 110), pygame.Rect(W // 2 + 30, int(H * 0.66), 300, 110)

    def _rt_catch(self, throw):
        """The catch window, after a wild one faints: throw a ball (the map's catch, its math question), or let it
        go (the battle's own win: its rewards)."""
        rt = self.rt
        if not throw:
            return self._rt_won()
        if not self._can_catch():
            story = self.game.story_manager
            self.flash("You can't catch Pokemon yet!" if not story.catch_unlocked() else "You're out of Poke Balls!")
            return
        self.rt = None
        self.encounter = rt["mover"]
        foe = rt["foes"][0]
        foe.current_hp = foe.get_max_hp()  # (a Pokemon caught joins healthy, as on the map)
        self._start_math()  # (then THROW, then the catch: party or PC, Pokedex, as on the map)

    def _rt_run(self):
        rt = self.rt
        if not rt or not rt["wild"]:
            return
        m = rt["mover"]
        f = self.run.floor
        spots = [(x, y) for x in range(f.w) for y in range(f.h) if f.walkable(x, y) and not f.occupied(x, y)
                 and abs(x - self.run.player[0]) + abs(y - self.run.player[1]) > 8]
        if spots:
            m.x, m.y = random.choice(spots)
        m.alert = False
        self.flash("You got away!")
        self.rt, self.mode, self.encounter, self.walk_goal = None, "MAP", None, None

    # ---------------------------------------------------------------- input
    def _rt_rects(self):
        W, H = self.game.width, self.game.height
        bw, bh, gap = 250, 74, 14
        x0 = W // 2 - (4 * bw + 3 * gap) // 2
        return [pygame.Rect(x0 + i * (bw + gap), H - bh - 18, bw, bh) for i in range(4)], \
            pygame.Rect(W - 146, H - 162, 126, 70)  # (RUN: beside the POKEMON button)

    def _rt_events(self, events):
        for e in events:
            if self.dialogue_box.visible:
                if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or \
                        (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)):
                    self.dialogue_box.advance()
                continue
            if self.mode == "RTCATCH":
                throw_r, go_r = self._rt_catch_rects()
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if throw_r.collidepoint(e.pos):
                        self._rt_catch(True)
                    elif go_r.collidepoint(e.pos):
                        self._rt_catch(False)
                elif e.type == pygame.KEYDOWN and e.key in (pygame.K_1, pygame.K_c, pygame.K_RETURN):
                    self._rt_catch(True)
                elif e.type == pygame.KEYDOWN and e.key in (pygame.K_2, pygame.K_ESCAPE):
                    self._rt_catch(False)
            elif self.mode == "RT":
                moves, run = self._rt_rects()
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    hit = [i for i, r in enumerate(moves) if r.collidepoint(e.pos)]
                    if hit:
                        self._rt_use(hit[0])
                    elif self._rt_mega_rect().collidepoint(e.pos) and self._rt_mega_option():
                        self._rt_mega()
                    elif run.collidepoint(e.pos) and self.rt["wild"]:
                        self._rt_run()
                    else:  # a tap on the map: walk there (the fight goes on)
                        to = self._tile_at(e.pos)
                        if self.run.floor.walkable(*to):
                            self.walk_goal = to
                elif e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        self._rt_use(e.key - pygame.K_1)
                    elif e.key in self.KEYS:
                        self.walk_goal = None
                        self._rt_step(*self.KEYS[e.key])
                    elif e.key == pygame.K_m:
                        self._rt_mega()
                    elif e.key in (pygame.K_ESCAPE, pygame.K_r):
                        self._rt_run()

    # ---------------------------------------------------------------- drawing
    def _tile_rect(self, x, y):
        from src.states.overworld.dungeon import TILE
        cx, cy = self._camera()
        ox, oy = int(self.game.width / 2 - cx), int(self.game.height / 2 - cy)
        return pygame.Rect(ox + x * TILE, oy + y * TILE, TILE, TILE)

    def _lerp_rect(self, a, b, left, frames):
        k = 1 - left / max(1, frames)
        ra, rb = self._tile_rect(*a), self._tile_rect(*b)
        return pygame.Rect(int(ra.x + (rb.x - ra.x) * k), int(ra.y + (rb.y - ra.y) * k), ra.w, ra.h)

    def _rt_foe_rect(self):
        rt = self.rt
        return self._lerp_rect(rt["f_from"], rt["spot"], rt["f_anim"], FPS * self.FOE_STEP)

    def _rt_partner_k(self):
        """How far your Pokemon is through its step (1: there), in a real-time battle."""
        return 1 - self.rt["p_anim"] / max(1, FPS * self.PARTNER_STEP)

    def _rt_partner_rect(self):
        return self._lerp_rect(self.partner_from, self.partner, self.rt["p_anim"], FPS * self.PARTNER_STEP)

    def _hp_bar(self, screen, poke, rect, mine):
        w = 64
        bar = pygame.Rect(0, 0, w, 10)
        bar.midbottom = (rect.centerx, rect.top - 30)
        if mine:  # (yours under your Pokemon, the foe's over it: they never overlap)
            bar.midtop = (rect.centerx, rect.bottom + 14)
        pygame.draw.rect(screen, (20, 20, 30), bar.inflate(4, 4), border_radius=4)
        k = poke.current_hp / max(1, poke.get_max_hp())
        col = (90, 220, 110) if k > 0.5 else (240, 200, 60) if k > 0.2 else (230, 70, 60)
        pygame.draw.rect(screen, col, (bar.x, bar.y, int(w * k), bar.h), border_radius=3)
        tag = self.game.assets.fonts["caption"].render(f"Lv{poke.level}", True, (255, 255, 255))
        screen.blit(tag, tag.get_rect(midtop=(bar.centerx, bar.bottom + 2)) if mine else tag.get_rect(midbottom=(bar.centerx, bar.y - 2)))
        if mine:
            pygame.draw.rect(screen, (120, 200, 255), bar.inflate(4, 4), 2, border_radius=4)

    def _rt_draw(self, screen):
        from src.states.overworld.dungeon import TILE
        rt = self.rt
        if not rt or self.mode not in self.RT_MODES:
            return
        fonts = self.game.assets.fonts
        foe, me = self._foe(), self._me()
        m = rt["mover"]
        fr = self._rt_foe_rect()
        mr = self._rt_partner_rect()
        if not rt["wild"] and foe:
            if rt["throw"] > 0:  # the Poke Ball's arc from the trainer to the tile
                k = 1 - rt["throw"] / (FPS * 0.6)
                a, b = self._tile_rect(m.x, m.y).center, fr.center
                x = a[0] + (b[0] - a[0]) * k
                y = a[1] + (b[1] - a[1]) * k - math.sin(k * math.pi) * 60
                pygame.draw.circle(screen, (230, 50, 50), (int(x), int(y)), 9)
                pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y) + 3), 9, draw_top_left=False,
                                   draw_top_right=False)
                pygame.draw.circle(screen, (30, 30, 30), (int(x), int(y)), 9, 2)
            else:
                img = self._icon(foe, TILE, facing=rt["face"])
                if img is not None:
                    screen.blit(img, img.get_rect(midbottom=(fr.centerx, fr.bottom + 4)))
        if foe and (rt["wild"] or rt["throw"] <= 0):  # which way it's looking (hit it from the side or back!)
            fx, fy = rt["face"]
            tip = (fr.centerx + fx * (TILE // 2 + 4), fr.centery + 6 + fy * (TILE // 2 + 4))
            pygame.draw.circle(screen, (255, 255, 255), tip, 5)
            pygame.draw.circle(screen, (200, 40, 40), tip, 5, 2)
        shot = rt.get("shot")
        if shot:  # the attack's quick animation
            a, b = (mr.center, fr.center) if shot["from"] == "me" else (fr.center, mr.center)
            k = shot["t"] / max(1, shot["dur"])
            col = TYPE_COLOR.get(shot["kind"], (255, 255, 255))
            if shot["physical"]:
                x, y = a[0] + (b[0] - a[0]) * min(1, k * 1.2), a[1] + (b[1] - a[1]) * min(1, k * 1.2)
                pygame.draw.line(screen, col, a, (int(x), int(y)), 6)
            else:
                for j in range(4):
                    kk = max(0, k - j * 0.06)
                    x, y = a[0] + (b[0] - a[0]) * kk, a[1] + (b[1] - a[1]) * kk
                    pygame.draw.circle(screen, col, (int(x), int(y)), 10 - j * 2)
                pygame.draw.circle(screen, (255, 255, 255), (int(a[0] + (b[0] - a[0]) * k), int(a[1] + (b[1] - a[1]) * k)), 4)
            if k > 0.75:
                pygame.draw.circle(screen, col, b, int(10 + (k - 0.75) * 120), 3)
        if foe and (rt["wild"] or rt["throw"] <= 0):
            self._hp_bar(screen, foe, fr, False)
        if me:
            self._hp_bar(screen, me, mr, True)
        for f in rt["fx"]:
            r = fr if f["who"] == "foe" else mr
            lift = int((FPS * 0.9 - f["t"]) * 2)
            if f.get("kind") and f["t"] > FPS * 0.75:  # the blow: a quick, small flash of its type's colour
                rad = int(TILE * 0.4)
                s = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*TYPE_COLOR.get(f["kind"], (255, 255, 255)), 110), (rad, rad), rad)
                screen.blit(s, s.get_rect(center=r.center))
            theme.shadow_text(screen, f["text"], fonts["label"], r.centerx, r.top - 50 - lift, color=f["color"],
                              shadow=(20, 20, 30), align="center")
        if self.mode == "RTCATCH":  # the catch window
            W, H = self.game.width, self.game.height
            q = pygame.Rect(0, 0, 560, 80)
            q.center = (W // 2, int(H * 0.56))
            theme.draw_textbox(screen, q)
            name = rt["foes"][0].display_name.upper()
            theme.shadow_text(screen, f"{name} is down! Catch it?", fonts["label"], q.centerx, q.centery, align="center")
            throw_r, go_r = self._rt_catch_rects()
            mouse = pygame.mouse.get_pos()
            theme.command_button(screen, throw_r, "THROW A BALL", fonts["label"],
                                 theme.POKEMON if self._can_catch() else theme.BACK, hover=throw_r.collidepoint(mouse))
            theme.command_button(screen, go_r, "LET IT GO", fonts["label"], theme.RUN, hover=go_r.collidepoint(mouse))
        elif self.mode == "RT" and not self.dialogue_box.visible:
            moves_r, run_r = self._rt_rects()
            mouse = pygame.mouse.get_pos()
            names = self._my_moves(me) if me else []
            for i, r in enumerate(moves_r):
                if i >= len(names):
                    continue
                info = move_info(self.game, names[i])
                col = TYPE_COLOR.get(str(info.get("type") or "NORMAL").upper(), (160, 160, 160))
                ready = rt["cd"][i] <= 0
                far = bool(info.get("power")) and self._dist(self.partner, rt["spot"]) > self.REACH
                theme.command_button(screen, r, names[i].replace("-", " "), fonts["caption"],
                                     (110, 110, 120) if far else col,
                                     hover=ready and not far and r.collidepoint(mouse), small=fonts["small"],
                                     sub="too far" if far else (f"power {info.get('power')}" if info.get("power") else "focus"))
                if not ready:  # recharging: a dark cover draining away
                    full = self._cooldown(names[i], me) if me else 1
                    left = rt["cd"][i] / max(1, full)
                    cover = pygame.Surface((r.w, max(1, int(r.h * left))), pygame.SRCALPHA)
                    cover.fill((10, 10, 20, 170))
                    screen.blit(cover, (r.x, r.bottom - cover.get_height()))
                    theme.shadow_text(screen, f"{rt['cd'][i] / FPS:.1f}", fonts["label"], r.right - 30, r.y + 8,
                                      color=(255, 255, 255), shadow=(0, 0, 0))
                elif rt["busy"] > 0 or rt["throw"] > 0:
                    pygame.draw.rect(screen, (255, 255, 255), r, 2, border_radius=12)
            if rt["wild"]:
                theme.command_button(screen, run_r, "RUN", fonts["caption"], theme.RUN, hover=run_r.collidepoint(mouse))
            self._draw_rt_mega(screen, fonts, mouse)

    def _draw_rt_mega(self, screen, fonts, mouse):
        """The MEGA button: ready, the minute counting down, or the Key Stone resting."""
        r = self._rt_mega_rect()
        m = mega_clock.state(self.game)
        if mega_clock.active(self.game):
            secs = (m["left"] + FPS - 1) // FPS
            theme.command_button(screen, r, f"MEGA {secs}s", fonts["caption"], (200, 70, 160), hover=False)
            k = m["left"] / (mega_clock.SECONDS * FPS)
            pygame.draw.rect(screen, (255, 200, 240), (r.x + 8, r.bottom - 10, int((r.w - 16) * k), 5), border_radius=2)
        elif mega_clock.cooling(self.game):
            secs = (m["cool"] + FPS - 1) // FPS
            theme.command_button(screen, r, f"MEGA in {secs}s", fonts["caption"], (110, 110, 120), hover=False)
        elif self._rt_mega_option():
            theme.command_button(screen, r, "MEGA", fonts["caption"], (220, 80, 180), hover=r.collidepoint(mouse))
