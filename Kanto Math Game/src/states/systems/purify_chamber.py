"""The Purify Chamber's screen at the HQ Lab (Orre batch 8b; the rules are src/world/purify_chamber.py).

The nine sets in a grid; open one to see it: its Shadow Pokemon in the middle, the ring circling round it (faster the
better its flow, glowing gold at Max Tempo). Put a Shadow Pokemon in the middle or others in the ring from your party, take
one back out, or purify a Shadow Pokemon whose heart has opened."""
import math

import pygame

from src.states.base import GameState
from src.ui import theme
from src.ui.panels import CommandButton
from src.world import purify_chamber as pc

ACCENT = (96, 70, 150)
GOLD = (236, 196, 80)


class PurifyChamberState(GameState):
    def __init__(self, game, back, show):
        super().__init__(game)
        self.back, self.show = back, show
        self.view = None      # None: the grid; else the set's index
        self.note = ""
        self.angle = 0.0
        self._icons = {}
        self.buttons = []

    # ------------------------------------------------------------------ buttons
    def _button(self, rect, label, fn, colour=None):
        b = CommandButton(rect, label, self.game.assets.fonts["button"], fn, bg_color=colour or theme.TAB_OFF, autosize=False)
        self.buttons.append(b)
        self.game.ui_manager.add_element(b)

    def _build(self):
        ui = self.game.ui_manager
        for b in self.buttons:
            if b in ui.elements:
                ui.elements.remove(b)
        self.buttons = []
        w, h = self.game.width, self.game.height
        self._button((16, 14, 140, 56), "BACK", self._back, theme.BACK)
        story = self.game.story_manager
        if self.view is None:
            top = theme.HEADER_H + 24
            cw, ch = (w - 80) // 3, max(80, (h - top - 120) // 3)
            for i, s in enumerate(pc.sets(story)):
                r = (40 + (i % 3) * cw, top + (i // 3) * (ch + 8), cw - 16, ch)
                name = self._name(s.get("shadow")) if s.get("shadow") else "EMPTY"
                tag = " MAX" if pc.tempo_max(self.game, s) else f" {len(s.get('ring') or [])}/4"
                self._button(r, f"{i + 1}: {name}{tag}", (lambda i=i: self._open(i)),
                             (150, 120, 40) if pc.tempo_max(self.game, s) else None)
            return
        s = pc.sets(story)[self.view]
        y = h - 90
        bw = (w - 80) // 4
        self._button((40, y, bw - 12, 70), "SHADOW IN", self._shadow_in)
        self._button((40 + bw, y, bw - 12, 70), "RING IN", self._ring_in)
        self._button((40 + 2 * bw, y, bw - 12, 70), "TAKE OUT", self._take_out)
        if pc.is_open(s.get("shadow")):
            self._button((40 + 3 * bw, y, bw - 12, 70), "PURIFY", self._purify, (150, 120, 40))

    # ------------------------------------------------------------------ actions
    def _back(self):
        if self.view is not None:
            self.view, self.note = None, ""
            self._build()
            return
        if hasattr(self.back, "is_resuming"):
            self.back.is_resuming = True
        self.game.change_state(self.back)
        self.show(["You stepped back from the Purify Chamber."])

    def _open(self, i):
        self.view, self.note = i, ""
        self._build()

    def _pick(self, then, want=None):
        """Pick a Pokemon from your party or the PC (Jordan 11-21: PC too). then(src, mon): src ("party", i) or ("pc", slot)."""
        from src.states.systems.pick_list import PickListState
        story = self.game.story_manager
        has_pc = any(p is not None and (want is None or want(p)) for p in story.pc_pokemon)

        def where(v):
            if v == "party":
                self._pick_party(then)
            elif v == "pc":
                self._pick_pc(then, want, 0)
        if not has_pc:
            self._pick_party(then)
            return
        self.game.change_state(PickListState(self.game, self, "FROM WHERE?", [("YOUR PARTY", "party"), ("THE PC", "pc")], where))

    def _pick_party(self, then):
        from src.states.systems import PokemonPartyMenuState

        def chose(i):
            self.game.change_state(self)
            team = self.game.story_manager.player_team
            if 0 <= i < len(team) and team[i]:
                then(("party", i), team[i])

        self.game.change_state(PokemonPartyMenuState(self.game, previous_state=self, context="use_item", on_select=chose,
                                                     on_cancel=lambda: self.game.change_state(self)))

    PC_PAGE = 10

    def _pick_pc(self, then, want, page):
        """The PC's Pokemon that fit, ten to a page (MORE for the next)."""
        from src.states.systems.pick_list import PickListState
        story = self.game.story_manager
        can = [(i, p) for i, p in enumerate(story.pc_pokemon) if p is not None and getattr(p, "id", 0) and (want is None or want(p))]
        part = can[page * self.PC_PAGE:(page + 1) * self.PC_PAGE]
        rows = [(f"{p.display_name.upper()} Lv{p.level}", i) for i, p in part]
        if (page + 1) * self.PC_PAGE < len(can):
            rows.append(("MORE...", "__more"))

        def chose(v):
            if v == "__more":
                self._pick_pc(then, want, page + 1)
            elif v is not None:
                then(("pc", v), story.pc_pokemon[v])
        self.game.change_state(PickListState(self.game, self, f"FROM THE PC ({page + 1})", rows, chose))

    def _leave(self, src):
        """The picked Pokemon leaves where it was (it's in the chamber now)."""
        story = self.game.story_manager
        kind, i = src if isinstance(src, tuple) else ("party", src)
        if kind == "pc":
            story.pc_pokemon[i] = None
            return True
        return self._leave_party(i)

    def _leave_party(self, i):
        team = self.game.story_manager.player_team
        if len([p for p in team if p]) <= 1:
            self.note = "You can't leave yourself without a Pokemon!"
            return False
        team.pop(i)
        return True

    def _shadow_in(self):
        story = self.game.story_manager

        def go(src, mon):
            if not story.is_shadow(mon):
                self.note = "Only a Shadow Pokemon goes in the middle."
            else:
                said = pc.put_shadow(self.game, self.view, mon)
                if said:
                    self.note = " ".join(said)
                elif self._leave(src):
                    self.note = f"{self._name(story._pokemon_record(mon))} went into the chamber."
                    if pc.is_open(pc.sets(story)[self.view]["shadow"]):
                        self.note = "The nine sets' flow poured into XD001 - its heart opened at once!"
                else:
                    pc.sets(story)[self.view]["shadow"] = None
            self._build()
        self._pick(go, want=story.is_shadow)

    def _ring_in(self):
        story = self.game.story_manager

        def go(src, mon):
            if story.is_shadow(mon):
                self.note = "Shadow Pokemon go in the middle, not the ring."
            elif getattr(mon, "is_egg", False) or getattr(mon, "unhatched", False):
                self.note = "An Egg can't go in the chamber."
            else:
                said = pc.put_ring(self.game, self.view, mon)
                if said:
                    self.note = " ".join(said)
                elif self._leave(src):
                    self.note = f"{mon.display_name.upper()} joined the ring."
                else:
                    pc.sets(story)[self.view]["ring"].pop()
            self._build()
        self._pick(go, want=lambda p: not story.is_shadow(p) and not getattr(p, "is_egg", False))

    def _home(self, mon):
        """Back to the party, or to the PC when the party's full. Returns where it went."""
        story = self.game.story_manager
        if len([p for p in story.player_team if p]) < 6:
            story.player_team.append(mon)
            return "your party"
        story.deposit_to_pc(mon)
        return "the PC"

    def _take_out(self):
        story = self.game.story_manager
        s = pc.sets(story)[self.view]
        which = len(s["ring"]) - 1 if s.get("ring") else ("shadow" if s.get("shadow") else None)
        if which is None:
            self.note = "This set is empty."
        else:
            mon = pc.take(self.game, self.view, which)
            self.note = f"{mon.display_name.upper()} went back to {self._home(mon)}."
        self._build()

    def _purify(self):
        new = pc.purify(self.game, self.view)
        if new is not None:
            to = self._home(new)
            self.note = f"{new.display_name.upper()}'s heart opened! It's no longer a Shadow Pokemon." + (" (Sent to the PC.)" if to == "the PC" else "")
            if int(new.id) == 249:
                self.note += " It can learn Feather Dance and Psycho Boost now."
        self._build()

    # ------------------------------------------------------------------ drawing
    def _name(self, rec):
        if not rec:
            return "-"
        if rec.get("nickname"):
            return str(rec["nickname"]).upper()
        raw = self.game.loader.fetch_specific(int(rec["id"])) or {}
        n = str(raw.get("name", "?")).upper()
        return n[7:] if n.startswith("SHADOW ") else n

    def _icon(self, rec, size):
        key = (id(rec), size)
        if key not in self._icons:
            img = None
            try:
                img = self.game.story_manager._load_pokemon(rec, self.game.loader).image
            except Exception:
                img = None
            self._icons[key] = pygame.transform.smoothscale(img, (size, size)) if img is not None else None
        return self._icons[key]

    def start(self):
        self._build()

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self._back()

    def update(self):
        if self.view is not None:
            s = pc.sets(self.game.story_manager)[self.view]
            self.angle += 0.6 + 0.5 * max(0, pc.flow(self.game, s))

    def draw(self):
        screen = self.game.screen
        f = self.game.assets.fonts
        title = "PURIFY CHAMBER" if self.view is None else f"PURIFY CHAMBER - SET {self.view + 1}"
        theme.menu_background(screen, ACCENT, title, f["button"], title_x=176)
        w, h = screen.get_size()
        small = f.get("small") or f["button"]
        if self.view is None:
            best = pc.best_circle(self.game)
            msg = "All nine sets at Max Tempo! XD001 could go in now." if best else "Four in a ring, each strong against the next, gives Max Tempo."
            screen.blit(small.render(msg, True, GOLD if best else (230, 230, 240)), (40, h - 44))
            return
        s = pc.sets(self.game.story_manager)[self.view]
        cx, cy, rad = w // 2, theme.HEADER_H + (h - theme.HEADER_H - 110) // 2, min(w, h) // 5
        maxed = pc.tempo_max(self.game, s)
        pygame.draw.circle(screen, GOLD if maxed else (120, 100, 180), (cx, cy), rad, 3)
        glow = int(40 + 30 * math.sin(self.angle / 20))
        pygame.draw.circle(screen, (glow, glow // 2, glow + 40), (cx, cy), rad // 2)
        if s.get("shadow"):
            ic = self._icon(s["shadow"], rad)
            if ic is not None:
                screen.blit(ic, ic.get_rect(center=(cx, cy)))
            sh = s["shadow"].get("shadow") or {}
            mx = max(1, int(sh.get("max", 1)))
            share = max(0, int(sh.get("gauge", 0))) / mx
            bar = pygame.Rect(cx - rad // 2, cy + rad // 2 + 6, rad, 10)
            pygame.draw.rect(screen, (40, 30, 60), bar)
            pygame.draw.rect(screen, (150, 70, 200), (bar.x, bar.y, int(bar.w * share), bar.h))
        ring = s.get("ring") or []
        for k, rec in enumerate(ring):
            a = math.radians(self.angle + k * 90)
            px, py = cx + int(rad * math.cos(a)), cy + int(rad * math.sin(a))
            pygame.draw.circle(screen, (60, 50, 90), (px, py), int(rad * 0.38))
            ic = self._icon(rec, int(rad * 0.62))
            if ic is not None:
                screen.blit(ic, ic.get_rect(center=(px, py)))
        fl = pc.flow(self.game, s)
        info = (f"Flow {fl:+d}" + ("  MAX TEMPO!" if maxed else "") +
                (f"  Heart opens {pc.opens_by(self.game, s)} every {pc.EVERY} steps" if s.get("shadow") and not pc.is_open(s["shadow"]) else "") +
                ("  Its heart is open: PURIFY!" if pc.is_open(s.get("shadow")) else ""))
        screen.blit(small.render(info, True, GOLD if maxed else (230, 230, 240)), (40, h - 130))
        names = ", ".join(self._name(r) for r in ring) or "nobody in the ring"
        screen.blit(small.render(f"Middle: {self._name(s.get('shadow'))}   Ring: {names}", True, (220, 220, 235)), (40, theme.HEADER_H + 8))
        if self.note:
            screen.blit(small.render(self.note, True, (250, 230, 170)), (40, h - 160))
