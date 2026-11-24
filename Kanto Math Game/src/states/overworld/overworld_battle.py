"""Battle styles on the walked maps (Jordan, 11-07): Options > BATTLE STYLE: CLASSIC or OVERWORLD.

Every battle is the same turn-based battle with a math question each turn; the style only changes how a
trainer battle looks. OVERWORLD: the trainer's lines come in the map's text box, then the battle is drawn
right on the map (the trainer's Pokemon in front of it, yours beside it, small HP bars over them, a quick
orb of the move's type's colour for each attack). The battle's buttons and math questions are the classic
ones. A wild Pokemon met on a walked map is fought there in OVERWORLD style too (dungeon._battle_wild); a wild double
(dark grass, a partner) or a horde uses the classic screen.

Also on the map (either style): MEGA, when the Pokemon following you can Mega Evolve (as in Legends: Z-A).
It stays a Mega for a minute of walking (src/pokemon/mega_clock.py; the minute waits during battles) and
goes into battles that way. POKEMON (or Tab): your party in a list above the button; tap one to have it
follow you, right-click it (or tap its potion) to heal it with your strongest potion (a Revive if it's
fainted)."""
import contextlib

import pygame

from src.config import FPS
from src.pokemon import forms, mega_clock
from src.ui import theme

TYPE_COLOR = {"NORMAL": (168, 168, 120), "FIRE": (240, 128, 48), "WATER": (104, 144, 240), "GRASS": (120, 200, 80),
              "ELECTRIC": (248, 208, 48), "ICE": (152, 216, 216), "FIGHTING": (192, 48, 40), "POISON": (160, 64, 160),
              "GROUND": (224, 192, 104), "FLYING": (168, 144, 240), "PSYCHIC": (248, 88, 136), "BUG": (168, 184, 32),
              "ROCK": (184, 160, 56), "GHOST": (112, 88, 152), "DRAGON": (112, 56, 248), "DARK": (112, 88, 72),
              "STEEL": (184, 184, 208), "FAIRY": (238, 153, 172)}


