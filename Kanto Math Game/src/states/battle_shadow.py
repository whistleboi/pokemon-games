"""Shadow Pokemon in battle (Orre; src/world/shadow.py has the rules): snagging a trainer's Shadow Pokemon with the
Snag Machine (Jordan's Q6: the machine's arm glows, the Snag Ball's dark throw), Hyper Mode and CALL (Q7).

A mixin on TrainerBattleState (singles) that DoubleBattleState inherits. Wild battles keep their own catching.
Hooks in battle.py / battle_double.py: resolve_turn -> _shadow_turn(); handle_run -> _shadow_call(); setup_action_menu
-> _shadow_menu(); trigger_outro (a win) -> _shadow_after(); update -> _snag_update(); draw -> _snag_draw();
the foe's sprite hides while it is drawn into the ball (_snag_hides)."""
import math
import random

import pygame

from src.world import shadow
from src.pokemon import catching

GLOW, THROW, ABSORB, DROP, SHAKE, DONE = "GLOW", "THROW", "ABSORB", "DROP", "SHAKE", "DONE"
FRAMES = {GLOW: 26, THROW: 22, ABSORB: 16, DROP: 16}
SNAG_PURPLE = (150, 60, 210)


class ShadowBattle:
    # ------------------------------------------------------------ CALL and Hyper Mode
    def _shadow_menu(self):
        """CALL stands in for RUN in a trainer battle while a Shadow Pokemon of yours is out."""
        mon = self.player_pokemon
        if self.trainer_class != "WILD" and getattr(mon, "shadow", None) and getattr(self, "action_menu", None):
            for b in self.action_menu.buttons:
                if b.text == "RUN":
                    b.text = "CALL"

    def _shadow_call(self):
        """RUN pressed: in a trainer battle with your Shadow Pokemon out, it's CALL (True: handled)."""
        mon = self.player_pokemon
        if self.trainer_class == "WILD" or not getattr(mon, "shadow", None):
            return False
        lines = shadow.call(self.game, mon)
        self.show_message(lines, callback=self.on_item_used)   # (the call takes its turn)
        return True

    def _shadow_turn(self):
        """Your Pokemon's action is in: a Shadow one may go into Hyper Mode and ignore you."""
        mon = self.player_pokemon
        fought = self.__dict__.setdefault("_shadow_fought", [])
        if mon is not None and all(m is not mon for m in fought):
            fought.append(mon)
        if not getattr(mon, "shadow", None):
            return
        lines = shadow.maybe_hyper(self.game, mon)
        over = shadow.hyper_override(mon)
        if over and over != getattr(self, "chosen_move", None):
            self.chosen_move = over
            lines.append(f"{mon.display_name.upper()} is in Hyper Mode! It ignored your order!")
        if lines:
            self._form_msgs.extend(lines)

    def _shadow_after(self):
        """A won battle: the Shadow Pokemon that fought open their hearts a little (lines to add)."""
        from src.world import miror_radar   # (Shadow Pokemon beaten unsnagged go to Miror B. once you hold his radar: XD's way)
        for m in list(getattr(self, "opponent_team", None) or []):
            if m is not None and shadow.is_shadow(self.game, m):
                miror_radar.miss(self.game, m)
        return shadow.after_battle(self.game, self.game.story_manager.player_team, self.__dict__.get("_shadow_fought", []))

    # ------------------------------------------------------------ snagging
    def _snag_target(self):
        foes = self.battlers("opponent") if getattr(self, "is_doubles", False) else [self.opponent_pokemon]
        return next((m for m in foes if m is not None and m.current_hp > 0 and shadow.is_shadow(self.game, m)), None)

    def throw_from_bag(self):
        """A Ball from the Bag in a trainer battle: with the Snag Machine, at a Shadow Pokemon, it's a snag; anything
        else the trainer blocks (the ball isn't lost)."""
        story = self.game.story_manager
        ball = catching.selected(story)
        target = self._snag_target()
        if target is None or not shadow.can_snag(self.game, target):
            self.show_message(["The trainer blocked the Ball!", "Don't be a thief!"], callback=self.return_to_menu)
            return
        catching.use(story, ball)
        ok, shakes, crit = catching.throw(self.game, target, ball, hp=max(1, target.current_hp), max_hp=target.get_max_hp(),
                                          turn=max(1, self.turn_count))   # (its disc snag rate: catching.catch_rate)
        img = self.game.assets.get_item_image(ball if ball != catching.POKE else "POKE_BALL")
        img = pygame.transform.smoothscale(img, (52, 52)) if img else pygame.transform.smoothscale(self.game.assets.ball_imgs[0], (52, 52))
        spot = self._snag_spot(target)
        self._snag = {"phase": GLOW, "t": 0, "target": target, "ok": ok, "shakes": 0 if crit else shakes,
                      "img": img, "start": (self.game.width * 0.16, self.game.height * 0.62), "spot": spot,
                      "ground": spot[1] + 40, "pos": None, "angle": 0, "hidden": False}
        self._snag_return = self.phase
        self.phase = "SNAG"
        if self.math_ui:
            self.math_ui.set_visibility(False)
        self.action_menu.set_visibility(False)
        self.dialogue_box.reset([f"{self.game.player_name} threw a {catching.label(ball)}!", "The Snag Machine glows!"])
        self.dialogue_box.set_visibility(True)

    def _snag_spot(self, mon):
        try:
            if getattr(self, "is_doubles", False):
                return self._spot(mon)
            from src.vfx.animations import battle_spot
            return battle_spot(self.game, mon, "opponent")
        except Exception:
            return (self.game.width * 0.7, self.game.height * 0.38)

    def _snag_hides(self, mon=None):
        s = getattr(self, "_snag", None)
        return bool(s and s["hidden"] and (mon is None or mon is s["target"]))

    def _snag_update(self):
        """One frame of the snag (True while it plays)."""
        s = getattr(self, "_snag", None)
        if self.phase != "SNAG" or not s:
            return False
        if self.dialogue_box.visible and not self.dialogue_box.is_finished:
            self.dialogue_box.update()
        s["t"] += 1
        ph, t = s["phase"], s["t"]
        if ph in FRAMES and t >= FRAMES[ph]:
            s["t"] = 0
            s["phase"] = {GLOW: THROW, THROW: ABSORB, ABSORB: DROP, DROP: SHAKE}[ph]
            if s["phase"] == ABSORB:
                s["hidden"] = True
            if s["phase"] == SHAKE:
                s["left"] = 30 * max(1, min(3, s["shakes"])) + 18 if not s["ok"] else 30 * 3 + 18
        elif ph == SHAKE:
            s["left"] -= 1
            if s["left"] <= 0:
                s["phase"] = DONE
                self._snag_result()
        return True

    def _snag_result(self):
        s = self._snag
        mon = s["target"]
        if not s["ok"]:
            s["hidden"] = False
            self._snag = None
            lines = [("Oh no! It broke free!", "Aww! It appeared to be caught!", "Aargh! Almost had it!",
                      "Gah! It was so close, too!")[min(3, s["shakes"])]]
            self.phase = self._snag_return if self._snag_return != "SNAG" else "MENU"
            self.show_message(lines, callback=self.on_item_used)
            return
        lines = shadow.receive_snagged(self.game, mon)
        self._snag = None
        self._remove_snagged(mon)
        self.show_message(lines, callback=self._after_snag)

    def _remove_snagged(self, mon):
        """It leaves its trainer's team (no faint, no Exp.)."""
        mon_team = self.opponent_team
        if getattr(self, "is_doubles", False):
            for k, m in enumerate(self.o_slots):
                if m is mon:
                    self.o_slots[k] = None
            self._d_down.add(id(mon))
        idx = next((i for i, m in enumerate(mon_team) if m is mon), None)
        if idx is not None:
            mon_team.pop(idx)
            if not getattr(self, "is_doubles", False) and idx <= self.current_opponent_idx:
                self.current_opponent_idx -= 1

    def _after_snag(self):
        """Its trainer sends out the next, or the battle is won."""
        if getattr(self, "is_doubles", False):
            mon = self.player_pokemon
            self._plans[id(mon)] = {"kind": "item", "mon": mon}
            if not any(p is not None and p.current_hp > 0 for p in self.opponent_team):
                self.show_trainer, self.trainer_slide_offset = True, 0
                return self.trigger_outro(win=True)
            if not self.battlers("opponent"):   # (both of theirs out of the fight: the turn ends, its replacements come in
                self.turn_actions = []           #  through the turn's own end, then your next turn - 11-21: snagging both of a
                self._turn_end_done = True       #  pair left "sent out" on screen with nothing after it, Greevil's doubles)
                self.phase = "D_RESOLVE"
                self._replace_fainted()
                return
            self._plan_done()
            return
        if self.current_opponent_idx + 1 < len(self.opponent_team):
            self.opponent_hp = 0
            self.phase = "TRAINER_SLIDE_IN"
            self.trainer_slide_offset = 300
            self.show_trainer = True
        else:
            self.trigger_outro(win=True)

    def _snag_draw(self, screen):
        s = getattr(self, "_snag", None)
        if self.phase != "SNAG" or not s:
            return
        ph, t = s["phase"], s["t"]
        sx, sy = s["start"]
        tx, ty = s["spot"]
        if ph == GLOW:   # the Snag Machine's arm lights up: rings pulse out from your side
            k = t / FRAMES[GLOW]
            for i in range(3):
                r = int(20 + 60 * ((k + i / 3) % 1.0))
                a = int(200 * (1 - (k + i / 3) % 1.0))
                ring = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(ring, SNAG_PURPLE + (a,), (r + 2, r + 2), r, 5)
                screen.blit(ring, ring.get_rect(center=(int(sx), int(sy))))
            core = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(core, (230, 200, 255, int(160 + 90 * math.sin(k * math.pi * 4))), (30, 30), 14)
            screen.blit(core, core.get_rect(center=(int(sx), int(sy))))
            return
        if ph == THROW:   # the dark ball arcs over, a purple trail behind it
            k = t / FRAMES[THROW]
            pts = []
            for j in range(10):
                kk = max(0.0, k - j * 0.035)
                x = sx + (tx - sx) * kk
                y = sy + (ty - 30 - sy) * kk - 170 * 4 * kk * (1 - kk)
                pts.append((x, y))
            for j, (x, y) in enumerate(reversed(pts[1:])):
                dot = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.circle(dot, (90, 20, 140, 40 + 18 * j), (15, 15), 6 + j)
                screen.blit(dot, dot.get_rect(center=(int(x), int(y))))
            s["pos"] = pts[0]
            s["angle"] = (s["angle"] + 36) % 360
        elif ph == ABSORB:   # the Shadow Pokemon turns dark and is drawn in
            k = t / FRAMES[ABSORB]
            flash = pygame.Surface((180, 180), pygame.SRCALPHA)
            pygame.draw.circle(flash, (60, 0, 90, int(170 * (1 - k))), (90, 90), int(40 + 60 * (1 - k)))
            screen.blit(flash, flash.get_rect(center=(int(tx), int(ty))))
            s["pos"] = (tx, ty - 30)
        elif ph == DROP:
            k = t / FRAMES[DROP]
            g = s["ground"]
            y = (ty - 30) + (g - (ty - 30)) * min(1.0, k / 0.7) ** 2 if k < 0.7 else g - 22 * 4 * ((k - 0.7) / 0.3) * (1 - (k - 0.7) / 0.3)
            s["pos"], s["angle"] = (tx, y), 0
        elif ph in (SHAKE, DONE):
            left = s.get("left", 0) - 18
            s["angle"] = 22 * math.sin(((left % 30) / 30) * 2 * math.pi) if left > 0 and (left % 30) > 10 else 0
        if s["pos"] is None:
            return
        img = pygame.transform.rotate(s["img"], s["angle"]) if s["angle"] else s["img"]
        x, y = s["pos"]
        aura = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(aura, (70, 10, 110, 110), (40, 40), 34)
        screen.blit(aura, aura.get_rect(center=(int(x), int(y))))
        screen.blit(img, img.get_rect(center=(int(x), int(y))))
