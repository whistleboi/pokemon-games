"""Horde battles (Jordan 11-23, Hoenn H3 DECISIONS #16: ORAS's hordes as real battles, built on main): five wild Pokemon
at once against your one Pokemon. The double battle engine plays it (battle_double.py, through battle_wild_double.py's
wild rules); what a horde changes:

- Five foe slots (your side keeps one Pokemon out; your second slot stays empty), each foe picking its own move.
- A move that hits all foes (Surf, Earthquake, Rock Slide...: SPREAD in battle_double.py) hits all five, at the
  doubles' 0.75x; a single-target move asks which of them.
- A Poke Ball only when one is left standing (as in ORAS); a knocked-out one can't be caught.
- Experience for each one knocked out, as in any battle (each faint pays out as it happens).
- "A horde of wild X appeared!" when all five are one species.
The area data that starts one: src/world/hordes.py.
"""
import pygame

from src.states.battle_wild_double import WildDoubleBattleState

# Where each of the five stands (feet), as shares of the screen: a loose arc, the middle one nearest you.
HORDE_FEET = ((0.52, 0.42), (0.64, 0.37), (0.76, 0.34), (0.88, 0.37), (0.70, 0.47))
HORDE_K = 0.62          # (five a side: smaller still than a double's)
HORDE_BOX = (300, 84)   # (two columns of HP boxes, top left)
HORDE_COLS = 2


class HordeBattleState(WildDoubleBattleState):
    is_horde = True

    def __init__(self, game, horde, area_name, background_image=None):
        horde = [p for p in horde if p is not None]
        super().__init__(game, horde, area_name, partner=None, background_image=background_image)
        foes = [p for p in self.opponent_team if p is not None]
        self.o_slots = foes[:5]
        able = [p for p in game.story_manager.player_team if p is not None and p.current_hp > 0]
        self.p_slots = [able[0] if able else self.player_pokemon, None]   # (you against all five)
        self.current_opponent_idx = 0
        self._focus(self.p_slots[0], self._first_foe())
        names = {p.display_name.upper() for p in foes}
        what = (f"A horde of wild {next(iter(names))} appeared!" if len(names) == 1
                else "A horde of wild Pokemon appeared!")
        self._opening = [what]
        if self.phase == "MENU":
            self._slot_turn = self._next_input_slot(-1) or 0
            self._focus(self.p_slots[self._slot_turn], self._first_foe())

    # ---- catching: one left standing only
    def throw_from_bag(self):
        if len(self.battlers("opponent")) != 1:
            self.show_message(["It's no good! You can't aim a ball when there's more than one wild Pokemon!"],
                              callback=self.return_to_menu)
            return
        return super().throw_from_bag()

    # ---- where they stand and their boxes
    def _sprite(self, mon, side):
        if side != "opponent":
            return super()._sprite(mon, side)
        from src.vfx.animations import battle_sprite
        img = battle_sprite(mon, side)
        if img is None:
            return None
        key = ("horde", id(mon), id(img))
        if key not in self._sprite_cache:
            self._sprite_cache[key] = pygame.transform.smoothscale(
                img, (max(1, int(img.get_width() * HORDE_K)), max(1, int(img.get_height() * HORDE_K))))
        return self._sprite_cache[key]

    def _feet(self, side, k):
        if side == "opponent":
            w, h = self.game.width, self.game.height
            fx, fy = HORDE_FEET[min(k, len(HORDE_FEET) - 1)]
            return w * fx, h * fy
        return super()._feet(side, k)

    def _box_rect(self, side, k, dx=0):
        if side != "opponent":
            return super()._box_rect(side, k, dx)
        bw, bh = HORDE_BOX
        col, row = k % HORDE_COLS, k // HORDE_COLS
        return pygame.Rect(self.renderer.MARGIN + col * (bw + 8) + int(dx), 16 + row * (bh + 8), bw, bh)

    def draw_side(self, screen, side, dx=0, sprites=True):
        """The far ones first, so the nearer ones stand in front of them."""
        if side != "opponent":
            return super().draw_side(screen, side, dx, sprites)
        order = sorted(range(len(self.o_slots)), key=lambda k: HORDE_FEET[min(k, len(HORDE_FEET) - 1)][1])
        for k in order:
            mon = self.o_slots[k]
            if sprites and self._shown(mon):
                self._draw_mon(screen, mon)
        for k, mon in enumerate(self.o_slots):
            if mon is not None and (mon.current_hp > 0 or self._has(self._d_faint_queue, mon)):
                self._draw_box(screen, mon, side, k, dx)