class OverworldBattles:
    # ---------------------------------------------------------------- the style
    def _ow_on(self):
        story = self.game.story_manager
        return getattr(story, "battle_style", "") == "OVERWORLD" and not getattr(self, "contest", None)

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
        """While the battle is made: the buttons it adds don't stay on the map's screen (it adds them again
        when it starts)."""
        ui = self.game.ui_manager

        @contextlib.contextmanager
        def kept():
            before = list(ui.elements)
            try:
                yield
            finally:
                ui.elements[:] = [e for e in ui.elements if e in before]
        return kept()

    def _ow_trainer(self, mover):
        """The route's own trainer battle (made as the classic one is), its intro lines in the map's text
        box, then the battle, drawn on the map."""
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

        def start():
            battle.overworld = OverworldView(self, mover)
            self.game.change_state(battle)
        self.say(lines or [f"{name} wants to battle!"], then=lambda: self.ow_walk_to_battle(mover, True, start))

    # ---------------------------------------------------------------- walking over to where the battle stands (Jordan 11-24)
    def ow_walk_to_battle(self, mover, trainer, then):
        """When the battle stands somewhere else (OverworldView._plan: side by side on open ground nearby), you and the
        foe walk there first, then(): the battle. Where you met is remembered: dungeon._back_from_battle walks you back."""
        plan = OverworldView._plan(self, mover, trainer)
        if not plan:
            return then()
        anchor, d, line = plan
        me = line[-1]
        if anchor == (mover.x, mover.y) and me == tuple(self.run.player):
            return then()
        self._ow_home = {"player": tuple(self.run.player), "facing": tuple(getattr(self, "facing", (0, 1))),
                         "mover": mover, "at": (mover.x, mover.y), "mover_facing": tuple(mover.facing or (0, 1))}
        self._ow_walk_start([(mover, anchor), ("me", me)], then, face=(mover, d))

    def _ow_walk_start(self, goals, then, face=None):
        """Walk everyone in goals [(mover or "me", tile)] there along the ground (anyone with no way, put there), then
        face: (mover, its way) - you face it back - and then()."""
        from src.dungeon import npc
        f = self.run.floor
        walkers = {id(w) for w, _ in goals if w != "me"}

        def ok(t, who):
            if not f.walkable(*t):
                return False
            m = f.mover_at(*t)
            return m is None or id(m) in walkers or m is who

        walk = {"movers": [], "me": [], "then": then, "face": face, "t": 0}
        for who, goal in goals:
            start = tuple(self.run.player) if who == "me" else (who.x, who.y)
            mo = npc.Motion(start)
            if goal != start and not mo.walk(goal, lambda t, who=who: ok(t, who) and t != tuple(self.run.player) or t == goal, beside=False):
                mo.path = []
            path = mo.path if mo.path and mo.path[-1] == goal else []
            if who == "me":
                walk["me"] = path or ([] if goal == start else None)
                walk["me_goal"] = goal
            else:
                had = getattr(who, "motion", None)
                if had is not None:
                    mo.facing = had.facing
                walk["movers"].append((who, mo, had, goal))
                mo.path = list(path)
                if not path and goal != start:   # (no way there: put there)
                    who.x, who.y = goal
                    mo.pos = mo.frm = goal
                who.motion = mo
        if walk["me"] is None:   # (no way for you: put there)
            self.run.player = self.anim_from = walk["me_goal"]
            walk["me"] = []
        self._ow_walk = walk
        self.walk_goal = None
        self.mode = "OWWALK"

    def _ow_walk_tick(self):
        """One frame of the walk over (or back): you step along your way, the foe along its own; then the battle."""
        w = getattr(self, "_ow_walk", None)
        if not w:
            self.mode = "MAP"
            return
        w["t"] += 1
        if self.anim == 0 and w["me"]:
            nxt = w["me"].pop(0)
            px, py = self.run.player
            self.facing = (max(-1, min(1, nxt[0] - px)), max(-1, min(1, nxt[1] - py)))
            self.partner_from, self.partner = self.partner, (px, py)
            self.anim_from, self.run.player = (px, py), nxt
            from src.states.overworld.dungeon import STEP_FRAMES
            self.anim = STEP_FRAMES
        busy = bool(w["me"]) or self.anim > 0
        for who, mo, had, goal in w["movers"]:
            mo.tick(lambda t: True)
            who.x, who.y = mo.pos
            who.facing = mo.facing
            busy = busy or not mo.idle()
        if busy and w["t"] < 25 * 12:
            return
        for who, mo, had, goal in w["movers"]:   # (there: the trainer keeps its own steps, a wild one none)
            who.x, who.y = goal
            if had is not None:
                had.pos = had.frm = goal
                had.path, had.t = [], 1.0
                had.facing = mo.facing
            who.motion = had
            if had is None and hasattr(who, "motion"):
                del who.motion
        if w.get("end_face"):   # (back on its spot: the way it looks now)
            m, d = w["end_face"]
            m.facing = d
            if getattr(m, "motion", None) is not None:
                m.motion.facing = d
        face = w.get("face")
        if face:
            m, d = face
            m.facing = d
            if getattr(m, "motion", None) is not None:
                m.motion.facing = d
            self.facing = (-d[0], -d[1])
        self.partner = self.partner_from = tuple(self.run.player)
        self._ow_walk = None
        self.mode = "MAP"
        if w["then"]:
            w["then"]()

    # ---------------------------------------------------------------- where everyone stands
    def _tile_rect(self, x, y):
        from src.states.overworld.dungeon import TILE
        ox, oy = self._origin()
        return pygame.Rect(ox + x * TILE, oy + y * TILE, TILE, TILE)

    def _throw_spot(self, mover):
        """The tile a trainer's Pokemon stands on: in front of it, toward you."""
        f = self.run.floor
        px, py = self.run.player
        near = [(mover.x + dx, mover.y + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
        near = [t for t in near if t != (px, py) and f.walkable(*t) and not f.occupied(*t)]
        return min(near, key=lambda t: abs(t[0] - px) + abs(t[1] - py)) if near else (mover.x, mover.y)

    def _partner_beside(self, at):
        """Your Pokemon steps up beside the foe's (you stand back)."""
        f = self.run.floor
        px, py = self.run.player
        ax, ay = at
        spots = [(ax + dx, ay + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
        spots = [s for s in spots if s != (px, py) and f.walkable(*s) and not f.occupied(*s)]
        if spots:
            self.partner = self.partner_from = min(spots, key=lambda s: abs(s[0] - px) + abs(s[1] - py))

    # ---------------------------------------------------------------- Mega Evolution on the map (Legends: Z-A)
    def _mega_rect(self):
        H = self.game.height
        return pygame.Rect(20, H - 74 - 110, 170, 60)

    def _map_mega_button(self):
        """The map's MEGA button (rect, label, colour, action, enabled, small text), or None (no Key Stone, or
        the Pokemon following you has no Mega Stone)."""
        lead = self.lead()
        story = self.game.story_manager
        if not lead or lead.current_hp <= 0:
            return None
        m = mega_clock.state(self.game)
        r = self._mega_rect()
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
        if not lead or mega_clock.active(self.game) or mega_clock.cooling(self.game):
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
        from src.states.overworld.dungeon import side_buttons
        return side_buttons(self.game)[3]  # (in the right band, beside the map)

    def _qp_rects(self):
        """A card a row, above the POKEMON button (the first at the top)."""
        b = self._qp_button_rect()
        n = len(self.game.story_manager.player_team)
        w, h, gap = 300, 56, 6
        x = b.x - 10 - w  # (beside the right band, its bottom by the screen's)
        y0 = min(b.y, self.game.height - 12 - n * h - (n - 1) * gap)
        return [pygame.Rect(x, y0 + k * (h + gap), w, h) for k in range(n)]

    def _qp_party_rect(self):
        """The list's top line: the full party screen."""
        rects = self._qp_rects()
        top = rects[0].y if rects else self._qp_button_rect().y
        x = rects[0].x if rects else self._qp_button_rect().x - 310
        return pygame.Rect(x, top - 44, 300, 36)

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

    def _qp_pick(self, i):
        """Tap a Pokemon in the list: it follows you."""
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
        """The POKEMON button's list. True if it used the event."""
        if self.dialogue_box.visible or self.mode != "MAP":
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
            if e.button == 1 and self._qp_party_rect().collidepoint(e.pos):
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
        """The POKEMON button's list (the button itself is one of the map's buttons)."""
        if self.dialogue_box.visible or self.mode != "MAP" or not self.qp_open:
            return
        fonts = self.game.assets.fonts
        mouse = pygame.mouse.get_pos()
        b = self._qp_button_rect()
        theme.command_button(screen, b, theme.pokemon_word("POKEMON"), fonts["caption"], theme.POKEMON, hover=True)
        from src.minigames.base import icon
        me = self.lead()
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
            pygame.draw.rect(screen, (34, 74, 48) if best else (40, 40, 48), heal, border_radius=8)
            pygame.draw.rect(screen, (90, 200, 120) if best else (180, 180, 190), heal, 2, border_radius=8)
            pimg = self._item_img(best or "POTION", 28)
            if pimg is not None:
                if not best:
                    pimg = pimg.copy()
                    pimg.set_alpha(70)
                screen.blit(pimg, pimg.get_rect(center=heal.center))
            ink = (248, 248, 248) if ok else (130, 130, 142)
            lv = fonts["small"].render(f"Lv{p.level}" if ok else "fainted", True, (176, 182, 200))
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


class OverworldView:
    """How a battle looks in the OVERWORLD style: the map behind it, the two Pokemon on their tiles. The
    battle itself (its turns, math questions, buttons, text) is the classic one. A wild Pokemon fights from
    where it stands; a trainer sends its Pokemon out in front of it."""
    SHOT = int(FPS * 0.4)

    def __init__(self, play, mover):
        self.play = play
        self.spot, self.mine = self._line_up_wild(play, mover) if mover.kind == "wild" else self._line_up(play, mover)
        play.partner = play.partner_from = self.mine
        from src.states.overworld.dungeon import TILE
        a, b = (mover.x, mover.y), play.run.player
        self.focus = ((a[0] + b[0] + 1) * TILE / 2, (a[1] + b[1] + 1) * TILE / 2)
        self.fx = []      # floating numbers: [side, text, colour, frames left]
        self.shots = []   # attacks flying: [from side, colour, frames gone]
        self.last = {}    # each side's HP last frame (a drop: a hit landed)
        self.anim_seen = None
        self.atk = None   # the move playing: src/vfx/map_attacks.py (a lunge, a beam, a ring)

    # ---------------------------------------------------------------- where the battle stands (Jordan 11-24)
    # Side by side first: a battle up and down the screen is hard to see. If the two can't stand side by side where they
    # met, the battle moves to open ground nearby (everyone is put back after it: dungeon._back_from_battle, _ow_home).
    # Only when there's no room anywhere near is it up and down, and then with two tiles between the Pokemon.
    NEAR = 8   # (how far, in steps from you, the battle may move to find room)

    @staticmethod
    def _plan(play, mover, trainer):
        """(anchor, (dx, dy), line) - where the foe stands, the way along the line, and the line's tiles (the trainer's
        Pokemon first, then the gap, yours, you) - or None. Side by side (where you met, then nearby), else up and down."""
        f = play.run.floor
        px, py = play.run.player
        from src.coop import world
        busy = {(m.x, m.y) for m in f.movers if m is not mover} | world.people_tiles(play.game)

        fixed = getattr(mover, "_ow_fixed", False)   # (one on your line: it stays in the water, you on the shore)
        from src.dungeon import core as _core

        def free(t):
            if fixed and t != (mover.x, mover.y) and f.tile(*t) in (_core.SURF, _core.WATER):
                return False
            return t == (px, py) or (f.walkable(*t) and t not in busy and not f.occupied(*t)) or t == (mover.x, mover.y)

        def fits(anchor, d, gap):
            n = (3 if trainer else 2) + gap
            line = [(anchor[0] + d[0] * k, anchor[1] + d[1] * k) for k in range(1, n + 1)]
            return line if all(free(t) for t in line) else None

        tx, ty = mover.x, mover.y
        side = 1 if px >= tx else -1
        horiz = [(side, 0), (-side, 0)]
        vert = [(0, 1 if py >= ty else -1), (0, -1 if py >= ty else 1)]
        seen, todo, spots = {(px, py): 0}, [(px, py)], []
        while todo and not fixed:   # (side by side, on open ground near you: the nearest)
            cur = todo.pop(0)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                t = (cur[0] + dx, cur[1] + dy)
                if t not in seen and seen[cur] < OverworldView.NEAR and free(t):
                    seen[t] = seen[cur] + 1
                    todo.append(t)
                    spots.append(t)
        spots.sort(key=lambda t: (seen[t], abs(t[1] - ty)))
        for gap in (2, 1, 0):   # (side by side with two tiles between, where you met, else nearby; then closer)
            for anchor in [(tx, ty)] + spots:
                for d in horiz:
                    line = fits(anchor, d, gap)
                    if line:
                        return anchor, d, line
        for gap in (2, 1, 0):   # (no room side by side: up and down, with more room between)
            for d in vert:
                line = fits((tx, ty), d, gap)
                if line:
                    return (tx, ty), d, line
        return None

    @staticmethod
    def _stand(play, mover, anchor, d, line):
        """Put the foe on anchor and you at the line's end, facing each other; moving them away from where they met is
        remembered to put back after the battle."""
        if anchor != (mover.x, mover.y) or line[-1] != tuple(play.run.player):
            if not getattr(play, "_ow_home", None):
                play._ow_home = {"player": tuple(play.run.player), "facing": tuple(getattr(play, "facing", (0, 1))),
                                 "mover": mover, "at": (mover.x, mover.y), "mover_facing": tuple(mover.facing or (0, 1))}
        mover.x, mover.y = anchor
        mo = getattr(mover, "motion", None)
        if mo is not None:   # (a trainer's own steps: stood there too)
            mo.pos = mo.frm = anchor
            mo.path, mo.t = [], 1.0
        play.anim, play.anim_from = 0, line[-1]
        play.run.player = line[-1]
        mover.facing, play.facing = d, (-d[0], -d[1])

    @staticmethod
    def _line_up(play, mover):
        """The trainer, its Pokemon, (a gap,) yours, then you, in a line; else its Pokemon in front of it and yours
        beside that."""
        plan = OverworldView._plan(play, mover, trainer=True)
        if plan:
            anchor, d, line = plan
            OverworldView._stand(play, mover, anchor, d, line)
            return line[0], line[-2]
        spot = play._throw_spot(mover)
        play._partner_beside(spot)
        return spot, play.partner

    @staticmethod
    def _line_up_wild(play, mover):
        """The wild Pokemon, (a gap,) yours, then you, in a line; else yours beside it."""
        play._ow_foe = mover  # (the battle draws it now, with its HP)
        plan = OverworldView._plan(play, mover, trainer=False)
        if plan:
            anchor, d, line = plan
            OverworldView._stand(play, mover, anchor, d, line)
            return anchor, line[-2]
        play._partner_beside((mover.x, mover.y))
        return (mover.x, mover.y), play.partner

    def catch_points(self):
        """Where a thrown ball starts and lands, on the screen: (your Pokemon's tile, the foe's tile)."""
        play = self.play
        play._focus, play._backdrop = self.focus, True
        try:
            return play._tile_rect(*self.mine), play._tile_rect(*self.spot)
        finally:
            play._backdrop = False

    def _face(self, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        if abs(dx) >= abs(dy) and dx:
            return (1 if dx > 0 else -1, 0)
        return (0, 1 if dy >= 0 else -1)

    def _hp_bar(self, screen, name, hp, top, level, rect, mine):
        fonts = self.play.game.assets.fonts
        w = 84
        bar = pygame.Rect(0, 0, w, 10)
        bar.midbottom = (rect.centerx, rect.top - 30)
        if mine:  # (yours under your Pokemon, the foe's over it: they never overlap)
            bar.midtop = (rect.centerx, rect.bottom + 14)
        pygame.draw.rect(screen, (20, 20, 30), bar.inflate(4, 4), border_radius=4)
        k = max(0, hp) / max(1, top)
        col = (90, 220, 110) if k > 0.5 else (240, 200, 60) if k > 0.2 else (230, 70, 60)
        pygame.draw.rect(screen, col, (bar.x, bar.y, int(w * k), bar.h), border_radius=3)
        tag = fonts["caption"].render(f"{name} Lv{level}", True, (255, 255, 255))
        box = tag.get_rect(midtop=(bar.centerx, bar.bottom + 2)) if mine else tag.get_rect(midbottom=(bar.centerx, bar.y - 2))
        shade = pygame.Surface(box.inflate(10, 4).size, pygame.SRCALPHA)
        shade.fill((10, 14, 24, 150))
        screen.blit(shade, box.inflate(10, 4))
        screen.blit(tag, box)
        if mine:
            pygame.draw.rect(screen, (120, 200, 255), bar.inflate(4, 4), 2, border_radius=4)

    def _watch(self, battle):
        """A hit landed (a side's HP went down): its number floats up, and an orb flies to it."""
        for side, poke, hp in (("foe", battle.opponent_pokemon, battle.opponent_hp),
                               ("me", battle.player_pokemon, battle.player_hp)):
            key = (side, id(poke))
            was = self.last.get(key)
            self.last[key] = hp
            if was is not None and hp < was - 0.5:
                self.fx.append([side, f"-{int(round(was - hp))}", (255, 255, 255) if side == "foe" else (255, 140, 130),
                                int(FPS * 0.9)])
        anim = getattr(battle, "move_anim", None)
        lunge = getattr(getattr(battle, "anim_ctrl", None), "lunge_side", None) \
            if getattr(getattr(battle, "anim_ctrl", None), "is_lunging", False) else None
        now = (id(anim), getattr(anim, "user_side", None)) if anim is not None else (lunge and ("lunge", lunge))
        if now and now != self.anim_seen:
            side = now[1] if anim is not None else lunge
            user = battle.player_pokemon if side == "player" else battle.opponent_pokemon
            kind = str((getattr(user, "types", None) or ["NORMAL"])[0]).upper()
            self.shots.append(["me" if side == "player" else "foe", TYPE_COLOR.get(kind, (255, 255, 255)), 0])
        self.anim_seen = now

    # ---------------------------------------------------------------- a move, played on the map (src/vfx/map_attacks.py)
    def attack(self, battle, mv):
        """Start the move mv ({"name", "side", "user", "target"}) as the map's own attack."""
        from src.vfx import map_attacks
        info = map_attacks.move_for(self.play.game, mv.get("name"))
        user, target = mv.get("user"), mv.get("target")
        if getattr(battle, "is_doubles", False):
            def rect(mon):
                return lambda: (self._double_rects(battle).get(id(mon)) or (None,))[0] or self.catch_points()[0]
        else:
            def rect(mon):
                mine = mv.get("side") == "player" if mon is user else mv.get("side") != "player"
                return lambda: self.catch_points()[0 if mine else 1]
        self_target = str(info.get("target") or "").startswith("user") or user is target
        self.atk = map_attacks.MapAttack(self.play.game, info, rect(user), rect(target), self_target=self_target)
        self.atk_ids = (id(user), id(target))
        self.shots = []

    def attacking(self):
        """A move still playing (and moving on a frame: the battle waits on this)."""
        if self.atk is None:
            return False
        self.atk.update()
        if self.atk.done:
            self.atk = None
            return False
        return True

    def _role(self, mon):
        """"user" / "target" in the move playing, or None."""
        if self.atk is None or mon is None:
            return None
        u, t = self.atk_ids
        return "user" if id(mon) == u else "target" if id(mon) == t else None

    def _moved(self, rect, mon, img):
        """Where a battler is drawn now (its lunge or recoil), and its picture (white as it's hit)."""
        role = self._role(mon)
        if role is None:
            return rect, img
        dx, dy = self.atk.offset(role)
        s = self.atk.shake()
        if s:
            import random
            dx, dy = dx + random.randint(-s, s), dy + random.randint(-s, s)
        if role == "target" and self.atk.flashing() and img is not None:
            from src.vfx.map_attacks import white
            img = white(img)
        return rect.move(dx, dy), img

    def _draw_map(self, screen):
        self.play._focus = self.focus
        self.play.draw_backdrop(screen)

    def draw(self, screen, battle):
        from src.states.overworld.dungeon import TILE
        if getattr(battle, "is_doubles", False):
            return self._draw_doubles(screen, battle)
        play = self.play
        self._draw_map(screen)
        self._watch(battle)
        fonts = play.game.assets.fonts
        fr, mr = self.catch_points()[::-1]  # (on the same camera as the map behind them)
        foe, me = battle.opponent_pokemon, battle.player_pokemon
        summoning_foe = battle.phase == "ENEMY_SUMMON"
        fainting = battle.fainting_side if battle.phase in ("FAINT_ANIM_RUNNING", "RETRACT_ANIM") else None
        kept = getattr(battle, "_ow_ko", False)  # (a knocked-out wild Pokemon stays while you decide to catch it)
        if foe is not None and not summoning_foe and not getattr(battle, "_ow_hide", False) \
                and (kept or not (fainting == "opponent" or foe.current_hp <= 0 and battle.opponent_hp <= 0)):
            img = play._icon(foe, TILE + 8, facing=self._face(self.spot, self.mine))
            if img is not None:
                at, img = self._moved(fr, foe, img)
                screen.blit(img, img.get_rect(midbottom=(at.centerx, at.bottom + 4)))
            self._hp_bar(screen, foe.display_name.upper(), battle.opponent_hp, battle.opp_max_hp, foe.level, fr, False)
        if me is not None and battle.phase != "PLAYER_SUMMON" and not (fainting == "player" or me.current_hp <= 0 and battle.player_hp <= 0):
            img = play._icon(me, TILE + 8, flip=self.spot[0] > self.mine[0], facing=self._face(self.mine, self.spot))
            if img is not None:
                at, img = self._moved(mr, me, img)
                screen.blit(img, img.get_rect(midbottom=(at.centerx, at.bottom + 4)))
            self._hp_bar(screen, me.display_name.upper(), battle.player_hp, battle.player_max_hp, me.level, mr, True)
        if self.atk is not None:   # (the move: its beam, its type's sprites)
            self.atk.draw(screen)
        for s in self.shots:  # an attack: an orb of the attacker's type's colour, flying across
            a, b = (mr.center, fr.center) if s[0] == "me" else (fr.center, mr.center)
            k = min(1.0, s[2] / self.SHOT)
            for j in range(4):
                kk = max(0.0, k - j * 0.06)
                pygame.draw.circle(screen, s[1], (int(a[0] + (b[0] - a[0]) * kk), int(a[1] + (b[1] - a[1]) * kk)), 10 - j * 2)
            if k > 0.75:
                pygame.draw.circle(screen, s[1], b, int(10 + (k - 0.75) * 120), 3)
            s[2] += 1
        self.shots = [s for s in self.shots if s[2] <= self.SHOT]
        for f in self.fx:
            r = fr if f[0] == "foe" else mr
            lift = int((FPS * 0.9 - f[3]) * 2)
            theme.shadow_text(screen, f[1], fonts["label"], r.right + 34, r.top - lift // 2, color=f[2],
                              shadow=(20, 20, 30), align="center")  # (beside it, clear of its name)
            f[3] -= 1
        self.fx = [f for f in self.fx if f[3] > 0]

    # ---------------------------------------------------------------- a double battle on the map (battle_double.py)
    def _double_rects(self, battle):
        """{id(mon): (tile rect, mine?, mon)} for everyone out: each side's second Pokemon two tiles across the line
        between the two sides (two tiles, so the HP bars over and under them never meet)."""
        from src.states.overworld.dungeon import TILE
        fr, mr = self.catch_points()[::-1]
        fx, fy = self._face(self.mine, self.spot)
        px, py = abs(fy), abs(fx)   # (across the line)
        out = {}
        for mine, base, slots in ((False, fr, battle.o_slots), (True, mr, battle.p_slots)):
            for k, mon in enumerate(slots):
                if mon is not None:
                    out[id(mon)] = (base.move(px * 2 * TILE * k, py * 2 * TILE * k), mine, mon)
        return out

    def _draw_doubles(self, screen, battle):
        from src.states.overworld.dungeon import TILE
        play = self.play
        self._draw_map(screen)
        fonts = play.game.assets.fonts
        spots = self._double_rects(battle)
        for key, (r, mine, mon) in spots.items():   # (a hit: its number floats up beside it)
            hp = mon.current_hp
            was = self.last.get(key)
            self.last[key] = hp
            if was is not None and hp < was - 0.5:
                self.fx.append([key, f"-{int(round(was - hp))}", (255, 140, 130) if mine else (255, 255, 255),
                                int(FPS * 0.9)])
        actor, hit = getattr(battle, "_d_actor", None), list(getattr(battle, "_d_hit", None) or [])
        anim = getattr(battle, "move_anim", None)
        lunging = getattr(getattr(battle, "anim_ctrl", None), "is_lunging", False)
        now = (id(actor), id(anim)) if actor is not None and (anim is not None or lunging) else None
        if now and now != self.anim_seen and hit and id(actor) in spots and id(hit[0]) in spots:
            kind = str((getattr(actor, "types", None) or ["NORMAL"])[0]).upper()
            self.shots.append([id(actor), TYPE_COLOR.get(kind, (255, 255, 255)), 0, id(hit[0])])
        self.anim_seen = now
        foe_face, my_face = self._face(self.spot, self.mine), self._face(self.mine, self.spot)
        for key, (r, mine, mon) in spots.items():
            if not battle._shown(mon):
                continue
            img = play._icon(mon, TILE + 8, flip=mine and self.spot[0] > self.mine[0], facing=my_face if mine else foe_face)
            if img is not None:
                at, img = self._moved(r, mon, img)
                screen.blit(img, img.get_rect(midbottom=(at.centerx, at.bottom + 4)))
            if mon.current_hp > 0:   # (a small bar on the map; the names and HP in the battle's own boxes, below)
                bar = pygame.Rect(0, 0, TILE - 4, 8)
                bar.midbottom = (r.centerx, r.top - 12)
                if mine:
                    bar.midtop = (r.centerx, r.bottom + 10)
                k = max(0, mon.current_hp) / max(1, mon.get_max_hp())
                col = (90, 220, 110) if k > 0.5 else (240, 200, 60) if k > 0.2 else (230, 70, 60)
                pygame.draw.rect(screen, (20, 20, 30), bar.inflate(4, 4), border_radius=4)
                pygame.draw.rect(screen, col, (bar.x, bar.y, int(bar.w * k), bar.h), border_radius=3)
                if mine:
                    pygame.draw.rect(screen, (120, 200, 255), bar.inflate(4, 4), 2, border_radius=4)
        if self.atk is not None:   # (the move: its beam, its type's sprites)
            self.atk.draw(screen)
        for s in self.shots:
            if s[0] not in spots or s[3] not in spots:
                s[2] = self.SHOT + 1
                continue
            a, b = spots[s[0]][0].center, spots[s[3]][0].center
            k = min(1.0, s[2] / self.SHOT)
            for j in range(4):
                kk = max(0.0, k - j * 0.06)
                pygame.draw.circle(screen, s[1], (int(a[0] + (b[0] - a[0]) * kk), int(a[1] + (b[1] - a[1]) * kk)), 10 - j * 2)
            if k > 0.75:
                pygame.draw.circle(screen, s[1], b, int(10 + (k - 0.75) * 120), 3)
            s[2] += 1
        self.shots = [s for s in self.shots if s[2] <= self.SHOT]
        for f in self.fx:
            if f[0] not in spots:
                f[3] = 0
                continue
            r = spots[f[0]][0]
            lift = int((FPS * 0.9 - f[3]) * 2)
            theme.shadow_text(screen, f[1], fonts["label"], r.right + 34, r.top - lift // 2, color=f[2],
                              shadow=(20, 20, 30), align="center")
            f[3] -= 1
        self.fx = [f for f in self.fx if f[3] > 0]
        battle.draw_side(screen, "opponent", sprites=False)   # (the same four boxes as the CLASSIC style: never overlapping)
        battle.draw_side(screen, "player", sprites=False)
