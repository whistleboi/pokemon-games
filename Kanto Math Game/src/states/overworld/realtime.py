"""Real-time battles on the walked maps (Jordan, 11-06), Legends: Z-A's way: Options > BATTLES: REAL-TIME
(every walked route), and always in Hyperspace Lumiose. Max Raids stay traditional.

The battle is the traditional one, one for one: the same TrainerBattleState / WildBattleState is made
(its Pokemon, their levels, its rewards) but not shown. A trainer's intro lines come first in the map's text
box (no intro animation); then one math question (right: you strike first and harder), then both sides
attack in real time: each move recharges on its own (stronger moves take longer), a short pause after every
attack, a quick animation (an orb of the move's type's colour, or a lunge), small HP bars over the two
Pokemon. A trainer throws its Pokemon out onto the tile in front of it, one after another. Each knock-out
gives the battle's own XP (_award_battle_xp: Exp. Share, the level cap, new moves); a win the battle's own
rewards and story steps (its victory text, then exit_battle), and back on the map as after any battle."""
import math
import random

import pygame

from src.config import FPS
from src.pokemon import balance, moves as mv
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
    RT_MODES = ("RTQ", "RT", "RTCATCH")
    PAUSE = 0.8   # seconds after any attack before the next (breathing room)
    SHOT = 0.35   # the attack's quick animation
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
            fn()
        finally:
            self.game.change_state = orig
        return caught[-1] if caught else None

    def _rt_wild(self, mover):
        from src.states.battle import WildBattleState
        self.walk_goal = None
        self.rounds_completed += 1
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
        self.rt = {"mover": mover, "battle": battle, "foes": foes, "i": 0, "wild": wild, "cd": [0, 0, 0, 0],
                   "foe_cd": FPS, "power": 1.0, "fx": [], "focus": 1.0, "spot": spot, "busy": 0, "shot": None,
                   "throw": 0 if wild else int(FPS * 0.6), "fought": []}
        play = self.game.states.get("play") or self
        self.rt_q = play.generate_math_set(0, num_options=3)
        self.mode = "RTQ"
        who = f"A wild {foes[0].display_name.upper()}" if wild else (battle.trainer_name or "The trainer")
        self.flash(f"{who}! Answer to strike first!", 120)

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

    def _rt_answer(self, i):
        problem, ans, opts = self.rt_q
        rt = self.rt
        if opts[i] == ans:
            rt["power"], rt["foe_cd"] = 1.25, int(FPS * 2.2)
            self.flash("Right! You strike first, and harder!", 90)
        else:
            rt["power"], rt["foe_cd"] = 1.0, int(FPS * 0.4)
            self.flash(f"It was {ans}. Watch out!", 90)
        self.mode = "RT"

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
        rt["cd"][k] = self._cooldown(name, me)
        if not any(p is me for p in rt["fought"]):
            rt["fought"].append(me)
        if not info.get("power"):  # a status move: the next hit lands harder
            rt["focus"] = 1.5
            rt["busy"] = int(FPS * self.PAUSE)
            self._fx("me", "Focused!", (255, 230, 120))
            return

        def land():
            got = self._hit(me, foe, name, rt["power"] * rt["focus"])
            rt["focus"] = 1.0
            dmg, eff, kind = got
            self._fx("foe", f"-{dmg}" if dmg else "No effect", (255, 255, 255), kind)
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
            self.mode = "RTCATCH"
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
        self.rt, self.mode = None, "MAP"
        self.pending = ("wild" if rt["wild"] else "trainer", mover)
        b.player_won = True
        lines = []
        if not rt["wild"]:
            won = (getattr(b, "custom_dialogue", None) or {}).get("player_won")
            lines += won if isinstance(won, list) else ([won] if won else [f"You beat {b.trainer_name}!"])
            try:
                b.phase = "VICTORY_TEXT"
                b.advance_victory_sequence()  # (it lists the rewards in its text box)
                lines += list(b.dialogue_box.text_lines or [])
            except Exception as e:
                print("Real-time rewards text failed:", e)
        else:
            lines.append(f"The wild {rt['foes'][0].display_name.upper()} fainted!")
        self.say(lines, then=b.exit_battle)

    def _rt_lost(self):
        rt = self.rt
        b = rt["battle"]
        self.rt, self.mode = None, "MAP"
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
        self.rt, self.mode, self.encounter = None, "MAP", None

    # ---------------------------------------------------------------- input
    def _rt_rects(self):
        W, H = self.game.width, self.game.height
        bw, bh, gap = 250, 74, 14
        x0 = W // 2 - (4 * bw + 3 * gap) // 2
        return [pygame.Rect(x0 + i * (bw + gap), H - bh - 18, bw, bh) for i in range(4)], \
            pygame.Rect(W - 170, H - bh - 110, 150, 60)

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
            elif self.mode == "RTQ":
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, r in enumerate(self._answer_rects()):
                        if r.collidepoint(e.pos):
                            self._rt_answer(i)
                            break
                elif e.type == pygame.KEYDOWN and e.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    self._rt_answer(e.key - pygame.K_1)
            elif self.mode == "RT":
                moves, run = self._rt_rects()
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for i, r in enumerate(moves):
                        if r.collidepoint(e.pos):
                            self._rt_use(i)
                    if run.collidepoint(e.pos):
                        self._rt_run()
                elif e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        self._rt_use(e.key - pygame.K_1)
                    elif e.key in (pygame.K_ESCAPE, pygame.K_r):
                        self._rt_run()

    # ---------------------------------------------------------------- drawing
    def _tile_rect(self, x, y):
        from src.states.overworld.dungeon import TILE
        cx, cy = self._camera()
        ox, oy = int(self.game.width / 2 - cx), int(self.game.height / 2 - cy)
        return pygame.Rect(ox + x * TILE, oy + y * TILE, TILE, TILE)

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
        fr = self._tile_rect(*rt["spot"])
        mr = self._tile_rect(*self.partner) if self.partner != self.run.player else self._tile_rect(*self.run.player)
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
                face = (mr.centerx - fr.centerx, mr.centery - fr.centery)
                face = ((1 if face[0] > 0 else -1), 0) if abs(face[0]) >= abs(face[1]) else (0, 1 if face[1] > 0 else -1)
                img = self._icon(foe, TILE, facing=face)
                if img is not None:
                    screen.blit(img, img.get_rect(midbottom=(fr.centerx, fr.bottom + 4)))
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
        elif self.mode == "RTQ":
            problem, ans, opts = self.rt_q
            W, H = self.game.width, self.game.height
            q = pygame.Rect(0, 0, max(380, fonts["big"].size(problem)[0] + 120), 92)
            q.center = (W // 2, int(H * 0.58))
            theme.draw_textbox(screen, q)
            theme.math_text(screen, problem, fonts["big"], q.centerx, q.centery)
            mouse = pygame.mouse.get_pos()
            for i, r in enumerate(self._answer_rects()):
                theme.card(screen, r, hover=r.collidepoint(mouse), accent=theme.RUN)
                theme.answer_text(screen, opts[i], fonts["num"], r.centerx, r.centery)
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
                theme.command_button(screen, r, names[i].replace("-", " "), fonts["caption"], col,
                                     hover=ready and r.collidepoint(mouse), small=fonts["small"],
                                     sub=(f"power {info.get('power')}" if info.get("power") else "focus"))
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
