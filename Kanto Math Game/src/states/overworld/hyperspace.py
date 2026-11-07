"""Hyperspace Lumiose (Jordan, 11-06): Legends: Z-A's Hyperspace as our dungeons. You get in with a donut
(src/world/donuts.py, src/states/donut.py); each zone is three big open floors with nothing in the way of the
view, trainers and wild Pokemon of its theme. Each floor has a clock (180 seconds, a Rainbow donut's 30 more):
beat everyone on it before time runs out, then the way down opens. The last floor's clear wins a Mega Stone
(Legends: Z-A's new ones, a few in each zone).

Battles happen on the map, in real time: one math question first (right: you strike first and harder), then
both sides attack as their moves come off cooldown, small HP bars over the two Pokemon. Tap a move when it's
ready. A wild one you can run from; beat a trainer's whole team. If yours all faint, or the clock runs out,
you're back at the Hyperspace hub."""
import math
import random

import pygame

from src.config import FPS
from src.pokemon import balance, moves as mv
from src.pokemon.data import Pokemon
from src.pokemon.mechanics import TypeAdvantage
from src.states.overworld.dungeon import DungeonState, TILE
from src.ui import theme
from src.world import donuts, levels

HUB = "HYPERSPACE_LUMIOSE"
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


class HyperspaceState(DungeonState):
    RT_MODES = ("RTQ", "RT")

    def __init__(self, game, restore_data=None, classic=False):
        super().__init__(game, restore_data=restore_data, classic=classic)
        self.hs = self.area_data.get("hyperspace") or {}
        story = game.story_manager
        donut = story.story_flags.pop(donuts.FLAG, None) or {}  # (eaten on the way in)
        self.bonus = int(donut.get("bonus_seconds", 0)) if donut.get("taste") == self.hs.get("taste") else 0
        self.chart = TypeAdvantage(game.loader.area_data.get("TYPE_CHART", {}))
        self.rt = None
        self._reset_clock()
        self.banner = 150

    # ---------------------------------------------------------------- the clock and the floors
    def _reset_clock(self):
        self.clock = (int(self.hs.get("seconds", 180)) + self.bonus) * FPS
        self.cleared_said = False

    def _enemies(self):
        return [m for m in self.run.floor.movers if m.kind in ("wild", "trainer")]

    def _stairs_blocked(self):
        left = len(self._enemies())
        if left:
            self.flash(f"Beat everyone on this floor first! ({left} left)")
            return True
        return False

    def _descend(self):
        super()._descend()
        self._reset_clock()

    def _collapse(self):
        self.rt, self.mode = None, "MAP"
        self.say(["The Hyperspace zone is fading away...", "You were pulled back to the Hyperspace hub!"],
                 then=lambda: self._leave(HUB))

    def _floor_check(self):
        if self.cleared_said or self._enemies() or self.dialogue_box.visible:
            return
        self.cleared_said = True
        if self.run.index < self.run.n_floors - 1:
            self.flash("Floor clear! The way down is open!", 150)
            return
        story = self.game.story_manager
        stone = next((s for s in self.hs.get("stones", []) if story.inventory.get(s, 0) <= 0), None)
        lines = [f"You cleared {self.hs.get('theme', 'the zone')}!"]
        if stone:
            story.inventory[stone] = 1
            from src.pokemon import forms
            lines.append(f"You found a {forms.item_label(stone).upper()}! A new Mega Stone!")
        else:
            story.add_item("RARE_CANDY", 3)
            lines.append("You found 3 RARE CANDY!")
        berry = self.hs.get("star_berry")
        if berry:
            story.add_item(berry, 2)
            lines.append(f"You found 2 {berry.replace('_', ' ')} too! Star berries make stronger donuts.")
        self.say(lines, then=lambda: self._leave(HUB))

    # ---------------------------------------------------------------- meeting someone: a real-time battle
    def _meet_wild(self, mover):
        self.walk_goal = None
        self.game.data.mark_seen(mover.payload.id)
        if mover.payload.cry:
            mover.payload.cry.play()
        self._rt_start(mover, [mover.payload], None)

    def _battle_trainer(self, mover):
        idx, t = mover.payload
        team = []
        for pid in t.get("team") or [25]:
            try:
                p = Pokemon(self.game.loader.fetch_specific(int(pid)), self.game.assets, size_mult=2.5)
            except Exception:
                continue
            team.append(p)
        levels.set_team(team, levels.trainer_team_levels(self.game, self.area_key, len(team)))
        self._rt_start(mover, team, (idx, t))

    def _rt_start(self, mover, foes, trainer):
        for p in foes:
            mv.ensure_moves(self.game, p)
        self.encounter = mover
        self._partner_beside(mover)
        self.rt = {"mover": mover, "foes": foes, "i": 0, "trainer": trainer, "cd": [0, 0, 0, 0], "foe_cd": FPS,
                   "power": 1.0, "fx": [], "focus": 1.0}
        play = self.game.states.get("play") or self
        self.rt_q = play.generate_math_set(0, num_options=3)
        self.mode = "RTQ"
        who = trainer[1].get("name") if trainer else f"A wild {foes[0].display_name.upper()}"
        self.flash(f"{who} wants to battle! Answer to strike first!", 120)

    def _partner_beside(self, mover):
        """Your lead Pokemon steps up beside the foe (it fights; you stand back)."""
        f = self.run.floor
        px, py = self.run.player
        spots = [(mover.x + dx, mover.y + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
        spots = [s for s in spots if s != (px, py) and f.walkable(*s) and not f.occupied(*s)]
        if spots:
            self.partner = self.partner_from = min(spots, key=lambda s: abs(s[0] - px) + abs(s[1] - py))

    def _rt_answer(self, i):
        problem, ans, opts = self.rt_q
        right = opts[i] == ans
        rt = self.rt
        if right:
            rt["power"], rt["foe_cd"] = 1.25, int(FPS * 2.2)
            self.flash("Right! You strike first, and harder!", 90)
        else:
            rt["power"], rt["foe_cd"] = 1.0, int(FPS * 0.4)
            self.flash(f"It was {ans}. Watch out!", 90)
        self.mode = "RT"

    def _me(self):
        return self.lead() if self.lead() and self.lead().current_hp > 0 else None

    def _foe(self):
        rt = self.rt
        return rt["foes"][rt["i"]] if rt and rt["i"] < len(rt["foes"]) else None

    def _my_moves(self, me):
        mv.ensure_moves(self.game, me)
        return list(me.moves or [])[:4] or ["TACKLE"]

    def _cooldown(self, name, poke):
        power = move_info(self.game, name).get("power") or 0
        speed = poke.stat_value("SPEED")
        base = 0.9 + power / 70 if power else 2.4
        return int(FPS * base * (1.3 - min(0.6, speed / 300)))

    def _hit(self, att, dfn, name, mult=1.0):
        info = move_info(self.game, name)
        power = info.get("power") or 0
        if not power:  # a status move: the next hit lands harder
            return None
        kind = str(info.get("type") or "NORMAL").upper()
        special = str(info.get("category") or "").upper() == "SPECIAL"
        attack = att.stat_value("SPATK" if special else "ATTACK")
        defense = dfn.stat_value("SPDEF" if special else "DEFENSE")
        eff = self.chart.get_multiplier(kind, dfn.types or [])
        if eff == 0:
            return 0, eff, kind
        dmg, _crit = balance.damage(att.level, power, attack, defense, stab=kind in (att.types or []),
                                    effectiveness=eff)
        dmg = max(1, int(dmg * mult))
        dfn.current_hp = max(0, dfn.current_hp - dmg)
        return dmg, eff, kind

    def _fx(self, who, text, color, kind=None):
        self.rt["fx"].append({"who": who, "text": text, "color": color, "t": int(FPS * 0.9), "kind": kind})

    def _rt_use(self, k):
        me, foe = self._me(), self._foe()
        rt = self.rt
        if not me or not foe or rt["cd"][k] > 0:
            return
        moves = self._my_moves(me)
        if k >= len(moves):
            return
        name = moves[k]
        rt["cd"][k] = self._cooldown(name, me)
        got = self._hit(me, foe, name, rt["power"] * rt["focus"])
        if got is None:
            rt["focus"] = 1.5
            self._fx("me", "Focused!", (255, 230, 120))
            return
        rt["focus"] = 1.0
        dmg, eff, kind = got
        self._fx("foe", f"-{dmg}" if dmg else "No effect", (255, 255, 255), kind)
        if eff > 1:
            self._fx("foe", "Super effective!", (255, 220, 90))
        elif 0 < eff < 1:
            self._fx("foe", "Not very effective", (200, 200, 210))

    def _rt_foe_turn(self):
        me, foe = self._me(), self._foe()
        moves = [m for m in (foe.moves or []) if (move_info(self.game, m).get("power") or 0) > 0] or ["TACKLE"]
        name = random.choice(moves)
        self.rt["foe_cd"] = int(self._cooldown(name, foe) * random.uniform(1.0, 1.4))
        got = self._hit(foe, me, name)
        if got:
            dmg, eff, kind = got
            self._fx("me", f"-{dmg}", (255, 120, 110), kind)

    def _rt_update(self):
        rt = self.rt
        for f in rt["fx"]:
            f["t"] -= 1
        rt["fx"] = [f for f in rt["fx"] if f["t"] > 0]
        if self.mode != "RT":
            return
        me, foe = self._me(), self._foe()
        if me is None:
            team = self.game.story_manager.player_team
            if not any(p and p.current_hp > 0 for p in team):
                self.rt, self.mode = None, "MAP"
                self.say(["Your Pokemon are too tired to go on!", "You hurried back to the Hyperspace hub."],
                         then=lambda: self._leave(HUB))
            return
        if foe is None:
            return self._rt_won()
        if foe.current_hp <= 0:
            story = self.game.story_manager
            gain = Pokemon.battle_xp(me.level, foe.level, trainer=bool(rt["trainer"]))
            me.gain_xp(gain, levels.xp_cap(story))
            self._fx("me", f"+{gain} XP", (140, 230, 140))
            rt["i"] += 1
            rt["foe_cd"] = int(FPS * 1.2)
            if self._foe() is None:
                return self._rt_won()
            self.flash(f"{rt['trainer'][1].get('name')} sent out {self._foe().display_name.upper()}!", 90)
            return
        rt["cd"] = [max(0, c - 1) for c in rt["cd"]]
        rt["foe_cd"] -= 1
        if rt["foe_cd"] <= 0:
            self._rt_foe_turn()
            if me.current_hp <= 0:
                self.flash(f"{me.display_name.upper()} fainted!", 90)
                rt["cd"] = [0, 0, 0, 0]

    def _rt_won(self):
        rt = self.rt
        mover = rt["mover"]
        story = self.game.story_manager
        if mover in self.run.floor.movers:
            self.run.floor.movers.remove(mover)
        if rt["trainer"]:
            story.mark_trainer_defeated(self.area_key, rt["trainer"][0])
            story.money += 300
            self.flash(f"You beat {rt['trainer'][1].get('name')}! (+$300)", 120)
        else:
            self.flash(f"The wild {rt['foes'][0].display_name.upper()} fainted!", 90)
        self.rt, self.mode, self.encounter = None, "MAP", None

    def _rt_run(self):
        rt = self.rt
        if not rt or rt["trainer"]:
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

    # ---------------------------------------------------------------- the loop
    def update(self):
        super().update()
        if self.dialogue_box.visible:
            return
        if self.mode in ("MAP", "RT", "RTQ", "SPOTTED"):
            self.clock -= 1
            if self.clock <= 0:
                return self._collapse()
        if self.mode in self.RT_MODES and self.rt:
            self._rt_update()
        elif self.mode == "MAP":
            self._floor_check()

    # the battle's buttons
    def _rt_rects(self):
        W, H = self.game.width, self.game.height
        bw, bh, gap = 250, 74, 14
        x0 = W // 2 - (4 * bw + 3 * gap) // 2
        return [pygame.Rect(x0 + i * (bw + gap), H - bh - 18, bw, bh) for i in range(4)], \
            pygame.Rect(W - 170, H - bh - 110, 150, 60)

    def handle_events(self, events):
        if self.mode not in self.RT_MODES or self.dialogue_box.visible:
            return super().handle_events(events)
        for e in events:
            if self.mode == "RTQ":
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

    def draw(self):
        super().draw()
        screen = self.game.screen
        fonts = self.game.assets.fonts
        rt = self.rt
        if rt and self.mode in self.RT_MODES:
            foe, me = self._foe(), self._me()
            m = rt["mover"]
            fr = self._tile_rect(m.x, m.y)
            mr = self._tile_rect(*self.partner) if self.partner != self.run.player else self._tile_rect(*self.run.player)
            if foe:
                self._hp_bar(screen, foe, fr, False)
            if me:
                self._hp_bar(screen, me, mr, True)
            for f in rt["fx"]:
                r = fr if f["who"] == "foe" else mr
                lift = int((FPS * 0.9 - f["t"]) * 2)
                if f.get("kind") and f["t"] > FPS * 0.6:  # the blow: a burst of its type's colour
                    rad = int(TILE * 0.6 * (1 + (FPS * 0.9 - f["t"]) / FPS))
                    s = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (*TYPE_COLOR.get(f["kind"], (255, 255, 255)), 150), (rad, rad), rad)
                    screen.blit(s, s.get_rect(center=r.center))
                theme.shadow_text(screen, f["text"], fonts["label"], r.centerx, r.top - 50 - lift, color=f["color"],
                                  shadow=(20, 20, 30), align="center")
        if self.mode == "RTQ" and rt:
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
        elif self.mode == "RT" and rt:
            me = self._me()
            moves_r, run_r = self._rt_rects()
            mouse = pygame.mouse.get_pos()
            names = self._my_moves(me) if me else []
            for i, r in enumerate(moves_r):
                if i >= len(names):
                    continue
                info = move_info(self.game, names[i])
                col = TYPE_COLOR.get(str(info.get("type") or "NORMAL").upper(), (160, 160, 160))
                ready = rt["cd"][i] <= 0
                theme.command_button(screen, r, names[i].replace("-", " "), fonts["caption"], col if ready else theme.BACK,
                                     hover=ready and r.collidepoint(mouse), small=fonts["small"],
                                     sub=(f"power {info.get('power')}" if info.get("power") else "focus") if ready else "...")
                if not ready:  # the cooldown filling back up
                    full = self._cooldown(names[i], me) if me else 1
                    k = 1 - rt["cd"][i] / max(1, full)
                    pygame.draw.rect(screen, (255, 255, 255), (r.x + 8, r.bottom - 10, int((r.w - 16) * k), 5), border_radius=3)
            if not rt["trainer"]:
                theme.command_button(screen, run_r, "RUN", fonts["caption"], theme.RUN, hover=run_r.collidepoint(mouse))

    def _draw_hud(self, screen):
        super()._draw_hud(screen)
        if not hasattr(self, "clock"):
            return
        fonts = self.game.assets.fonts
        secs = max(0, self.clock // FPS)
        text = f"TIME {secs // 60}:{secs % 60:02d}   LEFT {len(self._enemies())}"
        t = fonts["label"].render(text, True, (255, 255, 255))
        pill = t.get_rect(topleft=(24, 128)).inflate(26, 10)  # (under MENU: clear of the messages)
        hurry = secs <= 30 and (pygame.time.get_ticks() // 300) % 2
        pygame.draw.rect(screen, (150, 30, 40) if hurry else (40, 24, 70), pill, border_radius=10)
        pygame.draw.rect(screen, (200, 120, 255), pill, 2, border_radius=10)
        screen.blit(t, t.get_rect(center=pill.center))
